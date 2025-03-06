import subprocess
import threading
import time
import streamlit as st
import streamlit.errors
from datetime import datetime
from queue import Queue, Empty
import pty
import os
import select
import fcntl
import termios
import struct

class CommandExecutor:
    def __init__(self):
        self.process = None
        self.interactive = False
        self.output_queue = Queue()
        self.master_fd = None
        self.slave_fd = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def is_interactive(self):
        return self.is_running() and self.interactive

    def execute_command(self, command, output_placeholder, progress_placeholder, status_placeholder, cmd_entry=None):
        """Execute a shell command with real-time output and potential interactivity."""
        if self.is_running():
            status_placeholder.error("A command is already running. Please wait or stop it.")
            return

        # Create a pseudoterminal pair
        self.master_fd, self.slave_fd = pty.openpty()

        # Set non-blocking mode for master fd
        flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Start the command
        try:
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                close_fds=True,
                universal_newlines=True,
                preexec_fn=os.setsid
            )

            # Close the slave fd in this process as the child process has it
            os.close(self.slave_fd)
            self.slave_fd = None

            # Show initial status
            status_placeholder.info(f"Command started: {command}")
            progress_placeholder.progress(0)

            # Start output monitoring in a separate thread
            self.output_thread = threading.Thread(
                target=self._monitor_output,
                args=(self.master_fd, output_placeholder, progress_placeholder, status_placeholder, cmd_entry),
                daemon=True
            )
            self.output_thread.start()

            # Check if command might be interactive
            interactive_commands = ['python', 'python3', 'ipython', 'node', 'bash', 'sh', 'mysql', 'psql', 'mongo']
            self.interactive = any(cmd in command.split() for cmd in interactive_commands)

        except Exception as e:
            if self.master_fd:
                os.close(self.master_fd)
                self.master_fd = None
            if self.slave_fd:
                os.close(self.slave_fd)
                self.slave_fd = None
            status_placeholder.error(f"Error executing command: {str(e)}")
            if cmd_entry:
                cmd_entry['return_code'] = -1

    def _monitor_output(self, master_fd, output_placeholder, progress_placeholder, status_placeholder, cmd_entry=None):
        """Monitor command output and update UI in real time."""
        output_buffer = ""
        start_time = time.time()
        update_interval = 0.2  # Slightly increased interval to reduce updates

        try:
            last_update_time = 0
            while self.is_running() or select.select([master_fd], [], [], 0)[0]:
                try:
                    data = os.read(master_fd, 1024).decode('utf-8', errors='replace')
                    if not data:
                        break

                    # Add to buffer
                    output_buffer += data

                    # Only update session state at specified intervals
                    current_time = time.time()
                    if current_time - last_update_time >= update_interval:
                        last_update_time = current_time
                        
                        # Calculate progress
                        elapsed = time.time() - start_time
                        progress = min(0.99, elapsed / 60)  # Max 60 seconds for full progress
                        
                        # Thread-safe session state update
                        try:
                            # Using a dictionary to update multiple values at once
                            # to reduce the risk of race conditions
                            updates = {
                                "latest_output": output_buffer,
                                "latest_progress": progress,
                                "latest_timestamp": time.time(),
                                "output_pending": True
                            }
                            
                            # Update session state in a synchronized way
                            for key, value in updates.items():
                                st.session_state[key] = value
                                
                        except streamlit.errors.StreamlitAPIException:
                            # Handle potential Streamlit context errors
                            pass

                except (OSError, IOError) as e:
                    if e.errno != 11:  # EAGAIN: Resource temporarily unavailable
                        break
                    time.sleep(0.1)

            # Command completed, get return code
            if self.process:
                return_code = self.process.poll()
                if return_code is not None:
                    status = "Completed successfully" if return_code == 0 else f"Failed with code {return_code}"

                    try:
                        # Set final update in session state
                        st.session_state["latest_output"] = output_buffer
                        st.session_state["latest_progress"] = 1.0
                        st.session_state["latest_status"] = status
                        st.session_state["latest_success"] = return_code == 0
                        st.session_state["latest_timestamp"] = time.time()
                        st.session_state["output_pending"] = True
                        st.session_state["command_completed"] = True

                        # Update command history entry
                        if cmd_entry:
                            cmd_entry['return_code'] = return_code
                            cmd_entry['output'] = output_buffer
                    except streamlit.errors.StreamlitAPIException:
                        # Handle potential Streamlit context errors
                        pass

        finally:
            # Clean up
            if master_fd:
                os.close(master_fd)
                self.master_fd = None
            self.process = None
            self.interactive = False

    def send_input(self, input_text):
        """Send input to the running interactive process."""
        if not self.is_running() or not self.interactive or not self.master_fd:
            return False

        try:
            # Ensure input ends with newline
            if not input_text.endswith('\n'):
                input_text += '\n'

            # Write to the master fd
            os.write(self.master_fd, input_text.encode('utf-8'))
            return True
        except Exception as e:
            st.error(f"Failed to send input: {str(e)}")
            return False

    def terminate_current_process(self):
        """Terminate the currently running process."""
        if self.is_running():
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.process.pid), 15)
                # Wait a bit to see if it terminates
                time.sleep(0.5)
                # If still running, force kill
                if self.is_running():
                    os.killpg(os.getpgid(self.process.pid), 9)
            except Exception as e:
                st.error(f"Failed to terminate process: {str(e)}")
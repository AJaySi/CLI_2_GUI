import subprocess
import threading
import time
import streamlit as st
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
        self._process = None
        self._is_running = False
        self._output_queue = Queue()
        self._interactive = False
        self._master_fd = None
        self._slave_fd = None

    def is_running(self):
        return self._is_running

    def is_interactive(self):
        return self._interactive

    def _read_output(self, fd):
        """Read output from file descriptor"""
        try:
            output = os.read(fd, 1024).decode()
            if output:
                self._output_queue.put(('output', output))
            return bool(output)
        except (OSError, IOError) as e:
            if e.errno != 11:  # EAGAIN
                return False
            return True

    def send_input(self, input_text):
        """Send input to interactive process"""
        if not self._interactive or not self._master_fd:
            return

        try:
            # Ensure input ends with newline
            if not input_text.endswith('\n'):
                input_text += '\n'
            os.write(self._master_fd, input_text.encode())
            self._output_queue.put(('output', f">>> {input_text}"))
        except OSError as e:
            self._output_queue.put(('error', f"Failed to send input: {str(e)}"))

    def execute_command(self, command, output_placeholder, progress_bar, status_placeholder, cmd_entry=None):
        """Execute a command with real-time output"""
        if self._is_running:
            status_placeholder.error("A command is already running")
            return

        self._is_running = True
        start_time = time.time()

        # Check if command might be interactive
        interactive_commands = ['python', 'python3', 'ipython', 'node', 'mysql']
        self._interactive = any(cmd in command.split()[0] for cmd in interactive_commands)

        def run_command():
            try:
                if self._interactive:
                    # Create PTY
                    self._master_fd, self._slave_fd = pty.openpty()

                    # Configure PTY
                    term_size = struct.pack('HHHH', 24, 80, 0, 0)
                    fcntl.ioctl(self._slave_fd, termios.TIOCSWINSZ, term_size)

                    # Set non-blocking mode
                    flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
                    fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                    # Start process
                    self._process = subprocess.Popen(
                        command.split(),
                        stdin=self._slave_fd,
                        stdout=self._slave_fd,
                        stderr=self._slave_fd,
                        preexec_fn=os.setsid
                    )

                    # Close slave fd in parent
                    os.close(self._slave_fd)
                    self._slave_fd = None

                    # Read output loop
                    while self._is_running and self._process.poll() is None:
                        r, w, e = select.select([self._master_fd], [], [], 0.1)
                        if self._master_fd in r:
                            if not self._read_output(self._master_fd):
                                break

                        # Update progress
                        elapsed = time.time() - start_time
                        self._output_queue.put(('progress', min(0.99, elapsed / 10.0)))

                else:
                    # Non-interactive mode
                    self._process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )

                    # Read output in real-time
                    while self._is_running and self._process.poll() is None:
                        # Read stdout
                        line = self._process.stdout.readline()
                        if line:
                            self._output_queue.put(('output', line))

                        # Read stderr
                        line = self._process.stderr.readline()
                        if line:
                            self._output_queue.put(('output', f"ERROR: {line}"))

                        # Update progress
                        elapsed = time.time() - start_time
                        self._output_queue.put(('progress', min(0.99, elapsed / 10.0)))

                    # Get remaining output
                    out, err = self._process.communicate()
                    if out:
                        self._output_queue.put(('output', out))
                    if err:
                        self._output_queue.put(('output', f"ERROR: {err}"))

                # Get return code and send final status
                return_code = self._process.poll() or 0
                execution_time = time.time() - start_time

                if cmd_entry is not None:
                    cmd_entry['return_code'] = return_code

                if self._interactive:
                    status_text = "Interactive session ended"
                else:
                    status_text = (
                        f"Command completed (Return code: {return_code})\n"
                        f"Execution time: {execution_time:.2f} seconds"
                    )
                self._output_queue.put(('status', (return_code == 0, status_text)))
                self._output_queue.put(('progress', 1.0))

            except Exception as e:
                self._output_queue.put(('error', f"Error executing command: {str(e)}"))
                if cmd_entry:
                    cmd_entry['return_code'] = -1
            finally:
                self._cleanup()

        # Start command execution in a separate thread
        command_thread = threading.Thread(target=run_command)
        command_thread.daemon = True
        command_thread.start()

        # Monitor the output queue and update UI
        while self._is_running or not self._output_queue.empty():
            try:
                msg_type, data = self._output_queue.get(timeout=0.1)
                if msg_type == 'output':
                    if 'output_text' not in st.session_state:
                        st.session_state.output_text = data
                    else:
                        st.session_state.output_text += data
                elif msg_type == 'progress':
                    st.session_state.progress_value = data
                elif msg_type == 'status':
                    is_success, text = data
                    if is_success:
                        status_placeholder.success(text)
                    else:
                        status_placeholder.error(text)
                elif msg_type == 'error':
                    status_placeholder.error(data)
            except Empty:
                continue

    def _cleanup(self):
        """Clean up resources"""
        self._is_running = False

        if self._master_fd:
            try:
                os.close(self._master_fd)
            except:
                pass
            self._master_fd = None

        if self._slave_fd:
            try:
                os.close(self._slave_fd)
            except:
                pass
            self._slave_fd = None

        if self._process:
            try:
                self._process.terminate()
                time.sleep(0.1)
                if self._process.poll() is None:
                    self._process.kill()
            except:
                pass
            self._process = None

        self._interactive = False

    def terminate_current_process(self):
        """Terminate the currently running process"""
        if self._is_running:
            self._cleanup()
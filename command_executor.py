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
        self._current_process = None
        self._is_running = False
        self._output_queue = Queue()
        self._interactive_mode = False
        self._master_fd = None
        self._slave_fd = None

    def is_running(self):
        return self._is_running

    def is_interactive(self):
        return self._interactive_mode

    def send_input(self, input_text):
        """Send input to the running interactive process"""
        if self._interactive_mode and self._master_fd:
            input_bytes = (input_text + '\n').encode()
            try:
                # Add the input to the output queue for display
                self._output_queue.put(('output', f">>> {input_text}"))
                os.write(self._master_fd, input_bytes)
            except OSError as e:
                self._output_queue.put(('error', f"Failed to send input: {str(e)}"))

    def _create_pty(self):
        """Create and configure a pseudo-terminal"""
        master_fd, slave_fd = pty.openpty()
        # Set terminal size
        term_size = struct.pack('HHHH', 24, 80, 0, 0)
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, term_size)
        # Set non-blocking mode for master
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        return master_fd, slave_fd

    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry=None):
        if self._is_running:
            status_container.error("A command is already running")
            return

        self._is_running = True
        start_time = time.time()
        output_text = []

        def run_command():
            try:
                # Check if command might be interactive
                interactive_commands = ['python', 'python3', 'ipython', 'node', 'mysql']
                self._interactive_mode = any(cmd in command.split()[0] for cmd in interactive_commands)

                if self._interactive_mode:
                    try:
                        # Create and configure PTY
                        self._master_fd, self._slave_fd = self._create_pty()

                        # Start process with PTY
                        process = subprocess.Popen(
                            command.split(),
                            stdin=self._slave_fd,
                            stdout=self._slave_fd,
                            stderr=self._slave_fd,
                            preexec_fn=os.setsid
                        )
                        self._current_process = process

                        # Buffer for incomplete lines
                        buffer = ""

                        # Read from PTY
                        while process.poll() is None and self._is_running:
                            try:
                                r, _, _ = select.select([self._master_fd], [], [], 0.1)
                                if self._master_fd in r:
                                    try:
                                        data = os.read(self._master_fd, 1024).decode(errors='replace')
                                        if data:
                                            buffer += data
                                            # Process complete lines
                                            while '\n' in buffer:
                                                line, buffer = buffer.split('\n', 1)
                                                if line.strip():
                                                    output_text.append(line)
                                                    self._output_queue.put(('output', '\n'.join(output_text)))
                                    except OSError as e:
                                        if e.errno != 11:  # Ignore EAGAIN
                                            raise

                                # Update progress
                                elapsed_time = time.time() - start_time
                                self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))

                            except (OSError, IOError) as e:
                                if e.errno == 5:  # Input/output error (possibly closed PTY)
                                    break
                                self._output_queue.put(('error', f"PTY Error: {str(e)}"))
                                break

                        # Process remaining buffer
                        if buffer.strip():
                            output_text.append(buffer.strip())
                            self._output_queue.put(('output', '\n'.join(output_text)))

                    except Exception as e:
                        self._output_queue.put(('error', f"Interactive mode error: {str(e)}"))
                        return

                else:
                    # Non-interactive command handling
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    self._current_process = process

                    # Read output in real-time
                    while True:
                        # Read stdout
                        stdout_line = process.stdout.readline()
                        if stdout_line:
                            output_text.append(stdout_line.strip())
                            self._output_queue.put(('output', '\n'.join(output_text)))

                        # Read stderr
                        stderr_line = process.stderr.readline()
                        if stderr_line:
                            output_text.append(f"ERROR: {stderr_line.strip()}")
                            self._output_queue.put(('output', '\n'.join(output_text)))

                        # Check if process has finished
                        if process.poll() is not None:
                            remaining_stdout, remaining_stderr = process.communicate()
                            if remaining_stdout:
                                output_text.append(remaining_stdout.strip())
                            if remaining_stderr:
                                output_text.append(f"ERROR: {remaining_stderr.strip()}")
                            if remaining_stdout or remaining_stderr:
                                self._output_queue.put(('output', '\n'.join(output_text)))
                            break

                        # Update progress
                        elapsed_time = time.time() - start_time
                        self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))
                        time.sleep(0.1)

                # Get return code and send final status
                return_code = process.poll() or 0
                execution_time = time.time() - start_time

                if cmd_entry is not None:
                    cmd_entry['return_code'] = return_code
                    cmd_entry['output'] = '\n'.join(output_text)

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
                    st.session_state.output_text = data
                elif msg_type == 'progress':
                    st.session_state.progress_value = data
                elif msg_type == 'status':
                    is_success, text = data
                    if is_success:
                        status_container.success(text)
                    else:
                        status_container.error(text)
                elif msg_type == 'error':
                    status_container.error(data)
            except Empty:
                continue

    def _cleanup(self):
        """Clean up resources"""
        # Clean up PTY
        if self._master_fd:
            try:
                os.close(self._master_fd)
            except:
                pass
        if self._slave_fd:
            try:
                os.close(self._slave_fd)
            except:
                pass
        self._master_fd = None
        self._slave_fd = None

        # Clean up process
        if self._current_process:
            try:
                self._current_process.terminate()
                time.sleep(0.1)
                if self._current_process.poll() is None:
                    self._current_process.kill()
            except:
                pass
        self._current_process = None
        self._interactive_mode = False
        self._is_running = False

    def terminate_current_process(self):
        """Terminate the currently running process"""
        if self._current_process and self._is_running:
            self._is_running = False
            self._cleanup()
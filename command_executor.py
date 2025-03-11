import subprocess
import threading
import time
import os
import pty
import select
import fcntl
import termios
import struct
from queue import Queue, Empty
from datetime import datetime

class CommandExecutor:
    def __init__(self):
        self._process = None
        self._is_running = False
        self._output_queue = Queue()
        self._interactive = False
        self._master_fd = None
        self._slave_fd = None
        self._output_buffer = ""

    def is_running(self):
        return self._is_running

    def is_interactive(self):
        return self._interactive

    def get_output(self):
        return self._output_buffer

    def send_input(self, input_text):
        """Send input to interactive process"""
        if not self._interactive or not self._master_fd:
            return False

        try:
            if not input_text.endswith('\n'):
                input_text += '\n'
            input_display = f">>> {input_text}"
            self._output_buffer += input_display
            self._output_queue.put(('output', input_display))
            os.write(self._master_fd, input_text.encode())
            return True
        except OSError as e:
            error_msg = f"Failed to send input: {str(e)}"
            self._output_queue.put(('error', error_msg))
            return False

    def execute_command(self, command):
        """Execute a command with real-time output"""
        if self._is_running:
            return False

        self._is_running = True
        self._output_buffer = ""
        start_time = time.time()

        interactive_commands = ['python', 'python3', 'ipython', 'node', 'mysql']
        self._interactive = any(cmd in command.split()[0] for cmd in interactive_commands)

        def run_command():
            try:
                if self._interactive:
                    # Interactive mode with PTY
                    self._master_fd, self._slave_fd = pty.openpty()
                    term_size = struct.pack('HHHH', 24, 80, 0, 0)
                    fcntl.ioctl(self._slave_fd, termios.TIOCSWINSZ, term_size)
                    flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
                    fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                    self._process = subprocess.Popen(
                        command.split(),
                        stdin=self._slave_fd,
                        stdout=self._slave_fd,
                        stderr=self._slave_fd,
                        env=os.environ.copy()
                    )

                    os.close(self._slave_fd)
                    self._slave_fd = None

                    time.sleep(0.1)  # Initial delay for startup

                    while self._is_running and self._process.poll() is None:
                        r, _, _ = select.select([self._master_fd], [], [], 0.1)
                        if self._master_fd in r:
                            try:
                                data = os.read(self._master_fd, 1024).decode(errors='replace')
                                if data:
                                    self._output_buffer += data
                                    self._output_queue.put(('output', data))
                            except OSError as e:
                                if e.errno != 11:  # EAGAIN
                                    break

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
                        bufsize=1
                    )

                    # Handle stdout and stderr in real-time
                    while self._is_running and self._process.poll() is None:
                        # Check stdout
                        stdout_data = self._process.stdout.read1().decode(errors='replace')
                        if stdout_data:
                            self._output_buffer += stdout_data
                            self._output_queue.put(('output', stdout_data))

                        # Check stderr
                        stderr_data = self._process.stderr.read1().decode(errors='replace')
                        if stderr_data:
                            error_text = f"ERROR: {stderr_data}"
                            self._output_buffer += error_text
                            self._output_queue.put(('output', error_text))

                        # Update progress
                        elapsed = time.time() - start_time
                        self._output_queue.put(('progress', min(0.99, elapsed / 10.0)))
                        time.sleep(0.05)  # Small delay to prevent CPU overuse

                    # Get any remaining output
                    remaining_out, remaining_err = self._process.communicate()
                    if remaining_out:
                        self._output_buffer += remaining_out
                        self._output_queue.put(('output', remaining_out))
                    if remaining_err:
                        error_text = f"ERROR: {remaining_err}"
                        self._output_buffer += error_text
                        self._output_queue.put(('output', error_text))

                # Send final status
                return_code = self._process.poll() or 0
                execution_time = time.time() - start_time

                status_text = (
                    "Interactive session active" if self._interactive else
                    f"Command completed (Return code: {return_code})\n"
                    f"Execution time: {execution_time:.2f} seconds"
                )
                self._output_queue.put(('status', (return_code == 0, status_text)))
                self._output_queue.put(('progress', 1.0))

            except Exception as e:
                error_msg = f"Error executing command: {str(e)}"
                self._output_buffer += f"\n{error_msg}\n"
                self._output_queue.put(('error', error_msg))
            finally:
                if not self._interactive:
                    self._cleanup()

        # Start command execution in a separate thread
        command_thread = threading.Thread(target=run_command)
        command_thread.daemon = True
        command_thread.start()
        return True

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
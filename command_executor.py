import subprocess
import threading
import time
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
        self._command_output = ""

    def is_running(self):
        return self._is_running

    def is_interactive(self):
        return self._interactive

    def get_output(self):
        """Get accumulated output"""
        return self._command_output

    def _read_output(self, fd):
        """Read output from file descriptor"""
        try:
            data = os.read(fd, 1024).decode(errors='replace')
            if data:
                self._command_output += data
                self._output_queue.put(('output', data))
            return bool(data)
        except (OSError, IOError) as e:
            if e.errno != 11:  # EAGAIN
                return False
            return True

    def send_input(self, input_text):
        """Send input to interactive process"""
        if not self._interactive or not self._master_fd:
            return False

        try:
            # Ensure input ends with newline
            if not input_text.endswith('\n'):
                input_text += '\n'
            # Add input to output queue for display
            self._command_output += f">>> {input_text}"
            self._output_queue.put(('output', f">>> {input_text}"))
            # Send input to process
            os.write(self._master_fd, input_text.encode())
            return True
        except OSError as e:
            self._output_queue.put(('error', f"Failed to send input: {str(e)}"))
            return False

    def execute_command(self, command):
        """Execute a command with real-time output"""
        if self._is_running:
            return False

        self._is_running = True
        self._command_output = ""  # Reset output
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
                        env=os.environ.copy()
                    )

                    # Close slave fd in parent
                    os.close(self._slave_fd)
                    self._slave_fd = None

                    # Initial delay to let Python start
                    time.sleep(0.2)

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
                            self._command_output += line
                            self._output_queue.put(('output', line))

                        # Read stderr
                        line = self._process.stderr.readline()
                        if line:
                            err_line = f"ERROR: {line}"
                            self._command_output += err_line
                            self._output_queue.put(('output', err_line))

                        # Update progress
                        elapsed = time.time() - start_time
                        self._output_queue.put(('progress', min(0.99, elapsed / 10.0)))

                    # Get remaining output
                    out, err = self._process.communicate()
                    if out:
                        self._command_output += out
                        self._output_queue.put(('output', out))
                    if err:
                        err_output = f"ERROR: {err}"
                        self._command_output += err_output
                        self._output_queue.put(('output', err_output))

                # Get return code
                return_code = self._process.poll() or 0
                execution_time = time.time() - start_time

                # Send final status
                status_text = (
                    "Interactive session active" if self._interactive else
                    f"Command completed (Return code: {return_code})\n"
                    f"Execution time: {execution_time:.2f} seconds"
                )
                self._output_queue.put(('status', (return_code == 0, status_text)))
                self._output_queue.put(('progress', 1.0))

            except Exception as e:
                self._output_queue.put(('error', f"Error executing command: {str(e)}"))
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
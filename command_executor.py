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
        self._input_queue = Queue()
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
                # Add input to output as user input marker
                self._output_queue.put(('output', '\n'.join([line for line in self._output_queue.queue 
                                                             if isinstance(line, tuple) and line[0] == 'output' 
                                                             and len(line) > 1 and isinstance(line[1], str)
                                                             and line[1]][-1] if self._output_queue.queue else '') + f"\n>>> {input_text}"))
                # Write to the process stdin
                os.write(self._master_fd, input_bytes)
            except OSError as e:
                self._output_queue.put(('error', f"Failed to send input to process: {str(e)}"))

    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry):
        def run_command():
            self._is_running = True
            start_time = time.time()
            output_text = []

            try:
                # Check if command might be interactive
                interactive_commands = ['python', 'python3', 'ipython', 'node', 'mysql']
                self._interactive_mode = any(cmd in command.split()[0] for cmd in interactive_commands)

                if self._interactive_mode:
                    try:
                        # Create pseudo-terminal
                        self._master_fd, self._slave_fd = pty.openpty()

                        # Set terminal size
                        term_size = struct.pack('HHHH', 24, 80, 0, 0)
                        fcntl.ioctl(self._slave_fd, termios.TIOCSWINSZ, term_size)

                        # Set non-blocking mode for master fd
                        flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
                        fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                        # Start process with PTY
                        process = subprocess.Popen(
                            command.split(),
                            stdin=self._slave_fd,
                            stdout=self._slave_fd,
                            stderr=self._slave_fd,
                            close_fds=True
                        )

                        self._current_process = process
                        buffer = ""

                        while process.poll() is None:
                            try:
                                # Check for input/output
                                r, w, e = select.select([self._master_fd], [], [], 0.1)

                                if self._master_fd in r:
                                    try:
                                        data = os.read(self._master_fd, 1024).decode(errors='replace')
                                        if data:
                                            buffer += data
                                            lines = buffer.split('\n')
                                            # Keep the last partial line in buffer
                                            buffer = lines[-1]
                                            # Process complete lines
                                            for line in lines[:-1]:
                                                output_text.append(line)
                                            # Update the output even if lines are empty to show prompts
                                            self._output_queue.put(('output', '\n'.join(output_text)))
                                    except OSError as e:
                                        if e.errno != 11:  # Ignore "Resource temporarily unavailable"
                                            raise

                                # Update progress periodically
                                elapsed_time = time.time() - start_time
                                self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))

                            except (OSError, IOError) as e:
                                if e.errno == 5:  # Input/output error, possibly due to closed PTY
                                    break
                                self._output_queue.put(('error', f"PTY Error: {str(e)}"))
                                break

                        # Process any remaining buffer
                        if buffer.strip():
                            output_text.append(buffer.strip())
                            self._output_queue.put(('output', '\n'.join(output_text)))

                    except Exception as e:
                        self._output_queue.put(('error', f"Interactive mode error: {str(e)}"))
                        self._interactive_mode = False
                        
                    # Add a message to indicate interactive mode is active
                    if self._interactive_mode:
                        self._output_queue.put(('status', (True, "Interactive session active. Use the Interactive Input field below to communicate with the process.")))

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

                    def read_output(pipe, is_error=False):
                        while True:
                            line = pipe.readline()
                            if not line and process.poll() is not None:
                                break
                            if line:
                                prefix = "ERROR: " if is_error else ""
                                output_text.append(f"{prefix}{line.strip()}")
                                self._output_queue.put(('output', '\n'.join(output_text)))

                    stdout_thread = threading.Thread(target=read_output, args=(process.stdout,))
                    stderr_thread = threading.Thread(target=read_output, args=(process.stderr, True))

                    stdout_thread.start()
                    stderr_thread.start()

                    while process.poll() is None:
                        elapsed_time = time.time() - start_time
                        self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))
                        time.sleep(0.1)

                    stdout_thread.join()
                    stderr_thread.join()

                # Get return code and update status
                return_code = process.poll()
                cmd_entry['return_code'] = return_code

                # Final status update
                execution_time = time.time() - start_time
                if self._interactive_mode:
                    status_text = "Interactive session ended"
                else:
                    status_text = (
                        f"Command completed (Return code: {return_code})\n"
                        f"Execution time: {execution_time:.2f} seconds"
                    )

                self._output_queue.put(('status', (return_code == 0, status_text)))

            except Exception as e:
                error_msg = f"Error executing command: {str(e)}"
                self._output_queue.put(('error', error_msg))
                cmd_entry['return_code'] = -1

            finally:
                # Clean up PTY resources
                if self._interactive_mode:
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
                    self._interactive_mode = False

                # Clean up process
                if self._current_process:
                    try:
                        self._current_process.terminate()
                        self._current_process.wait(timeout=1)
                    except:
                        pass
                self._is_running = False
                self._current_process = None
                self._output_queue.put(('progress', 1.0))

        def update_ui():
            try:
                while self._is_running or not self._output_queue.empty():
                    try:
                        msg_type, data = self._output_queue.get(timeout=0.1)

                        if msg_type == 'output':
                            output_container.markdown(f"```python\n{data}\n```")
                        elif msg_type == 'progress':
                            progress_bar.progress(data)
                        elif msg_type == 'status':
                            is_success, text = data
                            if is_success:
                                status_container.success(text)
                            else:
                                status_container.error(text)
                        elif msg_type == 'error':
                            output_container.error(data)

                    except Empty:
                        continue
                    except Exception as e:
                        output_container.error(f"UI Update Error: {str(e)}")
                        time.sleep(0.1)

            except Exception as e:
                output_container.error(f"UI Thread Error: {str(e)}")

        # Clear previous output
        output_container.empty()
        status_container.empty()
        progress_bar.progress(0.0)

        # Start command execution in separate thread
        command_thread = threading.Thread(target=run_command)
        command_thread.start()

        # Update UI in the main thread
        update_ui()

    def terminate_current_process(self):
        if self._current_process and self._is_running:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=1)
            except:
                pass
            self._is_running = False
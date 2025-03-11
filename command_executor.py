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
                self._output_queue.put(('output', f">>> {input_text}"))
                os.write(self._master_fd, input_bytes)
            except OSError:
                self._output_queue.put(('error', "Failed to send input to process"))

    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry=None):
        """Execute a shell command with real-time output"""
        if self._is_running:
            status_container.error("A command is already running")
            return

        self._is_running = True
        start_time = time.time()
        output_text = []

        try:
            # Check if command might be interactive
            interactive_commands = ['python', 'python3', 'ipython', 'node', 'mysql']
            self._interactive_mode = any(cmd in command.split()[0] for cmd in interactive_commands)

            if self._interactive_mode:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=1,
                    universal_newlines=True,
                    env=os.environ.copy()
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=1,
                    universal_newlines=True,
                    env=os.environ.copy()
                )

            self._current_process = process

            # Define output reader function
            def read_output(pipe, is_error=False):
                for line in pipe:
                    if not self._is_running:
                        break
                    prefix = "ERROR: " if is_error else ""
                    output_text.append(f"{prefix}{line.strip()}")
                    self._output_queue.put(('output', '\n'.join(output_text)))

            # Start output reader threads
            stdout_thread = threading.Thread(target=read_output, args=(process.stdout,))
            stderr_thread = threading.Thread(target=read_output, args=(process.stderr, True))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Monitor process and update progress
            while process.poll() is None and self._is_running:
                elapsed_time = time.time() - start_time
                self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))
                time.sleep(0.1)

            # Wait for reader threads
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)

            # Get return code and update status
            return_code = process.poll() or 0
            execution_time = time.time() - start_time

            # Update command entry if provided
            if cmd_entry is not None:
                cmd_entry['return_code'] = return_code
                cmd_entry['output'] = '\n'.join(output_text)

            # Send final status update
            status_text = (
                f"Command completed (Return code: {return_code})\n"
                f"Execution time: {execution_time:.2f} seconds"
            )
            self._output_queue.put(('status', (return_code == 0, status_text)))
            self._output_queue.put(('progress', 1.0))

        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            self._output_queue.put(('error', error_msg))
            if cmd_entry:
                cmd_entry['return_code'] = -1

        finally:
            self._is_running = False
            if self._current_process:
                try:
                    self._current_process.terminate()
                except:
                    pass
            self._current_process = None
            self._interactive_mode = False

    def terminate_current_process(self):
        """Terminate the currently running process"""
        if self._current_process and self._is_running:
            self._is_running = False
            try:
                self._current_process.terminate()
                time.sleep(0.1)
                if self._current_process.poll() is None:
                    self._current_process.kill()
            except Exception as e:
                self._output_queue.put(('error', f"Failed to terminate process: {str(e)}"))
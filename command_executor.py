import subprocess
import threading
import time
import streamlit as st
from datetime import datetime
from queue import Queue, Empty

class CommandExecutor:
    def __init__(self):
        self._current_process = None
        self._is_running = False
        self._output_queue = Queue()

    def is_running(self):
        return self._is_running

    def send_input(self, input_text):
        """Send input to the running interactive process"""
        #This function is not used in the edited code and is left unchanged for completeness.  It might need to be removed or revised if interactive mode is to be reintroduced.
        pass


    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry=None):
        """Execute a shell command with real-time output"""
        if self._is_running:
            status_container.error("A command is already running")
            return

        self._is_running = True
        start_time = time.time()
        output_text = []

        def run_command():
            try:
                # Start process
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
                        # Get any remaining output
                        remaining_stdout, remaining_stderr = process.communicate()
                        if remaining_stdout:
                            output_text.append(remaining_stdout.strip())
                            self._output_queue.put(('output', '\n'.join(output_text)))
                        if remaining_stderr:
                            output_text.append(f"ERROR: {remaining_stderr.strip()}")
                            self._output_queue.put(('output', '\n'.join(output_text)))
                        break

                    # Update progress
                    elapsed_time = time.time() - start_time
                    self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))
                    time.sleep(0.1)

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
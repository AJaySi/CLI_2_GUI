import subprocess
import threading
import time
import streamlit as st
from datetime import datetime
from queue import Queue

class CommandExecutor:
    def __init__(self):
        self._current_process = None
        self._is_running = False
        self._output_queue = Queue()

    def is_running(self):
        return self._is_running

    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry):
        def run_command():
            self._is_running = True
            start_time = time.time()
            output_text = []

            try:
                # Create process with pipe for output
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
                    # Check if process has finished
                    return_code = process.poll()

                    # Read available output
                    stdout_data = process.stdout.read1().decode() if process.stdout else ''
                    stderr_data = process.stderr.read1().decode() if process.stderr else ''

                    if stdout_data:
                        output_text.append(stdout_data)
                        self._output_queue.put(('output', '\n'.join(output_text)))

                    if stderr_data:
                        output_text.append(f"ERROR: {stderr_data}")
                        self._output_queue.put(('output', '\n'.join(output_text)))

                    # Update progress
                    elapsed_time = time.time() - start_time
                    self._output_queue.put(('progress', min(1.0, elapsed_time / 10.0)))

                    if return_code is not None:
                        break

                    time.sleep(0.1)  # Small delay to prevent CPU overuse

                # Get return code and update status
                cmd_entry['return_code'] = return_code

                # Final status update
                execution_time = time.time() - start_time
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
                self._is_running = False
                self._current_process = None
                self._output_queue.put(('progress', 1.0))

        def update_ui():
            while self._is_running or not self._output_queue.empty():
                try:
                    msg_type, data = self._output_queue.get(timeout=0.1)

                    if msg_type == 'output':
                        output_container.code(data, language="bash")
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

                except Exception:
                    time.sleep(0.1)  # Wait a bit if queue is empty
                    continue

        # Start command execution in a separate thread
        command_thread = threading.Thread(target=run_command)
        ui_thread = threading.Thread(target=update_ui)

        command_thread.start()
        ui_thread.start()

    def terminate_current_process(self):
        if self._current_process and self._is_running:
            self._current_process.terminate()
            self._is_running = False
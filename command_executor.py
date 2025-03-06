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

    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry):
        def run_command():
            self._is_running = True
            start_time = time.time()
            output_text = []

            try:
                # Create process with pipe for output and specific shell
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    executable='/bin/bash'  # Explicitly specify bash
                )

                self._current_process = process

                # Non-blocking output reading
                def read_output(pipe, is_error=False):
                    while True:
                        line = pipe.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            prefix = "ERROR: " if is_error else ""
                            output_text.append(f"{prefix}{line.strip()}")
                            self._output_queue.put(('output', '\n'.join(output_text)))

                # Start output reader threads
                stdout_thread = threading.Thread(target=read_output, args=(process.stdout,))
                stderr_thread = threading.Thread(target=read_output, args=(process.stderr, True))

                stdout_thread.start()
                stderr_thread.start()

                # Monitor process and update progress
                while process.poll() is None:
                    elapsed_time = time.time() - start_time
                    self._output_queue.put(('progress', min(0.99, elapsed_time / 10.0)))
                    time.sleep(0.1)

                # Wait for output threads to complete
                stdout_thread.join()
                stderr_thread.join()

                # Get return code and update status
                return_code = process.poll()
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
                            output_container.markdown(f"```bash\n{data}\n```")
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
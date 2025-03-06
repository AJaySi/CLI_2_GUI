import subprocess
import threading
import time
import streamlit as st
from datetime import datetime

class CommandExecutor:
    def __init__(self):
        self._current_process = None
        self._is_running = False

    def is_running(self):
        return self._is_running

    def execute_command(self, command, output_container, progress_bar, status_container, cmd_entry):
        def run_command():
            self._is_running = True
            start_time = time.time()
            
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
                output_text = []
                
                # Read output in real-time
                while True:
                    stdout_line = process.stdout.readline()
                    stderr_line = process.stderr.readline()
                    
                    if stdout_line == '' and stderr_line == '' and process.poll() is not None:
                        break
                    
                    if stdout_line:
                        output_text.append(stdout_line)
                        output_container.code('\n'.join(output_text))
                    
                    if stderr_line:
                        output_text.append(f"ERROR: {stderr_line}")
                        output_container.code('\n'.join(output_text), language="bash")
                    
                    # Update progress
                    progress_bar.progress(min(1.0, (time.time() - start_time) / 10.0))
                
                # Get return code and update status
                return_code = process.wait()
                cmd_entry['return_code'] = return_code
                
                # Final status update
                execution_time = time.time() - start_time
                status_text = (
                    f"Command completed (Return code: {return_code})\n"
                    f"Execution time: {execution_time:.2f} seconds"
                )
                
                if return_code == 0:
                    status_container.success(status_text)
                else:
                    status_container.error(status_text)
                
            except Exception as e:
                output_container.error(f"Error executing command: {str(e)}")
                cmd_entry['return_code'] = -1
            
            finally:
                self._is_running = False
                self._current_process = None
                progress_bar.progress(1.0)

        # Start command execution in a separate thread
        thread = threading.Thread(target=run_command)
        thread.start()

    def terminate_current_process(self):
        if self._current_process and self._is_running:
            self._current_process.terminate()
            self._is_running = False

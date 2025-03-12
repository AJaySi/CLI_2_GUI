import streamlit as st
import subprocess
import threading
from datetime import datetime
import time

def main():
    """Simplified terminal app to verify basic functionality"""
    # Set page config
    st.set_page_config(
        page_title="Simple Web Terminal",
        page_icon="🖥️",
        layout="wide"
    )
    
    # Initialize session state
    if 'command_output' not in st.session_state:
        st.session_state.command_output = ""
    if 'running_command' not in st.session_state:
        st.session_state.running_command = False
    if 'command_process' not in st.session_state:
        st.session_state.command_process = None
    
    # Page title
    st.title("Simple Web Terminal")
    st.write("Enter a command and click 'Execute' to run it.")
    
    # Command input
    command = st.text_input("Command", placeholder="Enter command (e.g., ls -la)")
    execute_button = st.button("Execute", type="primary")
    
    # Add some basic shortcut buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("List Files (ls -la)"):
            command = "ls -la"
            execute_button = True
    with col2:
        if st.button("Current Directory (pwd)"):
            command = "pwd"
            execute_button = True
    with col3:
        if st.button("System Info (uname -a)"):
            command = "uname -a"
            execute_button = True
    with col4:
        if st.button("Date & Time (date)"):
            command = "date"
            execute_button = True
    
    # Output area
    st.write("### Command Output")
    output_area = st.empty()
    
    # Display current output
    if st.session_state.command_output:
        output_area.code(st.session_state.command_output)
    
    # Execute command
    if execute_button and command:
        # Clear previous output
        st.session_state.command_output = ""
        output_area.code("")
        
        # Mark as running
        st.session_state.running_command = True
        
        # Show command being executed
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.command_output = f"Executing: {command}\n[{timestamp}]\n\n"
        output_area.code(st.session_state.command_output)
        
        # Execute command in separate thread
        def run_command():
            try:
                # Start the process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Store process reference
                st.session_state.command_process = process
                
                # Read output in real-time
                for line in iter(process.stdout.readline, ''):
                    st.session_state.command_output += line
                
                # Wait for process to complete
                return_code = process.wait()
                
                # Add completion message
                st.session_state.command_output += f"\n\nCommand completed with return code: {return_code}"
                
                # Mark as no longer running
                st.session_state.running_command = False
                st.session_state.command_process = None
                
            except Exception as e:
                st.session_state.command_output += f"\n\nError: {str(e)}"
                st.session_state.running_command = False
                st.session_state.command_process = None
        
        # Start thread
        command_thread = threading.Thread(target=run_command)
        command_thread.daemon = True
        command_thread.start()
        
        # Rerun to show initial output
        st.rerun()
    
    # Update output if command is running
    if st.session_state.running_command:
        output_area.code(st.session_state.command_output)
        # Add a small delay to prevent too frequent refreshes
        time.sleep(0.1)
        st.rerun()

if __name__ == "__main__":
    main()
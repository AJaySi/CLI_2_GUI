import streamlit as st
import subprocess
import time
from datetime import datetime

def main():
    """Simplified terminal app to verify basic functionality"""
    # Set page config
    st.set_page_config(
        page_title="Simple Web Terminal",
        page_icon="🖥️",
        layout="wide"
    )
    
    # Title and instructions
    st.title("Simple Web Terminal")
    st.markdown("Enter commands below to execute them.")
    
    # Command input and execute button
    col1, col2 = st.columns([5, 1])
    
    with col1:
        command = st.text_input(
            "Enter command",
            placeholder="Type your command here (e.g., ls, pwd, python)",
            label_visibility="collapsed"
        )
    
    with col2:
        execute = st.button("Execute", type="primary", use_container_width=True)
    
    # Output area
    st.markdown("### Command Output")
    output_placeholder = st.empty()
    
    # Execute command if requested
    if execute and command.strip():
        try:
            with st.spinner("Executing command..."):
                # Execute the command
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                output = ""
                # Show output in real-time
                for line in process.stdout:
                    output += line
                    output_placeholder.code(output)
                
                # Wait for process to complete
                process.wait()
                
                # Display final status
                if process.returncode == 0:
                    st.success(f"Command completed successfully (exit code: {process.returncode})")
                else:
                    st.error(f"Command failed with exit code: {process.returncode}")
                
        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")
    elif execute:
        st.error("Please enter a command")

if __name__ == "__main__":
    main()
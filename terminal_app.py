import streamlit as st
import time
from datetime import datetime
from command_executor import CommandExecutor
from styles import apply_styles

def initialize_session_state():
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'command_executor' not in st.session_state:
        st.session_state.command_executor = CommandExecutor()
    if 'current_command' not in st.session_state:
        st.session_state.current_command = None

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    st.set_page_config(
        page_title="Web Terminal",
        page_icon="🖥️",
        layout="wide"
    )

    apply_styles()
    initialize_session_state()

    # Sidebar with command history
    with st.sidebar:
        st.title("Command History")
        for cmd in st.session_state.command_history:
            st.text(f"[{cmd['timestamp']}] {cmd['command']}")
            if cmd.get('return_code') is not None:
                status = "✅" if cmd['return_code'] == 0 else "❌"
                st.text(f"Status: {status} (Return code: {cmd['return_code']})")
            st.markdown("---")

    # Main terminal interface
    st.title("Web Terminal")

    # Command input
    command = st.text_input(
        "Enter command:",
        key="command_input",
        placeholder="Type your command here...",
        help="Enter a valid shell command to execute"
    )

    # Execute button and stop button side by side
    col1, col2 = st.columns([1, 4])

    with col1:
        execute = st.button("Execute", key="execute_button", type="primary")
    with col2:
        if st.session_state.command_executor.is_running():
            stop = st.button("Stop", key="stop_button", type="secondary")
            if stop:
                st.session_state.command_executor.terminate_current_process()
                st.error("Command execution stopped by user")

    if execute:
        if not command.strip():
            st.error("Please enter a command")
            return

        try:
            # Add command to history
            cmd_entry = {
                'command': command,
                'timestamp': format_timestamp(),
                'return_code': None
            }
            st.session_state.command_history.append(cmd_entry)

            # Create output containers
            output_container = st.empty()
            progress_bar = st.progress(0)
            status_container = st.empty()

            # Start command execution
            st.session_state.command_executor.execute_command(
                command,
                output_container,
                progress_bar,
                status_container,
                cmd_entry
            )
        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")

    # Display current execution status
    if st.session_state.command_executor.is_running():
        st.info("Command is currently running...")

if __name__ == "__main__":
    main()
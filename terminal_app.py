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
    if 'output_text' not in st.session_state:
        st.session_state.output_text = ''
    if 'progress_value' not in st.session_state:
        st.session_state.progress_value = 0.0
    if 'last_interactive_input' not in st.session_state:
        st.session_state.last_interactive_input = ''

def handle_interactive_input(input_text):
    """Callback to handle interactive input changes"""
    if input_text and input_text != st.session_state.last_interactive_input:
        st.session_state.last_interactive_input = input_text
        st.session_state.command_executor.send_input(input_text)

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def terminal_page():
    st.title("Web Terminal")
    st.markdown("Enter commands below to execute them. Use the sidebar to view command history.")

    # Command input
    command = st.text_input(
        "Enter command:",
        key="command_input",
        placeholder="Type your command here (e.g., ls, pwd, python)",
        help="Enter a valid shell command to execute"
    )

    # Execute and stop buttons in a row
    col1, col2 = st.columns([1, 4])
    with col1:
        execute = st.button("Execute", key="execute_button", type="primary")
    with col2:
        if st.session_state.command_executor.is_running():
            stop = st.button("Stop", key="stop_button", type="secondary")
            if stop:
                st.session_state.command_executor.terminate_current_process()
                st.error("Command execution stopped by user")

    # Interactive input section (only shown when in interactive mode)
    if st.session_state.command_executor.is_interactive():
        st.info("🖥️ Interactive session active - Enter commands below")
        st.text_input(
            "Interactive Input:",
            key="interactive_input",
            placeholder="Enter your command here...",
            help="Type your command and press Enter to send",
            on_change=handle_interactive_input,
            args=(st.session_state.get("interactive_input", ""),)
        )

    # Main output area with spacing
    st.markdown("### Command Output")
    output_placeholder = st.empty()
    st.markdown("")  # Add some spacing
    progress_placeholder = st.empty()
    st.markdown("")  # Add some spacing
    status_placeholder = st.empty()

    # Execute command
    if execute and command.strip():
        try:
            # Add command to history
            cmd_entry = {
                'command': command,
                'timestamp': format_timestamp(),
                'return_code': None
            }
            st.session_state.command_history.append(cmd_entry)

            # Clear previous output
            st.session_state.output_text = ''
            st.session_state.progress_value = 0.0
            st.session_state.last_interactive_input = ''

            # Execute command
            st.session_state.command_executor.execute_command(
                command,
                output_placeholder,
                progress_placeholder,
                status_placeholder,
                cmd_entry
            )
        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")
    elif execute:
        st.error("Please enter a command")

    # Update UI elements
    if st.session_state.command_executor.is_running():
        time.sleep(0.1)  # Small delay to prevent too frequent updates
        st.rerun()

    # Display current output
    if st.session_state.output_text:
        output_placeholder.code(st.session_state.output_text)
    if st.session_state.progress_value > 0:
        progress_placeholder.progress(st.session_state.progress_value)

def main():
    # Set page config
    st.set_page_config(
        page_title="Web Terminal",
        page_icon="🖥️",
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Apply custom styles
    apply_styles()

    # Sidebar with command history
    with st.sidebar:
        st.title("Command History")
        if st.session_state.command_history:
            for cmd in reversed(st.session_state.command_history):
                st.text(f"[{cmd['timestamp']}] {cmd['command']}")
                if cmd.get('return_code') is not None:
                    status = "✅" if cmd['return_code'] == 0 else "❌"
                    st.text(f"Status: {status} (Return code: {cmd['return_code']})")
                st.markdown("---")

    # Main terminal page
    terminal_page()

if __name__ == "__main__":
    main()
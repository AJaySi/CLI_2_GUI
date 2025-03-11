import streamlit as st
import time
from datetime import datetime
from command_executor import CommandExecutor
import command_groups

# Initialize session state
def initialize_session_state():
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'command_executor' not in st.session_state:
        st.session_state.command_executor = CommandExecutor()
    if 'current_command' not in st.session_state:
        st.session_state.current_command = None
    if 'interactive_input' not in st.session_state:
        st.session_state.interactive_input = ''
    if 'last_interactive_input' not in st.session_state:
        st.session_state.last_interactive_input = ''
    if 'output_text' not in st.session_state:
        st.session_state.output_text = ''
    if 'progress_value' not in st.session_state:
        st.session_state.progress_value = 0.0
    if 'page' not in st.session_state:
        st.session_state.page = 'terminal'


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

    # Execute and stop buttons
    col1, col2 = st.columns([1, 4])
    with col1:
        execute = st.button("Execute", key="execute_button", type="primary")
    with col2:
        if st.session_state.command_executor.is_running():
            stop = st.button("Stop", key="stop_button", type="secondary")
            if stop:
                st.session_state.command_executor.terminate_current_process()
                st.error("Command execution stopped by user")

    # Interactive input section
    if st.session_state.command_executor.is_interactive():
        st.info("🖥️ Interactive session is active")
        interactive_input = st.text_input(
            "Interactive Input:",
            key="interactive_input",
            placeholder="Enter input for the running command...",
            help="Type your input and press Enter to send it to the running command"
        )
        if interactive_input and interactive_input != st.session_state.last_interactive_input:
            st.session_state.last_interactive_input = interactive_input
            st.session_state.command_executor.send_input(interactive_input)

    # Main output area
    st.markdown("### Command Output")
    output_placeholder = st.empty()
    progress_placeholder = st.empty()
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

            # Execute command
            st.session_state.command_executor.execute_command(
                command,
                output_placeholder,
                progress_placeholder,
                status_placeholder,
                cmd_entry
            )
            st.rerun()

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
        output_placeholder.code(st.session_state.output_text, language="bash") #Added language here.
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

    # Sidebar with navigation and command history
    with st.sidebar:
        st.title("Navigation")

        # Navigation buttons
        if st.button("Terminal", key="nav_terminal", use_container_width=True):
            st.session_state.page = 'terminal'
            st.rerun()

        if st.button("Command Groups", key="nav_cmd_groups", use_container_width=True):
            st.session_state.page = 'command_groups'
            st.rerun()

        st.markdown("---")

        # Command History section
        st.title("Command History")
        if st.session_state.command_history:
            for cmd in reversed(st.session_state.command_history):
                st.text(f"[{cmd['timestamp']}] {cmd['command']}")
                if cmd.get('return_code') is not None:
                    status = "✅" if cmd['return_code'] == 0 else "❌"
                    st.text(f"Status: {status} (Return code: {cmd['return_code']})")
                st.markdown("---")

    # Display page based on selection
    if st.session_state.page == 'terminal':
        terminal_page()
    else:
        command_groups.run()

if __name__ == "__main__":
    main()
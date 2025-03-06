
import streamlit as st
import time
from datetime import datetime
from command_executor import CommandExecutor

# Enable Streamlit to share application state across reruns
st.cache_resource.clear()

# Make sure set_page_config is the very first Streamlit command
st.set_page_config(
    page_title="Web Terminal",
    page_icon="🖥️",
    layout="wide"
)

# Import styles after st.set_page_config
from styles import apply_styles

def initialize_session_state():
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'command_executor' not in st.session_state:
        st.session_state.command_executor = CommandExecutor()
    if 'current_command' not in st.session_state:
        st.session_state.current_command = None
    if 'interactive_input' not in st.session_state:
        st.session_state.interactive_input = ''

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    # Apply styles after page config
    apply_styles()
    initialize_session_state()

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

    # Main terminal interface
    st.title("Web Terminal")
    st.markdown("Enter commands below to execute them. Use the sidebar to view command history.")

    # Command input
    command = st.text_input(
        "Enter command:",
        key="command_input",
        placeholder="Type your command here (e.g., ls, pwd, python)",
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

    # Interactive input section (only shown when in interactive mode)
    if st.session_state.command_executor.is_interactive():
        st.info("🖥️ Interactive session is active. Enter your input below and press Enter to send.")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            interactive_input = st.text_input(
                "Interactive Input:",
                key="interactive_input",
                placeholder="Enter input for the running command...",
                help="Type your input and press Enter to send it to the running command"
            )
        with col2:
            send_button = st.button("Send", key="send_input_button")
            
        if (interactive_input and interactive_input != st.session_state.interactive_input) or send_button:
            if interactive_input:
                st.session_state.interactive_input = interactive_input
                st.session_state.command_executor.send_input(interactive_input)
                # Clear the input field after sending
                st.session_state.interactive_input = ""

    # Main output area - create containers to ensure visibility
    st.markdown("### Command Output")
    output_container = st.container()
    with output_container:
        output_placeholder = st.empty()
    
    progress_container = st.container()
    with progress_container:
        progress_placeholder = st.empty()
    
    status_container = st.container()
    with status_container:
        status_placeholder = st.empty()

    if execute and command.strip():
        try:
            # Add command to history
            cmd_entry = {
                'command': command,
                'timestamp': format_timestamp(),
                'return_code': None
            }
            st.session_state.command_history.append(cmd_entry)

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

if __name__ == "__main__":
    main()

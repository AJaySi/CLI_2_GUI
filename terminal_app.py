
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
    if 'last_interactive_input' not in st.session_state:
        st.session_state.last_interactive_input = ''

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    # Apply styles after page config
    apply_styles()
    initialize_session_state()
    
    # Initialize output updates queue if needed
    if 'output_updates' not in st.session_state:
        st.session_state.output_updates = []

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
                
    # Initialize output state variables if they don't exist
    if "latest_output" not in st.session_state:
        st.session_state["latest_output"] = ""
    if "latest_progress" not in st.session_state:
        st.session_state["latest_progress"] = 0.0
    if "output_pending" not in st.session_state:
        st.session_state["output_pending"] = False
    if "command_completed" not in st.session_state:
        st.session_state["command_completed"] = False

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
            
        # Store the last input in a different session state variable
        if 'last_interactive_input' not in st.session_state:
            st.session_state.last_interactive_input = ""
            
        if (interactive_input and interactive_input != st.session_state.last_interactive_input) or send_button:
            if interactive_input:
                st.session_state.last_interactive_input = interactive_input
                st.session_state.command_executor.send_input(interactive_input)
                # We can't clear the text_input directly, this will be handled on rerun

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

    # Add auto-rerun capability when command is running
    if st.session_state.command_executor.is_running():
        # Force a rerun every 1 second to update UI with latest output
        st.rerun()
    
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
            
            # Force immediate rerun to start showing output
            st.rerun()
        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")
    elif execute:
        st.error("Please enter a command")
        
    # Display current output from session state
    if st.session_state["output_pending"]:
        # Update output display
        if st.session_state["latest_output"]:
            output_placeholder.code(st.session_state["latest_output"], language="bash")
        
        # Update progress bar
        if "latest_progress" in st.session_state:
            progress_placeholder.progress(st.session_state["latest_progress"])
        
        # Show completion status if command is done
        if st.session_state.get("command_completed", False):
            if "latest_status" in st.session_state:
                if st.session_state.get("latest_success", False):
                    status_placeholder.success(st.session_state["latest_status"])
                else:
                    status_placeholder.error(st.session_state["latest_status"])
                # Reset completion flag after showing status
                st.session_state["command_completed"] = False
        
        # Keep output pending flag true to ensure output remains visible

if __name__ == "__main__":
    main()

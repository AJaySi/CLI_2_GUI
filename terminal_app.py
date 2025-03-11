import streamlit as st
import time
from datetime import datetime
from command_executor import CommandExecutor
from nsds_commands import CommandStructure
from styles import apply_styles
from queue import Empty

def initialize_session_state():
    """Initialize session state variables"""
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'command_executor' not in st.session_state:
        st.session_state.command_executor = CommandExecutor()
    if 'last_output' not in st.session_state:
        st.session_state.last_output = ''
    if 'progress_value' not in st.session_state:
        st.session_state.progress_value = 0.0
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'nsds_commands' not in st.session_state:
        st.session_state.nsds_commands = CommandStructure()

def format_timestamp():
    """Return formatted current timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def update_ui_from_queue(output_placeholder, progress_placeholder, status_placeholder):
    """Update UI elements from command output queue"""
    try:
        while True:
            msg_type, data = st.session_state.command_executor._output_queue.get_nowait()
            if msg_type == 'output':
                st.session_state.last_output = st.session_state.command_executor.get_output()
                output_placeholder.code(st.session_state.last_output)
            elif msg_type == 'progress':
                st.session_state.progress_value = data
                if data > 0:
                    progress_placeholder.progress(data)
            elif msg_type == 'status':
                is_success, text = data
                if is_success:
                    status_placeholder.success(text)
                else:
                    status_placeholder.error(text)
            elif msg_type == 'error':
                status_placeholder.error(data)
    except Empty:
        pass

def nsds_command_center():
    """NSDS Command Center UI"""
    st.sidebar.title("NSDS Command Center")

    # Get main categories
    categories = st.session_state.nsds_commands.get_main_categories()

    # Sidebar category selection
    selected_category = st.sidebar.selectbox(
        "Select Command Category",
        categories,
        format_func=lambda x: x.upper(),
        help="Choose a main command category"
    )

    if selected_category:
        st.session_state.selected_category = selected_category

        # Show category description
        st.title(f"{selected_category.upper()}")
        st.markdown(st.session_state.nsds_commands.get_category_title(selected_category))

        # Get subcommands for the category
        subcommands = st.session_state.nsds_commands.get_subcommands(selected_category)

        # Create tabs for subcommands
        if isinstance(subcommands, dict):
            if any(isinstance(v, dict) for v in subcommands.values()):
                # Handle nested subcommands
                for subcategory, subcmds in subcommands.items():
                    if isinstance(subcmds, dict) and "subcommands" in subcmds:
                        st.subheader(subcmds.get("title", subcategory))
                        tabs = st.tabs(list(subcmds["subcommands"].keys()))
                        for tab, (cmd, desc) in zip(tabs, subcmds["subcommands"].items()):
                            with tab:
                                st.write(desc)
                                if st.button(f"Execute {cmd}", key=f"{subcategory}_{cmd}"):
                                    full_command = f"nsds {selected_category} {subcategory} {cmd}"
                                    st.session_state.command_executor.execute_command(full_command)
            else:
                # Handle direct subcommands
                tabs = st.tabs(list(subcommands.keys()))
                for tab, (cmd, desc) in zip(tabs, subcommands.items()):
                    with tab:
                        st.write(desc)
                        if st.button(f"Execute {cmd}", key=f"{selected_category}_{cmd}"):
                            full_command = f"nsds {selected_category} {cmd}"
                            st.session_state.command_executor.execute_command(full_command)

def terminal_page():
    """Main terminal page"""
    # Add NSDS Command Center above the terminal
    nsds_command_center()

    st.markdown("---")
    st.title("Web Terminal")
    st.markdown("Enter commands below to execute them. Use the sidebar to view command history.")

    # Place command input and execute button side by side
    col1, col2 = st.columns([5, 1])

    with col1:
        command = st.text_input(
            "Enter command",
            key="command_input",
            placeholder="Type your command here (e.g., ls, pwd, python)",
            label_visibility="collapsed"
        )

    with col2:
        execute = st.button("Execute", key="execute_button", type="primary", use_container_width=True)

    # Stop button (only shown when command is running)
    if st.session_state.command_executor.is_running():
        if st.button("Stop", key="stop_button", type="secondary"):
            st.session_state.command_executor.terminate_current_process()
            st.error("Command execution stopped by user")

    # Interactive input section
    if st.session_state.command_executor.is_interactive():
        st.info("🖥️ Interactive session active - Enter commands below")

        # Place interactive input and send button side by side
        col1, col2 = st.columns([5, 1])

        with col1:
            interactive_input = st.text_input(
                "Interactive Input",
                key="interactive_input",
                placeholder="Enter your command here...",
                label_visibility="collapsed"
            )

        with col2:
            send = st.button("Send", key="send_button", type="primary", use_container_width=True)

        # Handle interactive input
        if send or (interactive_input and interactive_input.strip()):
            st.session_state.command_executor.send_input(interactive_input)

    # Output area
    st.markdown("### Command Output")
    output_placeholder = st.empty()
    st.markdown("")  # Spacing
    progress_placeholder = st.empty()
    st.markdown("")  # Spacing
    status_placeholder = st.empty()

    # Execute command if requested
    if execute and command.strip():
        try:
            # Add command to history
            cmd_entry = {
                'command': command,
                'timestamp': format_timestamp()
            }
            st.session_state.command_history.append(cmd_entry)

            # Reset output state
            st.session_state.last_output = ''
            st.session_state.progress_value = 0.0

            # Execute command
            st.session_state.command_executor.execute_command(command)

        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")
    elif execute:
        st.error("Please enter a command")

    # Update UI elements
    if st.session_state.command_executor.is_running():
        update_ui_from_queue(output_placeholder, progress_placeholder, status_placeholder)
        time.sleep(0.1)
        st.rerun()

    # Display current output
    if st.session_state.last_output:
        output_placeholder.code(st.session_state.last_output)
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
        st.markdown("---")
        st.title("Command History")
        if st.session_state.command_history:
            for cmd in reversed(st.session_state.command_history):
                st.text(f"[{cmd['timestamp']}] {cmd['command']}")
                st.markdown("---")

    # Main terminal page
    terminal_page()

if __name__ == "__main__":
    main()
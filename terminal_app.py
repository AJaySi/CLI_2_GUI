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
    # Reduce top margin
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            padding-top: 0rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Add title with reduced padding
    st.sidebar.markdown('<h1 style="margin-top: 0; padding-top: 0;">NSDS Command Center</h1>', unsafe_allow_html=True)

    # Search section with clear button
    col1, col2 = st.sidebar.columns([5, 1])
    with col1:
        search_query = st.text_input(
            "🔍 Search Commands",
            key="command_search",
            placeholder="Search commands...",
            help="Search for commands across all categories",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("❌", help="Clear search", key="clear_search"):
            search_query = ""

    # Show search results if there's a query
    if search_query:
        st.sidebar.markdown("### Search Results")
        results = st.session_state.nsds_commands.search_commands(search_query)

        if results:
            for idx, (path, cmd_type, description) in enumerate(results):
                # Create a button for each result with unique key
                safe_key = f"search_result_{idx}_{path.replace(' ', '_')}"
                if st.sidebar.button(
                    f"➡️ {path}",
                    key=safe_key,
                    help=description,
                    use_container_width=True
                ):
                    # Set the category when a search result is clicked
                    category = path.split()[0]
                    st.session_state.selected_category = category
                    st.rerun()
        else:
            st.sidebar.info("No matching commands found")

        st.sidebar.markdown("---")

    # Display categories as a list in sidebar
    st.sidebar.markdown("### Command Categories")

    # Create clickable buttons for each category
    categories = st.session_state.nsds_commands.get_main_categories()
    for category in categories:
        is_selected = st.session_state.selected_category == category
        button_style = "selected" if is_selected else ""

        if st.sidebar.button(
            category.upper(),
            key=f"sidebar_{category}",
            help=st.session_state.nsds_commands.get_category_title(category),
            use_container_width=True,
        ):
            st.session_state.selected_category = category

    # Move command history to bottom of sidebar
    st.sidebar.markdown("---")
    if st.session_state.command_history:
        with st.sidebar.expander("Command History", expanded=False):
            for cmd in reversed(st.session_state.command_history):
                st.text(f"[{cmd['timestamp']}] {cmd['command']}")

    # Main panel content - show category details
    if st.session_state.selected_category:
        selected_category = st.session_state.selected_category

        # Show category title and description with reduced spacing
        st.markdown(f'<h1 style="margin-top: 0; padding-top: 0;">{selected_category.upper()}</h1>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="category-description">{st.session_state.nsds_commands.get_category_title(selected_category)}</div>',
            unsafe_allow_html=True
        )

        # Get subcommands for the category
        subcommands = st.session_state.nsds_commands.get_subcommands(selected_category)

        if isinstance(subcommands, dict):
            if any(isinstance(v, dict) for v in subcommands.values()):
                # Handle nested subcommands
                for subcategory, subcmds in subcommands.items():
                    if isinstance(subcmds, dict) and "subcommands" in subcmds:
                        st.subheader(subcmds.get("title", subcategory))

                        # Create tabs for subcommands
                        tab_labels = list(subcmds["subcommands"].keys())
                        tabs = st.tabs(tab_labels)

                        for tab, (cmd, desc) in zip(tabs, subcmds["subcommands"].items()):
                            with tab:
                                st.markdown(f'<div class="subcommand-description">{desc}</div>', unsafe_allow_html=True)
                                col1, col2 = st.columns([3, 1])
                                with col2:
                                    if st.button(
                                        "Execute",
                                        key=f"{subcategory}_{cmd}_exec",
                                        help=f"Execute the {cmd} command",
                                        use_container_width=True
                                    ):
                                        full_command = f"nsds {selected_category} {subcategory} {cmd}"
                                        st.session_state.command_executor.execute_command(full_command)
            else:
                # Handle direct subcommands
                tab_labels = list(subcommands.keys())
                tabs = st.tabs(tab_labels)

                for tab, (cmd, desc) in zip(tabs, subcommands.items()):
                    with tab:
                        st.markdown(f'<div class="subcommand-description">{desc}</div>', unsafe_allow_html=True)
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button(
                                "Execute",
                                key=f"{selected_category}_{cmd}_exec",
                                help=f"Execute the {cmd} command",
                                use_container_width=True
                            ):
                                full_command = f"nsds {selected_category} {cmd}"
                                st.session_state.command_executor.execute_command(full_command)

def terminal_page():
    """Main terminal page"""
    # Add NSDS Command Center above the terminal
    nsds_command_center()

    st.markdown("---")
    st.title("Web Terminal")
    st.markdown("Enter commands below to execute them.")

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
    progress_placeholder = st.empty()
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

    # Main terminal page
    terminal_page()

if __name__ == "__main__":
    main()
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
    if 'voice_command_pending' not in st.session_state:
        st.session_state.voice_command_pending = None
    if 'command_input_default' not in st.session_state:
        st.session_state.command_input_default = ''

def format_timestamp():
    """Return formatted current timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def update_ui_from_queue(output_placeholder, progress_placeholder, status_placeholder):
    """Update UI elements from command output queue"""
    try:
        # Limit the number of messages processed in each update to prevent blocking
        max_messages = 10
        msg_count = 0
        
        while msg_count < max_messages:
            try:
                msg_type, data = st.session_state.command_executor._output_queue.get_nowait()
                msg_count += 1
                
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
                break
    except Exception as e:
        st.error(f"Error updating UI: {str(e)}")

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
        with st.sidebar.status("🔍 Searching...") as status:
            st.sidebar.markdown("### Search Results")
            results = st.session_state.nsds_commands.search_commands(search_query)
            status.update(label="✅ Search complete", state="complete")

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
                        with st.spinner(f"Loading {path} details..."):
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
            with st.spinner(f"Loading {category} details..."):
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
                                        with st.spinner(f"Preparing command: {cmd}..."):
                                            full_command = f"nsds {selected_category} {subcategory} {cmd}"
                                            st.session_state.command_input_default = full_command
                                            st.rerun()
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
                                with st.spinner(f"Preparing command: {cmd}..."):
                                    full_command = f"nsds {selected_category} {cmd}"
                                    st.session_state.command_input_default = full_command
                                    st.rerun()

def terminal_page():
    """Main terminal page"""
    # Add NSDS Command Center above the terminal
    nsds_command_center()

    st.markdown("---")
    st.title("Web Terminal")
    st.markdown("Enter commands below to execute them.")

    # Place command input, voice input, and execute button side by side
    col1, col2, col3 = st.columns([5, 0.5, 1])

    # Get pending voice command if any
    default_command = st.session_state.voice_command_pending if st.session_state.voice_command_pending else st.session_state.command_input_default
    st.session_state.voice_command_pending = None  # Clear pending command

    with col1:
        command = st.text_input(
            "Enter command",
            key="command_input",
            value=default_command,
            placeholder="Type your command here (e.g., ls, pwd, python)",
            label_visibility="collapsed"
        )
        # Store the current command input for next render
        st.session_state.command_input_default = command

    with col2:
        try:
            from voice_input import voice_input_component, handle_voice_input
            voice_input_component()
            voice_command = handle_voice_input()
            if voice_command:
                st.session_state.voice_command_pending = voice_command
        except Exception as e:
            st.warning(f"Voice input unavailable: {str(e)}")
            pass

    with col3:
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
            with st.spinner("Executing command..."):
                st.session_state.command_executor.execute_command(command)

        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")
    elif execute:
        st.error("Please enter a command")

    # Update UI elements
    if st.session_state.command_executor.is_running():
        update_ui_from_queue(output_placeholder, progress_placeholder, status_placeholder)
        # Use st.experimental_rerun() instead of rerun() with delay, which can cause issues
        st.rerun()

    # Display current output
    if st.session_state.last_output:
        output_placeholder.code(st.session_state.last_output)
    if st.session_state.progress_value > 0:
        progress_placeholder.progress(st.session_state.progress_value)

def main():
    try:
        # Set page config
        st.set_page_config(
            page_title="Web Terminal",
            page_icon="🖥️",
            layout="wide",
            menu_items={
                'Get Help': 'https://www.streamlit.io/community',
                'Report a bug': 'https://github.com/streamlit/streamlit/issues',
                'About': 'NSDS Command Center & Web Terminal Interface'
            }
        )

        # Initialize session state
        initialize_session_state()

        # Apply custom styles
        apply_styles()

        # Use a placeholder to show a simple loading message first
        with st.empty():
            if st.session_state.get('_test_element', None) is None:
                st.session_state._test_element = True
                st.info("Initializing Web Terminal Interface...")
            
            # Main terminal page
            terminal_page()
    except Exception as e:
        st.error(f"An error occurred during application startup: {str(e)}")
        st.info("Try refreshing the page. If the issue persists, check your streamlit installation.")
        
        # Display a simple command line as fallback
        st.subheader("Simple Command Line")
        cmd = st.text_input("Enter a command to execute:")
        if st.button("Run"):
            if cmd:
                try:
                    import subprocess
                    result = subprocess.check_output(cmd, shell=True, text=True)
                    st.code(result)
                except Exception as ex:
                    st.error(f"Command execution failed: {str(ex)}")

if __name__ == "__main__":
    main()
import streamlit as st
import subprocess
import time
from datetime import datetime
import threading
from queue import Queue, Empty
from voice_input import handle_voice_input
from command_suggestions import CommandSuggestionEngine
from styles import apply_styles, get_theme_names

# Initialize session state variables
def initialize_session_state():
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'current_output' not in st.session_state:
        st.session_state.current_output = ""
    if 'is_command_running' not in st.session_state:
        st.session_state.is_command_running = False
    if 'command_process' not in st.session_state:
        st.session_state.command_process = None
    if 'output_queue' not in st.session_state:
        st.session_state.output_queue = Queue()
    if 'suggestion_engine' not in st.session_state:
        st.session_state.suggestion_engine = CommandSuggestionEngine()
    if 'next_command' not in st.session_state:
        st.session_state.next_command = ""
    if 'accessibility_mode' not in st.session_state:
        st.session_state.accessibility_mode = False
    if 'selected_theme' not in st.session_state:
        st.session_state.selected_theme = "Blue to Purple"

def format_timestamp():
    """Return formatted current timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def execute_command(command, output_queue):
    """Execute a shell command and put output in the queue"""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        st.session_state.command_process = process
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                output_queue.put(('output', line))
        
        # Wait for process to complete
        process.wait()
        
        # Put completion status in queue
        if process.returncode == 0:
            output_queue.put(('status', (True, f"Command completed successfully (exit code: {process.returncode})")))
        else:
            output_queue.put(('status', (False, f"Command failed with exit code: {process.returncode}")))
        
        # Clear process reference
        st.session_state.command_process = None
        st.session_state.is_command_running = False
        
    except Exception as e:
        output_queue.put(('error', f"Error executing command: {str(e)}"))
        st.session_state.is_command_running = False
        st.session_state.command_process = None

def terminate_process():
    """Terminate the currently running process"""
    if st.session_state.command_process:
        try:
            st.session_state.command_process.terminate()
            st.session_state.is_command_running = False
            return True
        except Exception:
            return False
    return False

def update_output_area(output_placeholder, status_placeholder):
    """Update the output area with any new content from the queue"""
    try:
        # Process up to 10 messages at a time to avoid blocking
        for _ in range(10):
            try:
                msg_type, data = st.session_state.output_queue.get_nowait()
                
                if msg_type == 'output':
                    st.session_state.current_output += data
                    output_placeholder.code(st.session_state.current_output)
                elif msg_type == 'status':
                    is_success, text = data
                    if is_success:
                        status_placeholder.success(text)
                    else:
                        status_placeholder.error(text)
                elif msg_type == 'error':
                    status_placeholder.error(data)
                    
            except Empty:
                # No more messages in queue
                break
    except Exception as e:
        st.error(f"Error updating output: {str(e)}")

def nsds_basic_commands():
    """Display professional NSDS command sidebar based on original CLI structure"""
    st.sidebar.title("NSDS Command Center")
    
    # Accessibility and theme settings moved to right sidebar
    
    # Command Tree button - Shows all commands
    if st.sidebar.button("📋 Show All Commands", use_container_width=True, help="Display complete command tree"):
        run_nsds_command("nsds -t")
    
    # Auth Management
    with st.sidebar.expander("🔑 Auth Management", expanded=False):
        st.markdown("**Authentication Commands**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Show", use_container_width=True, help="Display current auth configuration"):
                run_nsds_command("nsds auth show")
            if st.button("Edit", use_container_width=True, help="Edit auth configuration"):
                run_nsds_command("nsds auth edit")
        with col2:
            if st.button("Init", use_container_width=True, help="Initialize authentication"):
                run_nsds_command("nsds auth init")
            if st.button("Clean", use_container_width=True, help="Remove auth configuration"):
                run_nsds_command("nsds auth clean")
        if st.button("Commit Changes", use_container_width=True, help="Commit edited auth configuration"):
            run_nsds_command("nsds auth commit")
    
    # Cluster Management
    with st.sidebar.expander("🌐 Cluster Management", expanded=False):
        st.markdown("**Cluster Commands**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Status", use_container_width=True, help="Show cluster status"):
                run_nsds_command("nsds cluster status")
            if st.button("Init", use_container_width=True, help="Initialize cluster"):
                run_nsds_command("nsds cluster init")
            if st.button("Start", use_container_width=True, help="Start services on all nodes"):
                run_nsds_command("nsds cluster start")
        with col2:
            if st.button("Stop", use_container_width=True, help="Stop services on all nodes"):
                run_nsds_command("nsds cluster stop")
            if st.button("Restart", use_container_width=True, help="Restart services on all nodes"):
                run_nsds_command("nsds cluster restart")
            if st.button("Destroy", use_container_width=True, help="Remove NSDS components"):
                run_nsds_command("nsds cluster destroy")
    
    # Configuration Management
    with st.sidebar.expander("⚙️ Configuration", expanded=True):
        # Cluster config
        st.markdown("**Cluster Config**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List Configs", use_container_width=True, help="List cluster configurations"):
                run_nsds_command("nsds config cluster list")
        with col2:
            if st.button("Backup", use_container_width=True, help="Backup configurations"):
                run_nsds_command("nsds config cluster backup")
        
        # NFS config
        st.markdown("**NFS Config**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("NFS List", use_container_width=True, help="List NFS configuration"):
                run_nsds_command("nsds config nfs list")
            if st.button("NFS Enable", use_container_width=True, help="Enable NFS service"):
                run_nsds_command("nsds config nfs enable")
        with col2:
            if st.button("NFS Disable", use_container_width=True, help="Disable NFS service"):
                run_nsds_command("nsds config nfs disable")
            if st.button("NFS Update", use_container_width=True, help="Update NFS configuration"):
                run_nsds_command("nsds config nfs update")
        
        # SMB config
        st.markdown("**SMB Config**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("SMB List", use_container_width=True, help="List SMB configuration"):
                run_nsds_command("nsds config smb list")
            if st.button("SMB Enable", use_container_width=True, help="Enable SMB service"):
                run_nsds_command("nsds config smb enable")
        with col2:
            if st.button("SMB Disable", use_container_width=True, help="Disable SMB service"):
                run_nsds_command("nsds config smb disable")
            if st.button("SMB Update", use_container_width=True, help="Update SMB configuration"):
                run_nsds_command("nsds config smb update")
                
        # File config
        st.markdown("**File Config**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List Files", use_container_width=True, help="List config files"):
                run_nsds_command("nsds config file list")
        with col2:
            if st.button("Update File", use_container_width=True, help="Update config file"):
                run_nsds_command("nsds config file update")
                
        # Docker config
        st.markdown("**Docker Config**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List Docker", use_container_width=True, help="List docker options"):
                run_nsds_command("nsds config docker list")
        with col2:
            if st.button("Update Docker", use_container_width=True, help="Update docker options"):
                run_nsds_command("nsds config docker update")
    
    # Export Management
    with st.sidebar.expander("📁 Export Management", expanded=False):
        # NFS exports
        st.markdown("**NFS Exports**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List NFS", use_container_width=True, help="List NFS exports"):
                run_nsds_command("nsds export nfs list")
            if st.button("Add NFS", use_container_width=True, help="Add NFS export"):
                run_nsds_command("nsds export nfs add")
        with col2:
            if st.button("Show NFS", use_container_width=True, help="Show NFS export details"):
                run_nsds_command("nsds export nfs show")
            if st.button("Remove NFS", use_container_width=True, help="Remove NFS export"):
                run_nsds_command("nsds export nfs remove")
        
        # SMB exports
        st.markdown("**SMB Exports**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List SMB", use_container_width=True, help="List SMB shares"):
                run_nsds_command("nsds export smb list")
            if st.button("Add SMB", use_container_width=True, help="Add SMB share"):
                run_nsds_command("nsds export smb add")
        with col2:
            if st.button("Show SMB", use_container_width=True, help="Show SMB share details"):
                run_nsds_command("nsds export smb show")
            if st.button("Remove SMB", use_container_width=True, help="Remove SMB share"):
                run_nsds_command("nsds export smb remove")
    
    # Node Management
    with st.sidebar.expander("🖥️ Node Management", expanded=False):
        st.markdown("**Node Commands**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Node Status", use_container_width=True, help="Show node status"):
                run_nsds_command("nsds node status")
            if st.button("Add Node", use_container_width=True, help="Add node to cluster"):
                run_nsds_command("nsds node add")
            if st.button("Start Node", use_container_width=True, help="Start services on node"):
                run_nsds_command("nsds node start")
        with col2:
            if st.button("Remove Node", use_container_width=True, help="Remove node from cluster"):
                run_nsds_command("nsds node remove")
            if st.button("Stop Node", use_container_width=True, help="Stop services on node"):
                run_nsds_command("nsds node stop")
            if st.button("Restart Node", use_container_width=True, help="Restart services on node"):
                run_nsds_command("nsds node restart")
    
    # Filesystem Management
    with st.sidebar.expander("💾 Filesystem Management", expanded=False):
        st.markdown("**Filesystem Commands**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List FS", use_container_width=True, help="List filesystems"):
                run_nsds_command("nsds filesystem list")
            if st.button("Add FS", use_container_width=True, help="Add new filesystem"):
                run_nsds_command("nsds filesystem add")
        with col2:
            if st.button("Remove FS", use_container_width=True, help="Remove filesystem"):
                run_nsds_command("nsds filesystem remove")
    
    # Diag & Prereq
    with st.sidebar.expander("🔍 Diagnostics & Prereq", expanded=False):
        st.markdown("**Diagnostic Tools**")
        if st.button("Collect Support Bundle", use_container_width=True, help="Collect diagnostic data"):
            run_nsds_command("nsds diag collect")
            
        st.markdown("**Prerequisite Checks**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Run Checks", use_container_width=True, help="Run prerequisite checks"):
                run_nsds_command("nsds prereq check")
            if st.button("List Checks", use_container_width=True, help="List available checks"):
                run_nsds_command("nsds prereq list")
        with col2:
            if st.button("Show Check", use_container_width=True, help="Show check details"):
                run_nsds_command("nsds prereq show")
    
    # System Utilities
    with st.sidebar.expander("🛠️ System Utilities", expanded=False):
        st.markdown("**File Operations**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("List Files", use_container_width=True, help="List files in current directory"):
                run_nsds_command("ls -la")
            if st.button("Disk Space", use_container_width=True, help="Show disk space usage"):
                run_nsds_command("df -h")
        with col2:
            if st.button("Current Dir", use_container_width=True, help="Show current directory"):
                run_nsds_command("pwd")
            if st.button("Process List", use_container_width=True, help="List running processes"):
                run_nsds_command("ps aux | head -10")
    
    # Command history has been moved to the right sidebar
    
    # Add NSDS Help button
    st.sidebar.markdown("---")
    if st.sidebar.button("📚 NSDS Help & Documentation", use_container_width=True):
        run_nsds_command("nsds --help")

def run_nsds_command(command):
    """Helper function to set command in session state"""
    # Use the nsds stub directly
    # We don't need to replace the path as our stub is now installed at /tmp/nsds
    # and will be found in the PATH when executing commands
    st.session_state.next_command = command
    
    # Clear any existing command input to avoid conflicts
    if 'command_input' in st.session_state:
        del st.session_state.command_input
        
    st.rerun()

def main():
    # Set page config with initial sidebar expanded state
    st.set_page_config(
        page_title="NSDS Terminal",
        page_icon="🖥️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state before CSS
    initialize_session_state()
    
    # Apply the selected theme (if accessibility mode is off)
    if not st.session_state.accessibility_mode:
        apply_styles(st.session_state.selected_theme)
    
    # Add CSS for right sidebar
    st.markdown("""
    <style>
        /* Right sidebar styling */
        [data-testid="stSidebarContent"] ~ div {
            background-color: #21252b;
            border-left: 1px solid #3b4048;
        }
        
        /* Right sidebar headers */
        [data-testid="stSidebarContent"] ~ div h3 {
            color: #56b6c2; /* Different color from left sidebar - Atom cyan */
            font-size: 1.2rem;
            margin-top: 1.2rem;
            margin-bottom: 0.7rem;
            font-weight: 600;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #3b4048;
        }
        
        /* Command history item in right sidebar */
        .command-history-item {
            background-color: #2c313a;
            border: 1px solid #3b4048;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 8px;
            font-family: monospace;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .command-history-item:hover {
            background-color: #333842;
            border-color: #56b6c2;
        }
        
        .command-text {
            color: #98c379; /* Atom green */
            font-weight: 500;
        }
        
        .timestamp {
            color: #7a818e;
            font-size: 0.8em;
            margin-top: 4px;
        }
        
        /* Right sidebar buttons */
        [data-testid="stSidebarContent"] ~ div .stButton button {
            background-color: #2c313a;
            color: #98c379;
            border: 1px solid #3b4048;
            text-align: left;
            font-family: monospace;
            margin-bottom: 4px;
            transition: all 0.2s ease;
        }
        
        [data-testid="stSidebarContent"] ~ div .stButton button:hover {
            background-color: #333842;
            border-color: #56b6c2;
        }
        
        /* High contrast version for accessibility mode */
        .high-contrast [data-testid="stSidebarContent"] ~ div {
            background-color: #000000;
            border-left: 2px solid #ffffff;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div h3 {
            color: #00ffff;
            border-bottom: 2px solid #ffffff;
        }
        
        .high-contrast .command-history-item {
            background-color: #000080;
            border: 2px solid #ffffff;
        }
        
        .high-contrast .command-text {
            color: #00ff00;
            font-weight: bold;
        }
        
        .high-contrast .timestamp {
            color: #ffffff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Apply custom CSS based on selected theme
    if st.session_state.accessibility_mode:
        # High Contrast Accessibility Mode Styling
        st.markdown("""
        <style>
            /* Main app styling with High Contrast for accessibility */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                background-color: #000000;
                color: #ffffff;
            }
            
            /* Make entire background black for maximum contrast */
            .stApp {
                background-color: #000000;
            }
            
            /* Title styling - larger and brighter for visibility */
            h1 {
                color: #ffffff;
                font-weight: 700;
                font-size: 2.2rem;
                margin-bottom: 1.5rem;
                border-bottom: 2px solid #ffffff;
                padding-bottom: 0.8rem;
            }
            
            /* Header styling - yellow for high contrast */
            h3 {
                color: #ffff00;
                font-weight: 700;
                font-size: 1.5rem;
                margin-top: 1.8rem;
                margin-bottom: 1.2rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid #ffff00;
            }
            
            /* Text color - bright white for better readability */
            p, span, div {
                color: #ffffff;
                font-size: 1.1rem;
                line-height: 1.6;
            }
            
            /* Code output styling - maximum contrast */
            pre {
                background-color: #000000;
                color: #00ff00; /* Bright green for maximum contrast */
                padding: 1rem;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 1.1rem;
                line-height: 1.6;
                overflow-x: auto;
                border: 2px solid #ffffff;
            }
            
            /* Code blocks with larger text */
            .stCodeBlock {
                background-color: #000000;
                font-size: 1.1rem;
            }
            
            /* Larger and clearer button styling */
            .stButton button {
                border-radius: 4px;
                font-weight: 700;
                font-size: 1.1rem;
                padding: 0.7rem 1rem;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
            
            /* Primary button - bright blue */
            .stButton button[data-baseweb="button"] {
                background-color: #0000ff;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            
            /* Secondary button - bright red */
            .stButton button[kind="secondary"] {
                background-color: #ff0000;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            
            /* Command input styling - larger and clearer */
            div[data-testid="stTextInput"] input {
                background-color: #000000;
                color: #00ff00;
                border: 2px solid #ffffff;
                border-radius: 4px;
                padding: 0.8rem;
                font-size: 1.2rem;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
            
            /* Enhanced Sidebar styling */
            .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
                background-color: #000000;
                border-right: 2px solid #ffffff;
            }
            
            /* Sidebar text and content */
            .sidebar .sidebar-content, section[data-testid="stSidebar"] {
                background-color: #000000;
            }
            
            /* Sidebar headers */
            section[data-testid="stSidebar"] h1 {
                color: #ffff00;
                font-size: 1.8rem;
                font-weight: 700;
                padding-bottom: 0.7rem;
                margin-bottom: 1.2rem;
                border-bottom: 2px solid #ffffff;
            }
            
            /* Sidebar subheaders */
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, 
            section[data-testid="stSidebar"] .stMarkdown h3 {
                color: #ffff00;
                font-size: 1.4rem;
                font-weight: 700;
                margin-top: 1.4rem;
                margin-bottom: 0.9rem;
                padding-bottom: 0.4rem;
                border-bottom: 2px solid #ffffff;
            }
            
            /* Sidebar button containers */
            section[data-testid="stSidebar"] .stButton {
                margin-bottom: 0.7rem;
            }
            
            /* Sidebar button styling */
            section[data-testid="stSidebar"] .stButton button {
                background-color: #000080;
                color: #ffffff;
                border: 2px solid #ffffff;
                border-radius: 4px;
                text-align: left;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 1.1rem;
                font-weight: 600;
                padding: 0.6rem;
            }
            
            /* Sidebar button focus - for keyboard navigation */
            section[data-testid="stSidebar"] .stButton button:focus {
                outline: 3px solid #ffff00;
                box-shadow: 0 0 0 5px rgba(255,255,0,0.5);
            }
            
            /* Sidebar separators */
            section[data-testid="stSidebar"] hr {
                border-color: #ffffff;
                border-width: 2px;
                margin: 1.8rem 0;
            }
            
            /* Sidebar expander */
            .st-expanderContent {
                background-color: #000000;
                border: 2px solid #ffffff;
                border-radius: 4px;
                padding: 0.8rem;
            }
            
            /* Voice button styling for better visibility */
            #startButton {
                background-color: #0000ff;
                color: #ffffff;
                border: 2px solid #ffffff;
                padding: 0.8rem;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 700;
                font-size: 1.1rem;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
            
            #startButton:disabled {
                background-color: #444444;
                cursor: not-allowed;
            }
            
            /* Status message styling */
            div.stAlert {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #ffffff;
                border-radius: 4px;
                padding: 1rem;
                font-size: 1.1rem;
            }
            
            /* Command history in sidebar */
            .sidebar-content pre, section[data-testid="stSidebar"] code {
                background-color: #000000;
                color: #00ff00;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 1rem;
                border: 1px solid #ffffff;
            }
            
            /* Success messages */
            .element-container .stSuccess {
                background-color: #004400;
                color: #00ff00;
                border: 2px solid #00ff00;
                font-weight: 700;
            }
            
            /* Error messages */
            .element-container .stError {
                background-color: #440000;
                color: #ff0000;
                border: 2px solid #ff0000;
                font-weight: 700;
            }
            
            /* Custom blinking cursor - larger and more visible */
            .terminal-cursor::after {
                content: "▋";
                color: #ffffff;
                font-size: 1.5rem;
                animation: blink 1s step-end infinite;
            }
            
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0; }
            }
            
            /* Suggestion container with higher contrast */
            .suggestion-container {
                background-color: #000080;
                border: 2px solid #ffffff;
                border-radius: 4px;
                margin-top: 8px;
                padding: 12px;
            }
            
            .suggestion-command {
                color: #00ff00;
                font-family: monospace;
                font-size: 1.1rem;
                font-weight: 700;
            }
            
            .suggestion-description {
                color: #ffffff;
                font-size: 1rem;
                margin-left: 12px;
                margin-top: 4px;
            }
            
            /* Screen reader only elements */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border-width: 0;
            }
            
            /* Focus styling for accessibility */
            :focus {
                outline: 3px solid #ffff00;
                outline-offset: 2px;
            }
            
            /* Checkbox styling for the accessibility toggle */
            [data-testid="stCheckbox"] {
                margin: 1rem 0;
            }
            
            [data-testid="stCheckbox"] label {
                font-size: 1.1rem;
                font-weight: 700;
            }
        </style>
        """, unsafe_allow_html=True)
    # Theme is now handled by our apply_styles function when accessibility mode is off
    
    # Display the NSDS command sidebar (left sidebar)
    nsds_basic_commands()
    
    # Create a layout with main content and right sidebar using columns
    main_col, right_sidebar_col = st.columns([3, 1])
    
    # Right sidebar content for command suggestions and history
    with right_sidebar_col:
        st.markdown("## Command Assistant")
        
        # Accessibility settings section
        st.markdown("### 👁️ Accessibility Settings")
        
        accessibility_toggle = st.checkbox(
            "Enable Accessibility Mode", 
            value=st.session_state.accessibility_mode,
            help="High contrast mode with screen reader optimizations"
        )
        
        # Update session state if toggle changed
        if accessibility_toggle != st.session_state.accessibility_mode:
            st.session_state.accessibility_mode = accessibility_toggle
            st.rerun()  # Rerun the app to apply accessibility changes
        
        # Command History Section
        st.markdown("### 📜 Command History")
        
        # Display command history in reverse order (newest first)
        if st.session_state.command_history:
            for i, cmd_entry in enumerate(reversed(st.session_state.command_history[-10:])):
                # Create a clickable history item that runs the command when clicked
                if st.button(
                    f"{cmd_entry['command']}",
                    key=f"history_{i}",
                    help=f"Executed at {cmd_entry['timestamp']}"
                ):
                    st.session_state.next_command = cmd_entry['command']
                    st.rerun()
        else:
            st.info("No commands executed yet.")
            
        # Command Analytics Section if available in the suggestion engine
        st.markdown("### 📊 Command Analytics")
        
        # Get stats from the suggestion engine if available
        if hasattr(st.session_state.suggestion_engine, 'get_command_statistics'):
            stats = st.session_state.suggestion_engine.get_command_statistics()
            
            # Display basic stats
            st.markdown(f"**Total Commands:** {stats.get('total_commands', 0)}")
            st.markdown(f"**Unique Commands:** {stats.get('unique_commands', 0)}")
            
            # Display most used commands
            if stats.get('most_used'):
                st.markdown("**Most Used Commands:**")
                for cmd, count in stats.get('most_used', [])[:3]:
                    st.markdown(f"- `{cmd}`: {count} times")
    
    # Main area with improved accessibility
    with main_col:
        st.title("NSDS Web Terminal")
        
        # Main description with better explanations for screen readers
        if st.session_state.accessibility_mode:
            st.markdown("""
            <p>
                Welcome to the NSDS Web Terminal. This application allows you to execute commands in a 
                terminal-like interface with voice input support. 
                <span class="sr-only">Accessibility mode is enabled, providing high contrast colors and larger text.</span>
            </p>
            <p>
                Enter commands in the text input below and press the Execute button or Enter key. 
                You can also use the quick command buttons in the sidebar menu.
            </p>
            """, unsafe_allow_html=True)
        else:
            st.markdown("Enter commands below to execute them or use the quick commands in the sidebar.")
    
        # Command input and execute button
        # Command section
        # Check for command from sidebar or voice input
        next_command = st.session_state.get('next_command', '')
        if next_command and 'command_input' in st.session_state:
            # Clear it after use to avoid state conflicts
            del st.session_state.command_input
            st.session_state.next_command = ''
        
        # Command input area with voice input and execute button
        cmd_col1, cmd_col2 = st.columns([5, 1])
        
        # Command input field
        with cmd_col1:
            command = st.text_input(
                "Enter command",
                value=next_command if next_command else "", 
                placeholder="Type your command here (e.g., ls, pwd, python)",
                label_visibility="collapsed",
                key="command_input"
            )
        
        # Voice input and execute button
        with cmd_col2:
            # Voice input integration
            voice_text = handle_voice_input()
            if voice_text:
                st.session_state.next_command = voice_text
                st.rerun()
                
            # Execute button
            execute = st.button("Execute", type="primary", use_container_width=True)
            
        # Command suggestions section - only show if there's input to suggest from
        if command:
            suggestions = st.session_state.suggestion_engine.get_suggestions(command)
            if suggestions:
                st.markdown("""
                <style>
                    .suggestion-container {
                        background-color: #383c44;
                        border-radius: 4px;
                        margin-top: 4px;
                        padding: 8px;
                    }
                    .suggestion-command {
                        color: #98c379; /* Atom green */
                        font-family: monospace;
                        font-weight: 500;
                    }
                    .suggestion-description {
                        color: #abb2bf; /* Atom foreground */
                        font-size: 0.85em;
                        margin-left: 10px;
                    }
                    .suggestion-category {
                        color: #61afef;
                        font-size: 0.85em;
                        margin-bottom: 4px;
                        font-weight: 500;
                    }
                    .suggestion-button:hover {
                        background-color: #3e4451;
                    }
                    /* Accessibility enhancements */
                    .high-contrast .suggestion-container {
                        background-color: #000000;
                        border: 2px solid #ffffff;
                    }
                    .high-contrast .suggestion-command {
                        color: #ffffff;
                        font-weight: bold;
                    }
                </style>
                <div class="suggestion-container">
                    <p style="color: #61afef; margin-bottom: 6px; font-size: 0.9em;">
                        <span aria-hidden="true">💡</span> Suggestions:
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Group suggestions by category
                grouped_suggestions = {}
                for suggestion in suggestions:
                    desc_type = suggestion['description']
                    
                    # Extract category from description
                    if "Recent command" in desc_type:
                        category = "Recent Commands"
                    elif "Frequently used" in desc_type:
                        category = "Frequently Used" 
                    elif "Suggested next" in desc_type:
                        category = "Suggested Next"
                    elif "current context" in desc_type:
                        category = "Context-Aware"
                    elif "From history" in desc_type:
                        category = "History Matches"
                    else:
                        category = "Command Suggestions"
                        
                    if category not in grouped_suggestions:
                        grouped_suggestions[category] = []
                    grouped_suggestions[category].append(suggestion)
                
                # Display suggestions by category
                for category, category_suggestions in grouped_suggestions.items():
                    st.markdown(f"**{category}:**")
                    
                    # Create buttons for each suggestion
                    for suggestion in category_suggestions:
                        if st.button(
                            f"{suggestion['command']}",
                            key=f"suggestion_{suggestion['command']}",
                            help=suggestion['description']
                        ):
                            st.session_state.next_command = suggestion['command']
                            st.rerun()
    
    # Show stop button if a command is running
    if st.session_state.is_command_running and st.session_state.command_process:
        if st.button("Stop", type="secondary"):
            if terminate_process():
                st.error("Command execution stopped by user")
    
    # Output area
    st.markdown("### Command Output")
    output_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Show current output if any
    if st.session_state.current_output:
        output_placeholder.code(st.session_state.current_output)
    
    # Execute command if requested
    if execute and command.strip():
        try:
            # Reset output
            st.session_state.current_output = ""
            output_placeholder.code("")
            status_placeholder.empty()
            
            # Add to history
            cmd_entry = {
                'command': command,
                'timestamp': format_timestamp()
            }
            st.session_state.command_history.append(cmd_entry)
            
            # Add to suggestion engine history
            st.session_state.suggestion_engine.add_to_history(command)
            
            # Set running flag
            st.session_state.is_command_running = True
            
            # Execute command in thread
            thread = threading.Thread(
                target=execute_command,
                args=(command, st.session_state.output_queue)
            )
            thread.daemon = True
            thread.start()
            
            # Force rerun to start showing output
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to execute command: {str(e)}")
    elif execute:
        st.error("Please enter a command")
    
    # Update output if command is running
    if st.session_state.is_command_running:
        update_output_area(output_placeholder, status_placeholder)
        # Rerun to continue updating
        time.sleep(0.1)  # Small delay to prevent too frequent refreshes
        st.rerun()

if __name__ == "__main__":
    main()
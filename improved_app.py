import streamlit as st
import subprocess
import time
from datetime import datetime
import threading
from queue import Queue, Empty
from voice_input import handle_voice_input

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
    
    # Display command history with better formatting 
    st.sidebar.markdown("---")
    if st.session_state.command_history:
        with st.sidebar.expander("📜 Command History", expanded=False):
            for cmd in reversed(st.session_state.command_history[-10:]):  # Show last 10 commands
                st.code(f"[{cmd['timestamp']}] {cmd['command']}")
    
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
    st.rerun()

def main():
    # Set page config
    st.set_page_config(
        page_title="NSDS Terminal",
        page_icon="🖥️",
        layout="wide"
    )
    
    # Apply custom CSS directly with Atom One Dark theme
    st.markdown("""
    <style>
        /* Main app styling with Atom One Dark theme */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: #282c34;
            color: #abb2bf;
        }
        
        /* Make entire background match Atom One Dark */
        .stApp {
            background-color: #282c34;
        }
        
        /* Title styling */
        h1 {
            color: #61afef;  /* Atom blue */
            font-weight: 700;
            margin-bottom: 1rem;
            border-bottom: 1px solid #3b4048;
            padding-bottom: 0.5rem;
        }
        
        /* Header styling */
        h3 {
            color: #c678dd; /* Atom purple */
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #3b4048;
        }
        
        /* Text color */
        p, span, div {
            color: #abb2bf;
        }
        
        /* Code output styling */
        pre {
            background-color: #21252b;
            color: #98c379; /* Atom green */
            padding: 1rem;
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            overflow-x: auto;
            border: 1px solid #3b4048;
        }
        
        /* Code blocks */
        .stCodeBlock {
            background-color: #21252b;
        }
        
        /* Button styling */
        .stButton button {
            border-radius: 4px;
            font-weight: 500;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        /* Primary button */
        .stButton button[data-baseweb="button"] {
            background-color: #61afef;
            color: #282c34;
            border: 1px solid #61afef;
        }
        
        /* Secondary button */
        .stButton button[kind="secondary"] {
            background-color: #e06c75;
            color: #282c34;
            border: 1px solid #e06c75;
        }
        
        /* Command input styling */
        div[data-testid="stTextInput"] input {
            background-color: #21252b;
            color: #98c379;
            border: 1px solid #3b4048;
            border-radius: 4px;
            padding: 0.5rem;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        /* Enhanced Sidebar styling */
        .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
            background-color: #21252b;
            border-right: 1px solid #3b4048;
        }
        
        /* Sidebar text and content */
        .sidebar .sidebar-content, section[data-testid="stSidebar"] {
            background-color: #21252b;
        }
        
        /* Sidebar headers */
        section[data-testid="stSidebar"] h1 {
            color: #e5c07b;
            font-size: 1.5rem;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #3b4048;
        }
        
        /* Sidebar subheaders */
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #c678dd;
            font-size: 1.2rem;
            margin-top: 1.2rem;
            margin-bottom: 0.7rem;
            font-weight: 600;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #3b4048;
        }
        
        /* Sidebar button containers */
        section[data-testid="stSidebar"] .stButton {
            margin-bottom: 0.5rem;
        }
        
        /* Sidebar button styling */
        section[data-testid="stSidebar"] .stButton button {
            background-color: #2c313a;
            color: #abb2bf;
            border: 1px solid #3b4048;
            border-radius: 4px;
            text-align: left;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            transition: all 0.2s ease;
        }
        
        /* Sidebar button hover */
        section[data-testid="stSidebar"] .stButton button:hover {
            background-color: #333842;
            border-color: #61afef;
        }
        
        /* Sidebar separators */
        section[data-testid="stSidebar"] hr {
            border-color: #3b4048;
            margin: 1.5rem 0;
        }
        
        /* Sidebar expander */
        .st-expanderContent {
            background-color: #282c34;
            border: 1px solid #3b4048;
            border-radius: 4px;
            padding: 0.5rem;
        }
        
        /* Voice button styling */
        #startButton {
            background-color: #61afef;
            color: #282c34;
            border: 1px solid #61afef;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        #startButton:disabled {
            background-color: #5c6370;
            cursor: not-allowed;
        }
        
        /* Status message styling */
        div.stAlert {
            background-color: #21252b;
            color: #abb2bf;
            border-radius: 4px;
        }
        
        /* Command history in sidebar */
        .sidebar-content pre, section[data-testid="stSidebar"] code {
            background-color: #2c313a;
            color: #98c379;
            padding: 0.3rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }
        
        /* Success messages */
        .element-container .stSuccess {
            background-color: rgba(152, 195, 121, 0.2);
            color: #98c379;
        }
        
        /* Error messages */
        .element-container .stError {
            background-color: rgba(224, 108, 117, 0.2);
            color: #e06c75;
        }
        
        /* Custom blinking cursor */
        .terminal-cursor::after {
            content: "▋";
            color: #61afef;
            animation: blink 1s step-end infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Display the NSDS command sidebar
    nsds_basic_commands()
    
    # Main area
    st.title("NSDS Web Terminal")
    st.markdown("Enter commands below to execute them or use the quick commands in the sidebar.")
    
    # Command input and execute button
    col1, col2 = st.columns([5, 1])
    
    # Check for command from sidebar
    next_command = st.session_state.get('next_command', '')
    if next_command:
        # Clear it after use
        st.session_state.next_command = ''
    
    with col1:
        # Use a container to put command input and voice button side by side
        input_container = st.container()
        input_col1, input_col2 = input_container.columns([9, 1])
        
        with input_col1:
            command = st.text_input(
                "Enter command",
                value=next_command,
                placeholder="Type your command here (e.g., ls, pwd, python)",
                label_visibility="collapsed"
            )
        
        # Voice input in the same row as command input
        with input_col2:
            # Check for voice input and pass it to command input
            voice_text = handle_voice_input()
            if voice_text:
                # Update the command with voice input and rerun to update UI
                st.session_state.next_command = voice_text
                st.rerun()
    
    with col2:
        execute = st.button("Execute", type="primary", use_container_width=True)
    
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
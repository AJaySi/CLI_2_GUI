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
    """Display professional NSDS command sidebar based on the new design reference"""
    with st.sidebar:
        st.title("NSDS Command Center")
        
        # SHOW ALL COMMANDS button at the top with document icon (matches screenshot)
        if st.button("📄 SHOW ALL COMMANDS", use_container_width=True, type="primary"):
            run_nsds_command("nsds -t")
        
        # Auth Management section
        with st.expander("🔑 Auth Management", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("SHOW", help="Display current auth configuration"):
                    run_nsds_command("nsds auth show")
                if st.button("EDIT", help="Edit auth configuration"):
                    run_nsds_command("nsds auth edit")
            with col2:
                if st.button("INIT", help="Initialize authentication"):
                    run_nsds_command("nsds auth init")
                if st.button("CLEAN", help="Remove auth configuration"):
                    run_nsds_command("nsds auth clean")
        
        # Cluster Management
        with st.expander("🌐 Cluster Management", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("STATUS", help="Show cluster status"):
                    run_nsds_command("nsds cluster status")
                if st.button("INIT", help="Initialize cluster"):
                    run_nsds_command("nsds cluster init")
                if st.button("START", help="Start services on all nodes"):
                    run_nsds_command("nsds cluster start")
            with col2:
                if st.button("STOP", help="Stop services on all nodes"):
                    run_nsds_command("nsds cluster stop")
                if st.button("RESTART", help="Restart services on all nodes"):
                    run_nsds_command("nsds cluster restart")
                if st.button("DESTROY", help="Remove NSDS components"):
                    run_nsds_command("nsds cluster destroy")
        
        # Configuration Management
        with st.expander("⚙️ Configuration", expanded=False):
            # Create columns for all configuration options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("LIST", help="List cluster configurations"):
                    run_nsds_command("nsds config cluster list")
                if st.button("NFS LIST", help="List NFS configuration"):
                    run_nsds_command("nsds config nfs list")
                if st.button("NFS ENABLE", help="Enable NFS service"):
                    run_nsds_command("nsds config nfs enable")
                if st.button("SMB LIST", help="List SMB configuration"):
                    run_nsds_command("nsds config smb list")
                if st.button("SMB ENABLE", help="Enable SMB service"):
                    run_nsds_command("nsds config smb enable")
                if st.button("FILE LIST", help="List config files"):
                    run_nsds_command("nsds config file list")
                if st.button("DOCKER LIST", help="List docker options"):
                    run_nsds_command("nsds config docker list")
            with col2:
                if st.button("BACKUP", help="Backup configurations"):
                    run_nsds_command("nsds config cluster backup")
                if st.button("NFS DISABLE", help="Disable NFS service"):
                    run_nsds_command("nsds config nfs disable")
                if st.button("NFS UPDATE", help="Update NFS configuration"):
                    run_nsds_command("nsds config nfs update")
                if st.button("SMB DISABLE", help="Disable SMB service"):
                    run_nsds_command("nsds config smb disable")
                if st.button("SMB UPDATE", help="Update SMB configuration"):
                    run_nsds_command("nsds config smb update")
                if st.button("FILE UPDATE", help="Update config file"):
                    run_nsds_command("nsds config file update")
                if st.button("DOCKER UPDATE", help="Update docker options"):
                    run_nsds_command("nsds config docker update")
        
        # Export Management
        with st.expander("📁 Export Management", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("NFS LIST", key="nfs_list", help="List NFS exports"):
                    run_nsds_command("nsds export nfs list")
                if st.button("NFS ADD", help="Add NFS export"):
                    run_nsds_command("nsds export nfs add")
                if st.button("SMB LIST", key="smb_list", help="List SMB shares"):
                    run_nsds_command("nsds export smb list")
                if st.button("SMB ADD", help="Add SMB share"):
                    run_nsds_command("nsds export smb add")
            with col2:
                if st.button("NFS SHOW", help="Show NFS export details"):
                    run_nsds_command("nsds export nfs show")
                if st.button("NFS REMOVE", help="Remove NFS export"):
                    run_nsds_command("nsds export nfs remove")
                if st.button("SMB SHOW", help="Show SMB share details"):
                    run_nsds_command("nsds export smb show")
                if st.button("SMB REMOVE", help="Remove SMB share"):
                    run_nsds_command("nsds export smb remove")
        
        # Node Management
        with st.expander("🖥️ Node Management", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("STATUS", key="node_status", help="Show node status"):
                    run_nsds_command("nsds node status")
                if st.button("ADD", key="node_add", help="Add node to cluster"):
                    run_nsds_command("nsds node add")
                if st.button("START", key="node_start", help="Start services on node"):
                    run_nsds_command("nsds node start")
            with col2:
                if st.button("REMOVE", key="node_remove", help="Remove node from cluster"):
                    run_nsds_command("nsds node remove")
                if st.button("STOP", key="node_stop", help="Stop services on node"):
                    run_nsds_command("nsds node stop")
                if st.button("RESTART", key="node_restart", help="Restart services on node"):
                    run_nsds_command("nsds node restart")
        
        # Filesystem Management
        with st.expander("💾 Filesystem Management", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("LIST", key="fs_list", help="List filesystems"):
                    run_nsds_command("nsds filesystem list")
                if st.button("ADD", key="fs_add", help="Add new filesystem"):
                    run_nsds_command("nsds filesystem add")
            with col2:
                if st.button("REMOVE", key="fs_remove", help="Remove filesystem"):
                    run_nsds_command("nsds filesystem remove")
        
        # Diagnostics & Prerequisites
        with st.expander("🔍 Diagnostics", expanded=False):
            if st.button("COLLECT BUNDLE", help="Collect diagnostic data"):
                run_nsds_command("nsds diag collect")
                
            col1, col2 = st.columns(2)
            with col1:
                if st.button("CHECK", help="Run prerequisite checks"):
                    run_nsds_command("nsds prereq check")
                if st.button("LIST CHECKS", help="List available checks"):
                    run_nsds_command("nsds prereq list")
            with col2:
                if st.button("SHOW CHECK", help="Show check details"):
                    run_nsds_command("nsds prereq show")
        
        # System Utilities - simplified
        with st.expander("🛠️ System Commands", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("LIST FILES", help="List files"):
                    run_nsds_command("ls -la")
                if st.button("DISK SPACE", help="Show disk space usage"):
                    run_nsds_command("df -h")
            with col2:
                if st.button("CURRENT DIR", help="Show current directory"):
                    run_nsds_command("pwd")
                if st.button("PROCESSES", help="List running processes"):
                    run_nsds_command("ps aux | head -10")

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
    
    # Apply custom styling based on accessibility mode
    if st.session_state.accessibility_mode:
        # High Contrast Accessibility Styling
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
                color: #ffffff !important;
                font-weight: 700;
                font-size: 2.2rem;
                margin-bottom: 1.5rem;
                border-bottom: 2px solid #ffffff;
                padding-bottom: 0.8rem;
            }
            
            /* Header styling - yellow for high contrast */
            h3 {
                color: #ffff00 !important;
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
            }
            
            /* Code output area - high contrast */
            pre {
                background-color: #000080 !important;
                color: #ffffff !important;
                border: 2px solid #ffffff;
                padding: 1rem;
                font-size: 1.1rem;
                font-weight: 600;
            }
            
            /* Button styling - high contrast */
            .stButton button {
                background-color: #ffffff !important;
                color: #000000 !important;
                font-weight: 700 !important;
                border: 2px solid #000000 !important;
                border-radius: 5px !important;
                font-size: 1.1rem !important;
                padding: 0.6rem 1rem !important;
            }
            
            /* Primary button - green with arrow */
            .stButton button[data-testid="baseButton-primary"] {
                background-color: #00ff00 !important;
                color: #000000 !important;
                font-weight: 700 !important;
                border: 2px solid #000000 !important;
            }
            
            /* Secondary button - red */
            .stButton button[data-testid="baseButton-secondary"] {
                background-color: #ff0000 !important;
                color: #ffffff !important;
                font-weight: 700 !important;
                border: 2px solid #ffffff !important;
            }
            
            /* Keep the arrow for primary buttons even in high contrast mode */
            .stButton button[data-testid="baseButton-primary"]::after {
                content: " →" !important;
                display: inline-block !important;
                margin-left: 0.5rem !important;
                font-size: 1.2rem !important;
            }
            
            /* Hover effects for high contrast */
            .stButton button:hover {
                box-shadow: 0 0 0 3px #ffff00 !important;
                transform: none !important; /* No movement, just focus indicator */
            }
            
            /* Input field - high contrast */
            div[data-testid="stTextInput"] input {
                background-color: #000000 !important;
                color: #ffffff !important;
                border: 2px solid #ffffff !important;
                font-weight: 600;
                font-size: 1.1rem;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Modern Professional Blue Gradient Styling
        st.markdown("""
        <style>
            /* Main app styling with blue gradient background */
            .stApp {
                background: linear-gradient(135deg, #1a2a6c, #2a3e89, #2c4893);
            }
            
            /* Main content area styling */
            .main .block-container {
                background-color: rgba(22, 30, 55, 0.8);
                border-radius: 10px;
                padding: 2rem;
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                margin: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Title styling */
            h1 {
                color: #ffffff !important;
                font-weight: 600;
                margin-bottom: 1.5rem;
                padding-bottom: 0.8rem;
                border-bottom: 1px solid rgba(100, 181, 246, 0.5);
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            /* Header styling */
            h3 {
                color: #90caf9 !important;
                font-weight: 600;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid rgba(100, 181, 246, 0.3);
            }
            
            /* Text styling */
            p, span, div {
                color: #e1e1e6;
            }
            
            /* Code output area - terminal style */
            pre {
                background-color: #0d1117 !important;
                color: #c9d1d9 !important;
                border-radius: 6px;
                padding: 1rem;
                border: 1px solid #30363d;
                box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.4);
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            }
            
            /* Command input styling */
            div[data-testid="stTextInput"] input {
                background-color: #162231 !important;
                color: #e2e8f0 !important;
                border: 1px solid #1e88e5 !important;
                border-radius: 4px;
                padding: 0.6rem 1rem;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            
            div[data-testid="stTextInput"] input:focus {
                border: 1px solid #64b5f6 !important;
                box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.3);
            }
            
            /* Button styling - based on modern gradient design */
            .stButton button {
                border-radius: 8px;
                border: none;
                font-weight: 500;
                transition: all 0.2s ease;
                font-size: 0.9rem;
                letter-spacing: 0.3px;
                background: linear-gradient(to right, #0d253f, #1a3b5b) !important;
                color: white !important;
                position: relative;
                padding: 0.6rem 1rem;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            }
            
            /* Add arrow icon to primary buttons */
            .stButton button[data-testid="baseButton-primary"]::after {
                content: " →";
                display: inline-block;
                margin-left: 0.5rem;
                font-size: 1rem;
                transition: transform 0.2s ease;
            }
            
            .stButton button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                background: linear-gradient(to right, #0f2c4a, #1e4268) !important;
            }
            
            /* Arrow animation on hover */
            .stButton button[data-testid="baseButton-primary"]:hover::after {
                transform: translateX(3px);
            }
            
            /* Secondary button - maintain distinct styling */
            .stButton button[data-testid="baseButton-secondary"] {
                background: linear-gradient(to right, #b71c1c, #e53935) !important;
                color: white !important;
            }
            
            /* No arrow for secondary buttons */
            .stButton button[data-testid="baseButton-secondary"]::after {
                content: "";
                margin-left: 0;
            }
            
            /* Status indicators */
            div.stAlert {
                border: none;
                border-radius: 4px;
            }
            
            /* Expander styling in main area */
            .main .stExpander {
                background-color: rgba(22, 30, 55, 0.8);
                border-radius: 8px;
                border: 1px solid rgba(100, 181, 246, 0.3);
                overflow: hidden;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            
            /* Expander header */
            .main .stExpander > div:first-child {
                background: linear-gradient(to right, #0d253f, #1a3b5b);
                padding: 0.75rem 1rem;
                border-bottom: 1px solid rgba(100, 181, 246, 0.3);
                color: white !important;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            /* All text elements inside expander header */
            .main .stExpander > div:first-child p,
            .main .stExpander > div:first-child span {
                color: white !important;
            }
            
            .main .stExpander > div:first-child:hover {
                background: linear-gradient(to right, #0f2c4a, #1e4268);
            }
            
            /* Expander content area */
            .main .stExpander > div:last-child {
                padding: 1rem;
                background-color: rgba(30, 40, 70, 0.5);
            }
            
            /* Text content inside expander body */
            .main .stExpander > div:last-child p, 
            .main .stExpander > div:last-child span,
            .main .stExpander > div:last-child div {
                color: #e1e1e6 !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Add CSS for sidebars - both left and right
    st.markdown("""
    <style>
        /* Left sidebar styling - matching the screenshot */
        section[data-testid="stSidebar"] .block-container {
            background-color: #f1f3f6;
            border-right: 1px solid #e0e5ec;
            padding: 1rem;
            box-shadow: inset -5px 0 15px -5px rgba(0, 0, 0, 0.05);
        }
        
        /* Left sidebar title */
        section[data-testid="stSidebar"] .block-container h1 {
            color: #37474f;
            font-size: 1.5rem;
            font-weight: 600;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #cfd8dc;
        }
        
        /* Left sidebar sections */
        section[data-testid="stSidebar"] .stExpander {
            background-color: #f1f3f6;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 0.8rem;
            border: 1px solid rgba(13, 37, 63, 0.3);
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        section[data-testid="stSidebar"] .stExpander:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.08);
            transform: translateY(-1px);
        }
        
        /* Left sidebar expander header - updated with blue-to-black gradient for all expanders */
        section[data-testid="stSidebar"] .stExpander > div:first-child {
            background: linear-gradient(135deg, #1e5799, #000000) !important;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            font-weight: 600;
            color: white !important;
            display: flex;
            align-items: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        /* Special styling for Auth Management expander removed as we now use inline approach */
        
        /* All text elements inside left sidebar expander header */
        section[data-testid="stSidebar"] .stExpander > div:first-child p,
        section[data-testid="stSidebar"] .stExpander > div:first-child span {
            color: white !important;
            font-weight: 600;
        }
        
        /* Icon in left sidebar expander header */
        section[data-testid="stSidebar"] .stExpander > div:first-child span[aria-hidden="true"] {
            color: rgba(255, 255, 255, 0.85) !important;
            margin-right: 0.5rem;
        }
        
        /* Left sidebar expander content */
        section[data-testid="stSidebar"] .stExpander > div:last-child {
            padding: 0.75rem 0.5rem;
            background-color: #ffffff;
        }
        
        /* Override global button styling for left sidebar buttons */
        section[data-testid="stSidebar"] .stButton button {
            background: #ffffff !important; 
            color: #455a64 !important;
            border: 1px solid #e0e5ec !important;
            border-radius: 4px !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            padding: 0.5rem 0.75rem !important;
            margin: 0.25rem 0 !important;
            text-transform: none !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        
        /* Remove arrow from left sidebar buttons */
        section[data-testid="stSidebar"] .stButton button::after {
            content: "" !important;
            margin-left: 0 !important;
        }
        
        section[data-testid="stSidebar"] .stButton button:hover {
            background: linear-gradient(to right, #f5f7fa, #f5f7fa) !important;
            border-color: #cfd8dc !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.08) !important;
        }
        
        /* Show all commands button - special styling */
        section[data-testid="stSidebar"] .stButton button[kind="primary"] {
            background: linear-gradient(to right, #3a7bd5, #9f5afd) !important;
            color: white !important;
            border: none !important;
            width: 100% !important;
            text-align: center !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
        }
        
        /* Add arrow to primary button */
        section[data-testid="stSidebar"] .stButton button[kind="primary"]::after {
            content: " →" !important;
            display: inline-block !important;
            margin-left: 0.5rem !important;
            transition: transform 0.2s ease !important;
        }
        
        section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
            background: linear-gradient(to right, #2a61b0, #8642e5) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2) !important;
        }
        
        section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover::after {
            transform: translateX(3px) !important;
        }

        /* Right sidebar styling */
        [data-testid="stSidebarContent"] ~ div {
            background-color: #2c3e50;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem;
        }
        
        /* Right sidebar title */
        [data-testid="stSidebarContent"] ~ div h2 {
            color: #ecf0f1;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1.2rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Right sidebar headers */
        [data-testid="stSidebarContent"] ~ div h3 {
            color: #3498db;
            font-size: 1.1rem;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
            font-weight: 600;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Right sidebar expanders */
        [data-testid="stSidebarContent"] ~ div .stExpander {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        [data-testid="stSidebarContent"] ~ div .stExpander:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transform: translateY(-2px);
        }
        
        /* Right sidebar expander header */
        [data-testid="stSidebarContent"] ~ div .stExpander > div:first-child {
            background: linear-gradient(to right, rgba(41, 128, 185, 0.4), rgba(52, 152, 219, 0.3));
            padding: 0.8rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            color: #ecf0f1 !important;
            font-weight: 600;
            display: flex;
            align-items: center;
        }
        
        /* All text elements inside right sidebar expander header */
        [data-testid="stSidebarContent"] ~ div .stExpander > div:first-child p,
        [data-testid="stSidebarContent"] ~ div .stExpander > div:first-child span,
        [data-testid="stSidebarContent"] ~ div .stExpander > div:first-child div {
            color: #ecf0f1 !important;
        }
        
        /* Icon in expander header */
        [data-testid="stSidebarContent"] ~ div .stExpander > div:first-child span[aria-hidden="true"] {
            color: #3498db !important;
            margin-right: 0.5rem;
        }
        
        /* Right sidebar expander content */
        [data-testid="stSidebarContent"] ~ div .stExpander > div:last-child {
            padding: 1rem;
            background-color: rgba(30, 40, 50, 0.5);
        }
        
        /* Text in right sidebar expander content */
        [data-testid="stSidebarContent"] ~ div .stExpander > div:last-child p,
        [data-testid="stSidebarContent"] ~ div .stExpander > div:last-child span,
        [data-testid="stSidebarContent"] ~ div .stExpander > div:last-child div:not(.stButton) {
            color: #ecf0f1 !important;
        }
        
        /* Right sidebar checkboxes */
        [data-testid="stSidebarContent"] ~ div [data-testid="stCheckbox"] {
            margin-bottom: 1rem;
        }
        
        [data-testid="stSidebarContent"] ~ div [data-testid="stCheckbox"] label {
            color: #ecf0f1;
            font-weight: 500;
        }
        
        /* Command history item in right sidebar */
        [data-testid="stSidebarContent"] ~ div .stButton button {
            background-color: rgba(255, 255, 255, 0.1);
            color: #ecf0f1;
            border: none;
            border-radius: 6px;
            text-align: left;
            font-family: 'Consolas', 'Monaco', monospace;
            padding: 0.6rem 0.8rem;
            margin-bottom: 0.5rem;
            transition: all 0.2s ease;
            font-size: 0.9rem;
            width: 100%;
        }
        
        [data-testid="stSidebarContent"] ~ div .stButton button:hover {
            background-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }
        
        /* Info box in right sidebar */
        [data-testid="stSidebarContent"] ~ div .stAlert {
            background-color: rgba(52, 152, 219, 0.2);
            color: #ecf0f1;
            border: 1px solid rgba(52, 152, 219, 0.3);
            border-radius: 6px;
        }
        
        /* Analytics section in right sidebar */
        [data-testid="stSidebarContent"] ~ div .stMarkdown {
            color: #ecf0f1;
        }
        
        [data-testid="stSidebarContent"] ~ div .stMarkdown strong {
            color: #3498db;
            font-weight: 600;
        }
        
        [data-testid="stSidebarContent"] ~ div .stMarkdown code {
            background-color: rgba(236, 240, 241, 0.1);
            color: #2ecc71;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        /* High contrast version for accessibility mode */
        .high-contrast section[data-testid="stSidebar"] .block-container {
            background-color: #000000;
            border-right: 2px solid #ffffff;
        }
        
        .high-contrast section[data-testid="stSidebar"] .block-container h1 {
            color: #ffffff;
            border-bottom: 2px solid #ffffff;
        }
        
        .high-contrast section[data-testid="stSidebar"] .stExpander {
            background-color: #000080;
            border: 2px solid #ffffff;
        }
        
        .high-contrast section[data-testid="stSidebar"] .stButton button {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
            font-weight: bold;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div {
            background-color: #000000;
            border-left: 2px solid #ffffff;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div h2,
        .high-contrast [data-testid="stSidebarContent"] ~ div h3 {
            color: #ffff00;
            border-bottom: 2px solid #ffffff;
        }
        
        /* High contrast right sidebar expanders */
        .high-contrast [data-testid="stSidebarContent"] ~ div .stExpander {
            background-color: #000080;
            border: 2px solid #ffffff;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div .stExpander > div:first-child {
            background-color: #000000;
            border-bottom: 2px solid #ffffff;
            color: #ffff00;
            font-weight: 700;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div .stButton button {
            background-color: #000080;
            color: #ffffff;
            border: 2px solid #ffffff;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div .stMarkdown {
            color: #ffffff;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div .stMarkdown strong {
            color: #ffff00;
        }
        
        .high-contrast [data-testid="stSidebarContent"] ~ div .stMarkdown code {
            background-color: #000080;
            color: #00ff00;
            border: 1px solid #ffffff;
        }
        
        /* High contrast expanders in main area */
        .high-contrast .main .stExpander {
            background-color: #000000;
            border: 2px solid #ffffff;
            border-radius: 6px;
            margin-bottom: 1.5rem;
        }
        
        .high-contrast .main .stExpander > div:first-child {
            background-color: #000080;
            color: #ffffff;
            font-weight: 700;
            font-size: 1.1rem;
            padding: 0.8rem 1rem;
            border-bottom: 2px solid #ffffff;
        }
        
        .high-contrast .main .stExpander > div:last-child {
            background-color: #000000;
            padding: 1rem;
            border-top: none;
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
        st.markdown('<h2 style="font-size: 1.4rem; margin-bottom: 1rem;">Command Assistant</h2>', unsafe_allow_html=True)
        
        # Accessibility settings section in an expander
        with st.expander("👁️ Accessibility Settings", expanded=False):
            accessibility_toggle = st.checkbox(
                "Enable Accessibility Mode", 
                value=st.session_state.accessibility_mode,
                help="High contrast mode with screen reader optimizations"
            )
            
            # Explain what accessibility mode does
            st.markdown("""
            Accessibility mode provides:
            - High contrast colors
            - Larger text and buttons
            - Screen reader optimizations
            - Better keyboard navigation
            """)
            
            # Update session state if toggle changed
            if accessibility_toggle != st.session_state.accessibility_mode:
                st.session_state.accessibility_mode = accessibility_toggle
                st.rerun()  # Rerun the app to apply accessibility changes
        
        # Command History Section in an expander
        with st.expander("📜 Command History", expanded=True):
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
            
        # Command Analytics Section in an expander
        with st.expander("📊 Command Analytics", expanded=False):
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
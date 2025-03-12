import streamlit as st
import subprocess
import time
from datetime import datetime
import threading
from queue import Queue, Empty

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
    """Display simple NSDS command buttons for common operations"""
    st.sidebar.title("NSDS Quick Commands")
    
    # Basic command groups
    st.sidebar.subheader("System")
    if st.sidebar.button("System Info", use_container_width=True):
        run_nsds_command("nsds system info")
    if st.sidebar.button("Disk Usage", use_container_width=True):
        run_nsds_command("nsds system disk-usage")
        
    st.sidebar.subheader("Network")
    if st.sidebar.button("Check Connectivity", use_container_width=True):
        run_nsds_command("nsds network check")
    if st.sidebar.button("Show IP", use_container_width=True):
        run_nsds_command("nsds network ip")
        
    st.sidebar.subheader("Utilities")
    if st.sidebar.button("List Files", use_container_width=True):
        run_nsds_command("ls -la")
    if st.sidebar.button("Current Directory", use_container_width=True):
        run_nsds_command("pwd")
    
    # Display command history    
    st.sidebar.markdown("---")
    if st.session_state.command_history:
        with st.sidebar.expander("Command History", expanded=False):
            for cmd in reversed(st.session_state.command_history):
                st.text(f"[{cmd['timestamp']}] {cmd['command']}")

def run_nsds_command(command):
    """Helper function to set command in session state"""
    # Replace 'nsds' with path to our stub
    modified_command = command.replace('nsds ', '/tmp/nsds ')
    # Set value for the next refresh
    st.session_state.next_command = modified_command
    st.rerun()

def main():
    # Set page config
    st.set_page_config(
        page_title="NSDS Terminal",
        page_icon="🖥️",
        layout="wide"
    )
    
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
        command = st.text_input(
            "Enter command",
            value=next_command,
            placeholder="Type your command here (e.g., ls, pwd, python)",
            label_visibility="collapsed"
        )
    
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
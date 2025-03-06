
import streamlit as st
import subprocess
import time
from command_executor import CommandExecutor

def run():
    st.title("Command Groups Interface")
    
    # Initialize session state for command groups
    if 'selected_group' not in st.session_state:
        st.session_state.selected_group = None
    if 'selected_subcommand' not in st.session_state:
        st.session_state.selected_subcommand = None
    if 'command_executor' not in st.session_state:
        st.session_state.command_executor = CommandExecutor()
    
    # Define command groups and their subcommands
    command_groups = {
        "auth": {
            "description": "Authentication management",
            "subcommands": {
                "clean": "Remove the auth configuration",
                "commit": "Commit the edited auth configuration",
                "edit": "Edit the auth configuration",
                "init": "Initialize the authentication configuration",
                "show": "Display the current auth configuration"
            }
        },
        "cluster": {
            "description": "Cluster-wide operations",
            "subcommands": {
                "destroy": "Stop and remove NSDS components from all nodes in the cluster",
                "init": "Create and initialize the NSDS cluster",
                "rename": "Rename the cluster",
                "restart": "Restart NSDS services on all nodes in the cluster",
                "start": "Start NSDS services on all nodes in the cluster",
                "status": "Display the cluster status",
                "stop": "Stop NSDS services on all nodes in the cluster"
            }
        },
        "config": {
            "description": "Configuration management",
            "subcommands": {
                "cluster": {
                    "backup": "Backup NSDS component configurations",
                    "list": "Display current cluster configurations"
                },
                "docker": {
                    "list": "Show current docker runtime options",
                    "update": "Update docker runtime options"
                },
                "file": {
                    "list": "List config files",
                    "update": "Update an NSDS config file"
                },
                "nfs": {
                    "disable": "Disable NFS service",
                    "enable": "Enable NFS service",
                    "list": "List NFS global config",
                    "update": "Update NFS config"
                },
                "smb": {
                    "disable": "Disable SMB service",
                    "enable": "Enable SMB service",
                    "list": "List SMB global config",
                    "update": "Update SMB config"
                },
                "feature": {
                    "list": "List available features",
                    "update": "Set a feature value"
                }
            }
        },
        "upgrade": {
            "description": "Upgrade management",
            "subcommands": {
                "apply": "Apply NSDS config upgrades on all nodes",
                "check": "Check if NSDS config can be upgraded",
                "status": "Check upgrade status on all nodes"
            }
        },
        "diag": {
            "description": "Diagnostics and debugging",
            "subcommands": {
                "collect": "Collect support bundles for NSDS nodes",
                "lustre": {
                    "debug": "Enable/disable Lustre client diagnostics"
                },
                "nfs": {
                    "debug": "Enable/disable debug for NFS service"
                },
                "smb": {
                    "debug": "Enable/disable debug for SMB service"
                }
            }
        },
        "export": {
            "description": "Export management",
            "subcommands": {
                "nfs": {
                    "add": "Add a new NFS export",
                    "list": "List NFS exports",
                    "load": "Load exports from config",
                    "remove": "Remove NFS exports",
                    "show": "Show NFS exports",
                    "update": "Update existing NFS exports"
                },
                "smb": {
                    "add": "Add a new SMB export",
                    "list": "List SMB exports",
                    "load": "Load exports from config",
                    "remove": "Remove SMB exports",
                    "show": "Show SMB exports",
                    "update": "Update existing SMB exports"
                }
            }
        },
        "filesystem": {
            "description": "File system management",
            "subcommands": {
                "add": "Add a new file system",
                "list": "List file systems",
                "remove": "Remove a file system"
            }
        },
        "node": {
            "description": "Node-specific operations",
            "subcommands": {
                "add": "Add a node to the cluster",
                "remove": "Remove a node from the cluster",
                "rename": "Rename a specific node",
                "restart": "Restart NSDS services on a node",
                "start": "Start NSDS services on a node",
                "status": "Show the current node status",
                "stop": "Stop NSDS services on a node"
            }
        },
        "prereq": {
            "description": "Prerequisite checks",
            "subcommands": {
                "check": "Run prerequisite checks on given nodes",
                "list": "List all checks",
                "show": "Display prerequisite check information"
            }
        }
    }
    
    # Layout with two columns
    col1, col2 = st.columns([1, 3])
    
    # Column 1: Command Groups Selection
    with col1:
        st.subheader("Command Groups")
        for group, data in command_groups.items():
            if st.button(f"{group} - {data['description']}", key=f"group_{group}"):
                st.session_state.selected_group = group
                st.session_state.selected_subcommand = None
                st.rerun()
    
    # Column 2: Subcommands and Command Execution
    with col2:
        # Only show subcommands if a group is selected
        if st.session_state.selected_group:
            group_data = command_groups[st.session_state.selected_group]
            st.subheader(f"{st.session_state.selected_group} - {group_data['description']}")
            
            # Handle nested and non-nested subcommands differently
            subcommands = group_data["subcommands"]
            is_nested = any(isinstance(v, dict) for v in subcommands.values())
            
            if is_nested:
                # Handle nested subcommands with expanders
                for section, cmds in subcommands.items():
                    with st.expander(f"{section}"):
                        for cmd, desc in cmds.items():
                            if st.button(f"{cmd} - {desc}", key=f"subcmd_{section}_{cmd}"):
                                st.session_state.selected_subcommand = f"{section} {cmd}"
                                st.rerun()
            else:
                # Handle flat subcommands
                for cmd, desc in subcommands.items():
                    if st.button(f"{cmd} - {desc}", key=f"subcmd_{cmd}"):
                        st.session_state.selected_subcommand = cmd
                        st.rerun()
            
            # Show command execution area if a subcommand is selected
            if st.session_state.selected_subcommand:
                st.markdown("---")
                st.subheader(f"Execute: {st.session_state.selected_group} {st.session_state.selected_subcommand}")
                
                # Dynamic parameters based on command
                params = {}
                
                # Example parameter fields based on command
                if st.session_state.selected_group == "cluster" and st.session_state.selected_subcommand == "rename":
                    params["name"] = st.text_input("New Cluster Name")
                
                if st.session_state.selected_group == "node" and st.session_state.selected_subcommand == "add":
                    params["node_name"] = st.text_input("Node Name")
                    params["ip_address"] = st.text_input("IP Address")
                
                # Build the command string
                cmd_parts = [st.session_state.selected_group]
                
                # Handle nested subcommands
                if " " in st.session_state.selected_subcommand:
                    cmd_parts.extend(st.session_state.selected_subcommand.split())
                else:
                    cmd_parts.append(st.session_state.selected_subcommand)
                
                # Add parameters
                for key, value in params.items():
                    if value:
                        cmd_parts.append(f"--{key}={value}")
                
                command_string = " ".join(cmd_parts)
                st.code(command_string, language="bash")
                
                # Command execution
                execute_button = st.button("Execute Command", type="primary")
                
                if execute_button:
                    # Create placeholders for output
                    output_placeholder = st.empty()
                    progress_placeholder = st.empty()
                    status_placeholder = st.empty()
                    
                    # Add command to history
                    cmd_entry = {
                        'command': command_string,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'return_code': None
                    }
                    
                    if 'command_history' not in st.session_state:
                        st.session_state.command_history = []
                    
                    st.session_state.command_history.append(cmd_entry)
                    
                    # Execute the command
                    st.session_state.command_executor.execute_command(
                        command_string,
                        output_placeholder,
                        progress_placeholder,
                        status_placeholder,
                        cmd_entry
                    )

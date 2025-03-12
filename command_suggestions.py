import re
from typing import List, Dict, Tuple

class CommandSuggestionEngine:
    """
    Contextual Command Suggestion Engine for NSDS Terminal
    Provides intelligent command suggestions based on user input and history
    """
    
    def __init__(self, command_data=None):
        # Base command categories and common commands for suggestions
        self.base_commands = {
            "nsds": {
                "description": "NSDS Command Line Interface",
                "subcommands": {
                    "auth": ["show", "clean", "commit", "edit", "init"], 
                    "cluster": ["status", "init", "destroy", "rename", "restart", "start", "stop"],
                    "config": ["cluster", "docker", "file", "nfs", "node", "smb", "upgrade"],
                    "export": ["nfs", "smb"],
                    "filesystem": ["add", "list", "remove"],
                    "node": ["status", "add", "remove", "rename", "restart", "start", "stop"],
                    "prereq": ["check", "list", "show"],
                    "diag": ["collect"]
                }
            },
            "system": {
                "description": "System commands",
                "commands": ["ls", "cd", "pwd", "cat", "grep", "find", "df", "ps", "top"]
            }
        }
        
        # Initialize with provided command data if available
        if command_data:
            self.command_data = command_data
        else:
            self.command_data = self.base_commands
            
        # Command context tracking
        self.command_history = []
        self.max_history = 50
        
        # Common command patterns for detection
        self.patterns = {
            "file_operations": re.compile(r'^(ls|cd|pwd|find|cat|grep|mkdir|rm|cp|mv)'),
            "nsds_commands": re.compile(r'^nsds\s+(\w+)(?:\s+(\w+))?(?:\s+(\w+))?'),
            "process_management": re.compile(r'^(ps|top|kill|pkill)'),
            "system_info": re.compile(r'^(df|du|free|uname|hostname)')
        }
        
    def add_to_history(self, command: str) -> None:
        """Add command to history, maintaining max size"""
        if command and command.strip():
            self.command_history.append(command.strip())
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
    
    def get_suggestions(self, current_input: str, max_suggestions: int = 5) -> List[Dict[str, str]]:
        """
        Get command suggestions based on current input and command history
        Returns: List of suggestion dictionaries with 'command' and 'description'
        """
        if not current_input or current_input.isspace():
            return self._get_recent_suggestions(max_suggestions)
        
        suggestions = []
        
        # First priority: direct command completion
        direct_matches = self._get_direct_completion_suggestions(current_input)
        suggestions.extend(direct_matches)
        
        # Second priority: contextual based on command patterns
        context_matches = self._get_contextual_suggestions(current_input)
        suggestions.extend(context_matches)
        
        # Third priority: history-based suggestions
        history_matches = self._get_history_suggestions(current_input)
        suggestions.extend(history_matches)
        
        # Deduplicate while preserving order
        unique_suggestions = []
        seen_commands = set()
        
        for suggestion in suggestions:
            if suggestion['command'] not in seen_commands:
                seen_commands.add(suggestion['command'])
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= max_suggestions:
                    break
        
        return unique_suggestions
    
    def _get_direct_completion_suggestions(self, current_input: str) -> List[Dict[str, str]]:
        """Get suggestions by direct completion of the current command"""
        suggestions = []
        
        # Check for NSDS command completions
        if current_input.startswith("nsds"):
            parts = current_input.split()
            if len(parts) == 1:
                # Just "nsds" - suggest main categories
                for category in self.base_commands["nsds"]["subcommands"]:
                    suggestions.append({
                        "command": f"nsds {category}",
                        "description": f"NSDS {category} commands"
                    })
            elif len(parts) == 2:
                # "nsds category" - suggest subcommands for category
                category = parts[1]
                if category in self.base_commands["nsds"]["subcommands"]:
                    for subcmd in self.base_commands["nsds"]["subcommands"][category]:
                        suggestions.append({
                            "command": f"nsds {category} {subcmd}",
                            "description": f"NSDS {category} {subcmd} command"
                        })
            elif len(parts) >= 3:
                # Handle deeper completion like "nsds config nfs"
                category = parts[1]
                subcategory = parts[2]
                if category == "config" and subcategory in ["nfs", "smb"]:
                    for action in ["enable", "disable", "list", "update"]:
                        suggestions.append({
                            "command": f"nsds config {subcategory} {action}",
                            "description": f"{action.capitalize()} {subcategory.upper()} service"
                        })
                elif category == "export" and subcategory in ["nfs", "smb"]:
                    for action in ["add", "list", "show", "remove", "update"]:
                        suggestions.append({
                            "command": f"nsds export {subcategory} {action}",
                            "description": f"{action.capitalize()} {subcategory.upper()} export"
                        })
        # Check for NSDS subcommands without nsds prefix
        elif current_input in self.base_commands["nsds"]["subcommands"]:
            # Direct match for a main NSDS category, suggest the full NSDS command
            category = current_input
            suggestions.append({
                "command": f"nsds {category}",
                "description": f"NSDS {category} commands"
            })
            # Also suggest specific subcommands for this category
            for subcmd in self.base_commands["nsds"]["subcommands"][category]:
                suggestions.append({
                    "command": f"nsds {category} {subcmd}",
                    "description": f"NSDS {category} {subcmd} command"
                })
        elif any(category.startswith(current_input) for category in self.base_commands["nsds"]["subcommands"]):
            # Partial match for a main NSDS category
            for category in self.base_commands["nsds"]["subcommands"]:
                if category.startswith(current_input):
                    suggestions.append({
                        "command": f"nsds {category}",
                        "description": f"NSDS {category} commands"
                    })
        else:
            # Check if the input might be a subcommand (like "show" or "list")
            for category, subcommands in self.base_commands["nsds"]["subcommands"].items():
                if any(subcmd == current_input or subcmd.startswith(current_input) for subcmd in subcommands):
                    matching_subcommands = [subcmd for subcmd in subcommands if subcmd.startswith(current_input)]
                    for subcmd in matching_subcommands:
                        suggestions.append({
                            "command": f"nsds {category} {subcmd}",
                            "description": f"NSDS {category} {subcmd} command"
                        })
        
        # Always check for system command completions
        for cmd in self.base_commands["system"]["commands"]:
            if cmd.startswith(current_input):
                suggestions.append({
                    "command": cmd,
                    "description": f"System command: {cmd}"
                })
        
        return suggestions
    
    def _get_contextual_suggestions(self, current_input: str) -> List[Dict[str, str]]:
        """Get contextually relevant suggestions based on command patterns"""
        suggestions = []
        
        # File operations context
        if self.patterns["file_operations"].match(current_input):
            if current_input.startswith("ls"):
                suggestions.append({"command": "ls -la", "description": "List all files with details"})
            elif current_input.startswith("grep"):
                suggestions.append({"command": "grep -r \"search_term\" .", "description": "Recursive search"})
            elif current_input.startswith("find"):
                suggestions.append({"command": "find . -name \"*.py\"", "description": "Find Python files"})
        
        # NSDS command context
        elif current_input.startswith("nsds"):
            nsds_match = self.patterns["nsds_commands"].match(current_input)
            if nsds_match:
                category = nsds_match.group(1) if nsds_match.groups() else None
                
                if category == "auth":
                    suggestions.append({"command": "nsds auth show", "description": "Display auth configuration"})
                elif category == "cluster":
                    suggestions.append({"command": "nsds cluster status", "description": "Show cluster status"})
                elif category == "config":
                    subcategory = nsds_match.group(2) if len(nsds_match.groups()) > 1 else None
                    if subcategory == "nfs":
                        suggestions.append({"command": "nsds config nfs list", "description": "List NFS configuration"})
                    elif subcategory == "smb":
                        suggestions.append({"command": "nsds config smb list", "description": "List SMB configuration"})
                    else:
                        suggestions.append({"command": "nsds config cluster list", "description": "List cluster configurations"})
        
        # Direct NSDS category detection without nsds prefix
        elif current_input == "auth" or current_input == "au":
            suggestions.append({"command": "nsds auth show", "description": "Display auth configuration"})
            suggestions.append({"command": "nsds auth init", "description": "Initialize authentication"})
        elif current_input == "cluster" or current_input == "cl":
            suggestions.append({"command": "nsds cluster status", "description": "Show cluster status"})
            suggestions.append({"command": "nsds cluster start", "description": "Start cluster services"})
        elif current_input == "config" or current_input == "co":
            suggestions.append({"command": "nsds config cluster list", "description": "List cluster configurations"})
            suggestions.append({"command": "nsds config nfs list", "description": "List NFS configuration"})
        elif current_input == "node" or current_input == "no":
            suggestions.append({"command": "nsds node status", "description": "Show node status"})
            suggestions.append({"command": "nsds node start", "description": "Start services on node"})
        elif current_input == "export" or current_input == "ex":
            suggestions.append({"command": "nsds export nfs list", "description": "List NFS exports"})
            suggestions.append({"command": "nsds export smb list", "description": "List SMB shares"})
        elif current_input == "filesystem" or current_input == "fi":
            suggestions.append({"command": "nsds filesystem list", "description": "List filesystems"})
        
        # Common NSDS subcommands without prefix
        elif current_input == "show" or current_input == "sh":
            suggestions.append({"command": "nsds auth show", "description": "Show auth configuration"})
            suggestions.append({"command": "nsds export nfs show", "description": "Show NFS export details"})
        elif current_input == "list" or current_input == "li":
            suggestions.append({"command": "nsds config nfs list", "description": "List NFS configuration"})
            suggestions.append({"command": "nsds export smb list", "description": "List SMB shares"})
            suggestions.append({"command": "nsds filesystem list", "description": "List filesystems"})
        elif current_input == "status" or current_input == "st":
            suggestions.append({"command": "nsds cluster status", "description": "Show cluster status"})
            suggestions.append({"command": "nsds node status", "description": "Show node status"})
        elif current_input == "start":
            suggestions.append({"command": "nsds cluster start", "description": "Start all cluster services"})
            suggestions.append({"command": "nsds node start", "description": "Start services on a node"})
        
        # Process commands
        elif self.patterns["process_management"].match(current_input):
            if current_input.startswith("ps"):
                suggestions.append({"command": "ps aux", "description": "List all processes"})
        
        # System info commands
        elif self.patterns["system_info"].match(current_input):
            if current_input.startswith("df"):
                suggestions.append({"command": "df -h", "description": "Show disk space in human-readable format"})
        
        return suggestions
    
    def _get_history_suggestions(self, current_input: str) -> List[Dict[str, str]]:
        """Get suggestions based on command history"""
        suggestions = []
        
        # Match against history for similar commands
        for cmd in reversed(self.command_history):
            if cmd.startswith(current_input) and cmd != current_input:
                suggestions.append({
                    "command": cmd,
                    "description": "From history"
                })
        
        return suggestions
    
    def _get_recent_suggestions(self, max_count: int) -> List[Dict[str, str]]:
        """Get suggestions based on recent commands when input is empty"""
        suggestions = []
        
        # Add recent history first
        for cmd in reversed(self.command_history[-5:]):
            suggestions.append({
                "command": cmd,
                "description": "Recent command"
            })
        
        # Add some common NSDS commands
        common_commands = [
            {"command": "nsds cluster status", "description": "Check cluster status"},
            {"command": "nsds auth show", "description": "Show auth configuration"},
            {"command": "nsds config nfs list", "description": "List NFS configuration"},
            {"command": "nsds node status", "description": "Show node status"}
        ]
        
        suggestions.extend(common_commands)
        
        return suggestions[:max_count]
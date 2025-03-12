import re
import time
from datetime import datetime
from collections import Counter
from typing import List, Dict, Tuple, Optional, Set

class CommandSuggestionEngine:
    """
    Enhanced Contextual Command Suggestion Engine for NSDS Terminal
    Provides intelligent command suggestions based on user input, history,
    usage patterns, and contextual relationships between commands.
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
            
        # Enhanced command context tracking
        self.command_history = []
        self.command_timestamps = []  # For time-based context analysis
        self.max_history = 50
        self.command_frequency = Counter()  # Track command usage frequency
        self.last_context = None  # Last command context
        self.current_working_directory = "~"  # Track working directory for context
        
        # Command sequence patterns - what commands frequently follow others
        self.sequence_patterns = {}
        
        # Common command patterns for detection
        self.patterns = {
            "file_operations": re.compile(r'^(ls|cd|pwd|find|cat|grep|mkdir|rm|cp|mv)'),
            "nsds_commands": re.compile(r'^nsds\s+(\w+)(?:\s+(\w+))?(?:\s+(\w+))?'),
            "process_management": re.compile(r'^(ps|top|kill|pkill)'),
            "system_info": re.compile(r'^(df|du|free|uname|hostname)'),
            "network": re.compile(r'^(ping|telnet|netstat|curl|wget|ssh|nc)'),
            "text_processing": re.compile(r'^(grep|sed|awk|cut|tr|sort|uniq|wc)')
        }
        
        # Contextual relationships between commands
        self.command_contexts = {
            "file_view": {"ls", "cd", "pwd", "find", "du"},
            "file_content": {"cat", "less", "more", "head", "tail", "grep", "nano", "vim"},
            "system_status": {"ps", "top", "df", "free", "uptime", "vmstat"},
            "nsds_status": {"nsds cluster status", "nsds node status", "nsds auth show"},
            "nsds_config": {"nsds config nfs", "nsds config smb", "nsds config cluster"},
            "nsds_export": {"nsds export nfs", "nsds export smb"}
        }
        
    def add_to_history(self, command: str) -> None:
        """
        Add command to history with enhanced context tracking
        Analyzes command patterns and updates frequency counters
        """
        if command and command.strip():
            command = command.strip()
            
            # Add to basic history
            self.command_history.append(command)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                
            # Add to command frequency tracker
            self.command_frequency[command] += 1
            
            # Add timestamp for time-based analysis
            self.command_timestamps.append((command, time.time()))
            if len(self.command_timestamps) > self.max_history:
                self.command_timestamps.pop(0)
                
            # Update command sequence patterns if we have previous commands
            if len(self.command_history) > 1:
                prev_cmd = self.command_history[-2]
                if prev_cmd not in self.sequence_patterns:
                    self.sequence_patterns[prev_cmd] = Counter()
                self.sequence_patterns[prev_cmd][command] += 1
                
            # Track directory changes for context
            if command.startswith('cd '):
                try:
                    new_dir = command.split(' ', 1)[1].strip()
                    # Simplified directory tracking (actual implementation would be more complex)
                    if new_dir.startswith('/'):
                        self.current_working_directory = new_dir
                    elif new_dir == '..':
                        # Go up one level
                        if self.current_working_directory != '/':
                            self.current_working_directory = self.current_working_directory.rsplit('/', 1)[0] or '/'
                    else:
                        # Navigate into subdirectory
                        if self.current_working_directory.endswith('/'):
                            self.current_working_directory += new_dir
                        else:
                            self.current_working_directory += '/' + new_dir
                except:
                    pass  # Ignore errors in directory tracking
                    
            # Determine the command context category
            self.last_context = self._determine_command_context(command)
    
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
        """
        Get intelligent suggestions when input is empty based on
        recent commands, command frequency, and contextual patterns
        """
        suggestions = []
        
        # Get contextual suggestions based on the last command
        if self.command_history:
            context_suggestions = self._get_next_command_suggestions(self.command_history[-1])
            suggestions.extend(context_suggestions)
        
        # Add frequent commands (based on usage patterns)
        frequent_suggestions = self._get_frequent_command_suggestions(3)
        for suggestion in frequent_suggestions:
            suggestions.append({
                "command": suggestion,
                "description": "Frequently used command"
            })
        
        # Add recent history if not already included
        recent_history_set = {sugg["command"] for sugg in suggestions}
        for cmd in reversed(self.command_history[-5:]):
            if cmd not in recent_history_set:
                suggestions.append({
                    "command": cmd,
                    "description": "Recent command"
                })
                recent_history_set.add(cmd)
        
        # Add contextual commands based on current working directory
        if "/export" in self.current_working_directory:
            suggestions.append({"command": "nsds export nfs list", "description": "List NFS exports in current context"})
        elif "/config" in self.current_working_directory:
            suggestions.append({"command": "nsds config cluster list", "description": "List configs in current context"})
        
        # Always include key NSDS status commands as fallbacks
        fallback_commands = [
            {"command": "nsds cluster status", "description": "Check cluster status"},
            {"command": "nsds auth show", "description": "Show auth configuration"},
            {"command": "nsds node status", "description": "Show node status"}
        ]
        
        # Only add fallbacks if not already in suggestions
        fallback_set = {sugg["command"] for sugg in suggestions}
        for cmd in fallback_commands:
            if cmd["command"] not in fallback_set:
                suggestions.append(cmd)
        
        return suggestions[:max_count]
        
    def _determine_command_context(self, command: str) -> Optional[str]:
        """
        Determine the context category of a command
        Returns the context name or None if no specific context is found
        """
        # Check each context type
        for context, commands in self.command_contexts.items():
            for cmd_pattern in commands:
                if command.startswith(cmd_pattern):
                    return context
        
        # Check using regex patterns
        for pattern_name, pattern in self.patterns.items():
            if pattern.match(command):
                return pattern_name
                
        return None
        
    def _get_next_command_suggestions(self, last_command: str) -> List[Dict[str, str]]:
        """
        Get suggestions for commands that typically follow the last executed command
        based on historical command sequences and command context
        """
        suggestions = []
        
        # Check sequence patterns for direct follow-up commands
        if last_command in self.sequence_patterns:
            # Get the most common next commands for this command
            next_commands = self.sequence_patterns[last_command]
            for cmd, count in next_commands.most_common(2):
                suggestions.append({
                    "command": cmd,
                    "description": "Suggested next command"
                })
        
        # Add context-specific suggestions
        context = self._determine_command_context(last_command)
        
        if context == "file_view":
            # After viewing files, suggest examining content
            if last_command.startswith("ls"):
                suggestions.append({"command": "cat filename", "description": "View file content"})
        
        elif context == "nsds_status":
            # After checking status, suggest actions
            if "cluster status" in last_command:
                suggestions.append({"command": "nsds node status", "description": "Check individual node status"})
            elif "node status" in last_command:
                suggestions.append({"command": "nsds cluster start", "description": "Start cluster services"})
        
        elif context == "nsds_config":
            # After config operations, suggest exports
            if "config nfs" in last_command:
                suggestions.append({"command": "nsds export nfs list", "description": "View NFS exports"})
            elif "config smb" in last_command:
                suggestions.append({"command": "nsds export smb list", "description": "View SMB shares"})
        
        return suggestions
        
    def _get_frequent_command_suggestions(self, count: int = 3) -> List[str]:
        """
        Get the most frequently used commands
        """
        # Return the most common commands
        return [cmd for cmd, _ in self.command_frequency.most_common(count)]
        
    def get_command_statistics(self) -> Dict[str, any]:
        """
        Get statistics about command usage for display
        """
        stats = {
            "total_commands": len(self.command_history),
            "unique_commands": len(self.command_frequency),
            "most_used": self.command_frequency.most_common(5),
            "contexts": {}
        }
        
        # Count commands by context
        context_counts = Counter()
        for cmd in self.command_history:
            context = self._determine_command_context(cmd)
            if context:
                context_counts[context] += 1
        
        stats["contexts"] = dict(context_counts)
        
        return stats
import shutil
import re
from typing import Tuple, Optional

class CommandValidator:
    def __init__(self):
        self._common_commands = {
            'ls': 'List directory contents',
            'cd': 'Change directory',
            'pwd': 'Print working directory',
            'echo': 'Print text to terminal',
            'cat': 'Display file contents',
            'python': 'Run Python interpreter',
            'python3': 'Run Python3 interpreter',
            'pip': 'Python package manager',
            'node': 'Run Node.js',
            'npm': 'Node.js package manager',
            'git': 'Version control system',
        }

    def validate_command(self, command: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a command and return validation status, message, and suggestion
        Returns: (is_valid, message, suggestion)
        """
        if not command or command.isspace():
            return False, "Command cannot be empty", None

        # Split command and arguments
        parts = command.strip().split()
        base_command = parts[0]

        # Check if command exists
        if not self._command_exists(base_command):
            suggestion = self._get_suggestion(base_command)
            return False, f"Command '{base_command}' not found", suggestion

        # Validate command syntax
        syntax_valid, syntax_msg = self._validate_syntax(command)
        if not syntax_valid:
            return False, syntax_msg, None

        return True, "Valid command", None

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system"""
        # Check common commands first
        if command in self._common_commands:
            return True
        
        # Check if command exists in system PATH
        return bool(shutil.which(command))

    def _get_suggestion(self, command: str) -> Optional[str]:
        """Get suggestion for similar commands"""
        suggestions = []
        for cmd in self._common_commands:
            # Simple distance-based matching
            if (command in cmd or cmd in command) or \
               (len(command) > 2 and self._levenshtein_distance(command, cmd) <= 2):
                suggestions.append(f"{cmd} ({self._common_commands[cmd]})")
        
        if suggestions:
            return f"Did you mean: {' or '.join(suggestions)}?"
        return None

    def _validate_syntax(self, command: str) -> Tuple[bool, str]:
        """Validate command syntax"""
        # Check for unmatched quotes
        if command.count('"') % 2 != 0 or command.count("'") % 2 != 0:
            return False, "Unmatched quotes in command"

        # Check for invalid pipe syntax
        if '|' in command:
            parts = command.split('|')
            if any(not part.strip() for part in parts):
                return False, "Invalid pipe syntax: missing command before/after |"

        # Check for invalid redirection
        if '>' in command:
            if '>>' in command:
                parts = command.split('>>')
            else:
                parts = command.split('>')
            
            if len(parts) > 2 or not parts[-1].strip():
                return False, "Invalid redirection syntax"

        return True, "Valid syntax"

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

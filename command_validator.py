import shutil

class CommandValidator:
    def __init__(self):
        # Basic list of common commands
        self._common_commands = {
            'ls': 'List directory contents',
            'cd': 'Change directory',
            'pwd': 'Print working directory',
            'python': 'Python interpreter',
            'pip': 'Python package manager',
        }

    def validate_command(self, command: str) -> tuple[bool, str]:
        """Simple command validation"""
        if not command or command.isspace():
            return False, "Please enter a command"

        # Get the base command (first word)
        base_command = command.strip().split()[0]

        # Check if command exists
        if base_command in self._common_commands or shutil.which(base_command):
            return True, "Valid command"

        return False, f"Command '{base_command}' not found"

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
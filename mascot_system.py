import streamlit as st
import openai
import random
import time
from typing import Dict, List, Optional, Tuple

class AIMascot:
    """
    A playful AI mascot that interacts with users in the terminal environment.
    Provides helpful tips, reactions to commands, and occasional humor.
    """
    
    # Mascot appearance and personality traits
    MASCOT_NAME = "Bitsy"
    MASCOT_PERSONALITY = "friendly, knowledgeable, slightly quirky tech assistant"
    
    # Mascot emotion states
    EMOTIONS = {
        "happy": "😄",
        "excited": "🤩",
        "curious": "🧐",
        "thinking": "🤔",
        "surprised": "😮",
        "confused": "😕",
        "funny": "😂",
        "impressed": "👏",
        "teaching": "👨‍🏫",
        "helpful": "🤝",
        "technical": "👨‍💻",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }
    
    # Command categories for targeted reactions
    COMMAND_CATEGORIES = {
        "file_operations": ["ls", "cd", "pwd", "cp", "mv", "rm", "mkdir", "touch", "cat", "less", "head", "tail"],
        "system_info": ["top", "ps", "free", "df", "du", "uname", "hostname", "uptime", "w", "who"],
        "network": ["ping", "curl", "wget", "netstat", "ifconfig", "ip", "ssh", "nslookup", "dig", "traceroute"],
        "package_management": ["apt", "apt-get", "dpkg", "yum", "dnf", "npm", "pip", "conda"],
        "development": ["git", "python", "node", "npm", "make", "gcc", "java", "javac", "mvn"],
        "database": ["mysql", "psql", "mongo", "sqlite3", "redis-cli"],
        "text_processing": ["grep", "sed", "awk", "cut", "sort", "uniq", "wc", "tr", "diff", "find"]
    }
    
    # Tips for different command categories
    TIPS = {
        "file_operations": [
            "Try using 'ls -la' to see hidden files and detailed information.",
            "Need to find a file? Use 'find /path -name \"filename\"'.",
            "Remember, 'rm -rf' is powerful but dangerous - use with caution!"
        ],
        "system_info": [
            "Use 'htop' for a more interactive system monitor than 'top'.",
            "Check disk space usage with 'df -h' for human-readable sizes.",
            "Monitor live memory usage with 'watch free -m'."
        ],
        "network": [
            "Test web API endpoints easily with 'curl -X GET url'.",
            "See all open network connections with 'netstat -tuln'.",
            "Use 'ping -c 4 domain.com' to limit the number of pings."
        ],
        "development": [
            "Use 'git stash' to temporarily save changes without committing.",
            "Python virtual environments keep dependencies clean with 'python -m venv env'.",
            "Debug Python with 'python -m pdb your_script.py'."
        ],
        "text_processing": [
            "Pipe commands together for powerful text processing: 'cat file | grep pattern | sort'.",
            "Count lines, words, and characters with 'wc file.txt'.",
            "Use 'grep -r \"text\" .' to recursively search directories."
        ],
        "general": [
            "Press Ctrl+R to search your command history.",
            "Add '&' at the end of a command to run it in the background.",
            "Use tab completion to save typing and avoid mistakes.",
            "Create command aliases in your .bashrc for frequently used commands.",
            "Redirect output to a file with '>' or append with '>>'."
        ]
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI mascot with optional OpenAI API key for enhanced interactions."""
        self.last_interaction_time = time.time()
        self.interaction_count = 0
        self.command_history = []
        self.current_emotion = "happy"
        self.openai_available = False
        
        # Set up OpenAI if API key is provided
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
                # Test the connection
                self.openai_available = True
            except Exception:
                self.openai_available = False
    
    def react_to_command(self, command: str) -> Dict[str, str]:
        """
        Generate a mascot reaction to a command input.
        Returns a dictionary with emotion, message, and tip keys.
        """
        self.command_history.append(command)
        self.interaction_count += 1
        self.last_interaction_time = time.time()
        
        # For empty commands, give a gentle prompt
        if not command.strip():
            return {
                "emotion": "curious",
                "message": "Waiting for your command!",
                "tip": None
            }
        
        # Use OpenAI for enhanced responses if available
        if self.openai_available and random.random() < 0.3:  # 30% chance for AI-generated response
            try:
                return self._generate_ai_reaction(command)
            except Exception:
                # Fall back to template-based response if AI fails
                pass
        
        # Otherwise use template-based responses
        return self._generate_template_reaction(command)
    
    def _generate_template_reaction(self, command: str) -> Dict[str, str]:
        """Generate reaction based on templates and rules."""
        # Extract the base command (first word)
        base_cmd = command.split()[0].lower()
        
        # Determine the command category
        category = "general"
        for cat, cmds in self.COMMAND_CATEGORIES.items():
            if base_cmd in cmds:
                category = cat
                break
        
        # Select emotion and message based on command and category
        emotion, message = self._get_emotion_and_message(base_cmd, category)
        
        # Decide whether to show a tip (30% chance, or higher for beginners)
        show_tip = random.random() < 0.3
        tip = random.choice(self.TIPS.get(category, self.TIPS["general"])) if show_tip else None
        
        return {
            "emotion": emotion,
            "message": message,
            "tip": tip
        }
    
    def _get_emotion_and_message(self, command: str, category: str) -> Tuple[str, str]:
        """Get appropriate emotion and message for a command."""
        # Special case reactions for common commands
        if command == "ls":
            return "curious", "Looking at what's around?"
        elif command == "cd":
            return "happy", "Navigating to a new location!"
        elif command == "pwd":
            return "helpful", "It's always good to know where you are!"
        elif command == "rm":
            return "warning", "Be careful with deletion commands!"
        elif command == "grep":
            return "thinking", "Searching for patterns... what will we find?"
        elif command == "python":
            return "excited", "Python time! What are we coding today?"
        elif command == "git":
            return "technical", "Managing your code repository, I see!"
        elif command in ["sudo", "su"]:
            return "surprised", "Using superuser powers! With great power comes..."
        elif command in ["help", "man"]:
            return "teaching", "Looking for help? That's what I'm here for!"
        elif command in ["exit", "logout", "quit"]:
            return "funny", "Leaving so soon? I was just getting started!"
        elif "error" in command.lower() or "failed" in command.lower():
            return "confused", "That didn't work? Let's figure out why!"
            
        # Category-based reactions
        if category == "file_operations":
            return random.choice(["happy", "helpful"]), "Managing your files, I see!"
        elif category == "system_info":
            return random.choice(["curious", "technical"]), "Checking out system stats?"
        elif category == "network":
            return random.choice(["technical", "curious"]), "Exploring the network today?"
        elif category == "development":
            return random.choice(["excited", "impressed"]), "Time for some coding magic!"
        elif category == "database":
            return random.choice(["technical", "thinking"]), "Database work needs precision!"
        elif category == "text_processing":
            return random.choice(["thinking", "technical"]), "Processing text like a pro!"
        
        # Default reactions
        return random.choice(["happy", "curious", "thinking"]), "Let's see what happens!"
    
    def _generate_ai_reaction(self, command: str) -> Dict[str, str]:
        """Generate a more sophisticated reaction using OpenAI."""
        if not self.openai_available:
            return self._generate_template_reaction(command)
        
        try:
            # Create prompt for OpenAI
            system_prompt = f"""
            You are {self.MASCOT_NAME}, a {self.MASCOT_PERSONALITY} for a terminal application.
            Create a short, playful response to the user's command, using at most 15 words.
            Include an appropriate emoji from this list: {', '.join(self.EMOTIONS.values())}
            
            Your response should feel helpful and appropriate for a terminal context, and occasionally include
            mild humor or personality. Don't explain what the command does in technical detail,
            but react to it like a friendly assistant would.
            """
            
            user_prompt = f"Command: {command}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=60,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract emoji if present
            emoji = None
            for e in self.EMOTIONS.values():
                if e in content:
                    emoji = e
                    content = content.replace(e, "").strip()
                    break
            
            emotion = "happy"  # default
            for name, e in self.EMOTIONS.items():
                if emoji == e:
                    emotion = name
                    break
            
            # Determine if we should include a tip
            show_tip = random.random() < 0.3
            tip = None
            if show_tip:
                # Extract base command
                base_cmd = command.split()[0].lower()
                category = "general"
                for cat, cmds in self.COMMAND_CATEGORIES.items():
                    if base_cmd in cmds:
                        category = cat
                        break
                tip = random.choice(self.TIPS.get(category, self.TIPS["general"]))
            
            return {
                "emotion": emotion,
                "message": content,
                "tip": tip
            }
        
        except Exception as e:
            # Fall back to template if OpenAI fails
            return self._generate_template_reaction(command)
    
    def get_idle_message(self) -> Optional[Dict[str, str]]:
        """
        Maybe generate an idle message if the user hasn't interacted in a while.
        Has a small random chance of triggering.
        """
        # Only trigger if it's been at least 60 seconds since last interaction
        time_since_last = time.time() - self.last_interaction_time
        if time_since_last < 60:
            return None
        
        # Small random chance (5%) of showing an idle message
        if random.random() > 0.05:
            return None
        
        idle_emotions = ["curious", "thinking", "funny"]
        idle_messages = [
            "Still there? I'm ready when you are!",
            "Just waiting for your next command...",
            "Terminal getting lonely over here!",
            "Need any help thinking of commands?",
            "I wonder what we'll discover next?",
            "Did you know? You can type 'help' for assistance!",
            "Taking a break? That's cool, I'll be here.",
            "Hmm, what shall we try next?"
        ]
        
        return {
            "emotion": random.choice(idle_emotions),
            "message": random.choice(idle_messages),
            "tip": None
        }
    
    def get_welcome_message(self) -> Dict[str, str]:
        """Generate a welcome message when the application starts."""
        welcome_messages = [
            f"Hello! I'm {self.MASCOT_NAME}, your terminal assistant!",
            f"{self.MASCOT_NAME} at your service! Ready for some command-line adventures?",
            f"Welcome! I'm {self.MASCOT_NAME}, here to make terminal work more fun!",
            f"{self.MASCOT_NAME} activated! Let's make terminal magic happen!"
        ]
        
        return {
            "emotion": "excited",
            "message": random.choice(welcome_messages),
            "tip": "Type a command in the input field and click Execute or press Enter to run it."
        }
    
    def get_command_success_message(self) -> Dict[str, str]:
        """Generate a message for successful command execution."""
        success_messages = [
            "Command completed successfully!",
            "All done! That worked perfectly.",
            "Success! Command executed like a charm.",
            "Great job! That command executed without errors.",
            "Command complete! What's next on the agenda?"
        ]
        
        return {
            "emotion": "success",
            "message": random.choice(success_messages),
            "tip": None
        }
    
    def get_command_error_message(self, error_text: str = None) -> Dict[str, str]:
        """Generate a message for failed command execution."""
        error_messages = [
            "Hmm, that didn't quite work.",
            "We've hit a small snag.",
            "That command encountered an error.",
            "Something went wrong with that command.",
            "Oops! Not what we were hoping for."
        ]
        
        # Add a more specific tip if we have error text
        tip = None
        if error_text:
            if "command not found" in error_text:
                tip = "It looks like that command isn't installed or there's a typo."
            elif "permission denied" in error_text:
                tip = "You might need different permissions. Consider using 'sudo' carefully."
            elif "no such file or directory" in error_text:
                tip = "The file or directory doesn't exist. Check the path and spelling."
        
        return {
            "emotion": "error",
            "message": random.choice(error_messages),
            "tip": tip
        }
    
    def render_mascot(self, container, reaction: Dict[str, str]) -> None:
        """Render the mascot with the given reaction in the provided container."""
        emotion = reaction.get("emotion", "happy")
        message = reaction.get("message", "")
        tip = reaction.get("tip")
        
        emoji = self.EMOTIONS.get(emotion, self.EMOTIONS["happy"])
        
        # Create the mascot display
        with container:
            # Use columns for layout - emoji in first, text in second
            cols = st.columns([1, 9])
            
            with cols[0]:
                st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{emoji}</div>", unsafe_allow_html=True)
                
            with cols[1]:
                # Message from mascot
                st.markdown(f"<div style='background-color: #282c34; padding: 10px; border-radius: 10px; margin-bottom: 5px;'><p style='color: #61afef; margin: 0; font-weight: 500;'>{self.MASCOT_NAME}</p><p style='margin: 0; color: #abb2bf;'>{message}</p></div>", unsafe_allow_html=True)
                
                # Optional tip
                if tip:
                    st.markdown(f"<div style='background-color: #2c323c; padding: 8px; border-radius: 8px; margin-top: 5px;'><p style='color: #98c379; margin: 0; font-size: 0.9em;'><strong>Tip:</strong> {tip}</p></div>", unsafe_allow_html=True)


def check_openai_api():
    """Check if OpenAI API key is available in session state."""
    if 'openai_api_key' not in st.session_state:
        return None
    
    api_key = st.session_state.openai_api_key
    if not api_key or not api_key.startswith('sk-'):
        return None
        
    # Verify key works
    try:
        client = openai.OpenAI(api_key=api_key)
        # Minimal test call
        client.models.list(limit=1)
        return api_key
    except Exception:
        return None


def create_mascot_instance():
    """Create or retrieve a mascot instance."""
    if 'mascot' not in st.session_state:
        # Check if OpenAI API key is available
        api_key = check_openai_api()
        st.session_state.mascot = AIMascot(api_key=api_key)
    
    return st.session_state.mascot


def mascot_settings():
    """Settings interface for the mascot."""
    st.markdown("### Mascot Settings")
    
    # OpenAI API key for enhanced responses
    openai_key = st.text_input(
        "OpenAI API Key (optional)",
        type="password",
        help="Provide an OpenAI API key to enable more dynamic mascot responses.",
        key="mascot_openai_key",
        value=st.session_state.get('openai_api_key', '')
    )
    
    if openai_key:
        if st.button("Save API Key"):
            # Update the API key in session state
            st.session_state.openai_api_key = openai_key
            # Recreate mascot instance with new API key
            st.session_state.mascot = AIMascot(api_key=openai_key)
            st.success("API key saved and mascot updated!")

    # Toggle for mascot
    enable_mascot = st.checkbox(
        "Enable Mascot", 
        value=st.session_state.get('enable_mascot', True),
        help="Show or hide the mascot in the terminal interface."
    )
    
    if 'enable_mascot' not in st.session_state or enable_mascot != st.session_state.enable_mascot:
        st.session_state.enable_mascot = enable_mascot
        st.experimental_rerun()


def render_mascot_reaction(command=None, container=None, reaction_type="command"):
    """
    Render a mascot reaction in the provided container based on the reaction type.
    Types: "command", "welcome", "success", "error", "idle"
    """
    if not st.session_state.get('enable_mascot', True) or not container:
        return
        
    mascot = create_mascot_instance()
    
    # Generate the appropriate reaction based on type
    if reaction_type == "welcome":
        reaction = mascot.get_welcome_message()
    elif reaction_type == "success":
        reaction = mascot.get_command_success_message()
    elif reaction_type == "error":
        reaction = mascot.get_command_error_message(command)
    elif reaction_type == "idle":
        reaction = mascot.get_idle_message()
        if not reaction:  # No idle message to show
            return
    else:  # Default to command reaction
        reaction = mascot.react_to_command(command)
    
    # Render the mascot with the reaction
    mascot.render_mascot(container, reaction)
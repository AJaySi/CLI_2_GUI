import streamlit as st

# Define gradient themes
GRADIENT_THEMES = {
    "Default": {
        "name": "Default",
        "gradient": "none",
        "bg_color": "#ffffff",
        "text_color": "#2c3e50",
    },
    "Terminal Dark": {
        "name": "Terminal Dark",
        "gradient": "linear-gradient(135deg, #1a1a1a, #2d2d2d)",
        "bg_color": "#1a1a1a",
        "text_color": "#d4d4d4",
    },
    "Blue to Purple": {
        "name": "Blue to Purple",
        "gradient": "linear-gradient(135deg, #4b6cb7, #182848)",
        "bg_color": "#4b6cb7",
        "text_color": "#ffffff",
    },
    "Green to Blue": {
        "name": "Green to Blue",
        "gradient": "linear-gradient(135deg, #11998e, #38ef7d)",
        "bg_color": "#11998e",
        "text_color": "#ffffff",
    },
    "Sunset": {
        "name": "Sunset", 
        "gradient": "linear-gradient(135deg, #ff512f, #f09819)",
        "bg_color": "#ff512f",
        "text_color": "#ffffff",
    },
    "Dark Ocean": {
        "name": "Dark Ocean",
        "gradient": "linear-gradient(135deg, #141e30, #243b55)",
        "bg_color": "#141e30",
        "text_color": "#ffffff",
    },
    "Midnight City": {
        "name": "Midnight City",
        "gradient": "linear-gradient(135deg, #232526, #414345)",
        "bg_color": "#232526",
        "text_color": "#ffffff",
    },
}

def get_theme_names():
    """Get a list of available theme names"""
    return list(GRADIENT_THEMES.keys())

def get_theme_css(theme_name="Default"):
    """Get CSS for the selected theme"""
    # Get the theme or default if not found
    theme = GRADIENT_THEMES.get(theme_name, GRADIENT_THEMES["Default"])
    
    # Background gradient or color
    if theme["gradient"] == "none":
        background = f"background-color: {theme['bg_color']};"
    else:
        background = f"background: {theme['gradient']};"
    
    # Text color
    text_color = theme["text_color"]
    
    # Return CSS with the theme details
    return {
        "background": background,
        "text_color": text_color
    }

def apply_styles(theme_name="Default"):
    """Apply custom CSS styles with the given theme"""
    
    # Get theme-specific CSS
    theme_css = get_theme_css(theme_name)
    
    # Custom CSS with theme integration
    st.markdown(f"""
    <style>
        /* Main app styling with gradient background */
        .main {{
            {theme_css["background"]}
            min-height: 100vh;
            transition: background 0.5s ease;
        }}
        
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Title styling */
        h1 {{
            color: {theme_css["text_color"]};
            font-weight: 700;
            margin-bottom: 1rem;
        }}
        
        /* Header styling */
        h3 {{
            color: {theme_css["text_color"]};
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* Code output styling */
        pre {{
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 1rem;
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        
        /* Terminal prompt styling */
        .terminal-prompt {{
            color: #4caf50; 
            font-weight: bold;
        }}
        
        /* Command history styling */
        .command-history {{
            padding: 0.5rem;
            margin-top: 0.5rem;
            border-radius: 5px;
            background-color: rgba(0, 0, 0, 0.2);
            max-height: 300px;
            overflow-y: auto;
        }}
        
        /* Sidebar customization */
        .css-1r6slb0 e1tzin5v2 {{
            background-color: rgba(0, 0, 0, 0.1);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* Button styling */
        .stButton>button {{
            border-radius: 4px;
            font-weight: 500;
        }}
        
        /* Primary button */
        .stButton>button[data-testid="baseButton-primary"] {{
            background-color: #2196f3;
            color: white;
        }}
        
        /* Secondary button */
        .stButton>button[data-testid="baseButton-secondary"] {{
            background-color: #f44336;
            color: white;
        }}
        
        /* Command input styling */
        div[data-testid="stTextInput"] input {{
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            padding: 0.5rem;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: rgba(0, 0, 0, 0.2);
            color: {theme_css["text_color"]};
        }}
        
        /* Status message styling */
        div.stAlert {{
            padding: 0.5rem;
            border-radius: 4px;
        }}
        
        /* Voice input area styling */
        #status {{
            font-style: italic;
        }}
        
        #result {{
            padding: 0.5rem;
            border-radius: 4px;
            background-color: rgba(0, 0, 0, 0.2);
            min-height: 30px;
        }}
        
        /* Voice button styling */
        #startButton {{
            background-color: #4caf50;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}
        
        #startButton:disabled {{
            background-color: #cccccc;
            cursor: not-allowed;
        }}
        
        /* Theme selector styling */
        .theme-selector {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .theme-option {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .theme-option:hover {{
            transform: scale(1.1);
        }}
        
        .theme-option.active {{
            border: 2px solid white;
            transform: scale(1.1);
        }}
    </style>
    """, unsafe_allow_html=True)
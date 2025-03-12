import streamlit as st

def apply_styles():
    """Apply custom CSS styles to improve the application's appearance"""
    
    # Custom CSS
    st.markdown("""
    <style>
        /* Main app styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Title styling */
        h1 {
            color: #2c3e50;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        
        /* Header styling */
        h3 {
            color: #34495e;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #eaeaea;
        }
        
        /* Code output styling */
        pre {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 1rem;
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        
        /* Terminal prompt styling */
        .terminal-prompt {
            color: #4caf50; 
            font-weight: bold;
        }
        
        /* Command history styling */
        .command-history {
            padding: 0.5rem;
            margin-top: 0.5rem;
            border-radius: 5px;
            background-color: #f8f9fa;
            max-height: 300px;
            overflow-y: auto;
        }
        
        /* Sidebar customization */
        .css-1r6slb0 e1tzin5v2 {
            background-color: #f8f9fa;
            border-right: 1px solid #eaeaea;
        }
        
        /* Button styling */
        .stButton>button {
            border-radius: 4px;
            font-weight: 500;
        }
        
        /* Primary button */
        .stButton>button[data-testid="baseButton-primary"] {
            background-color: #2196f3;
            color: white;
        }
        
        /* Secondary button */
        .stButton>button[data-testid="baseButton-secondary"] {
            background-color: #f44336;
            color: white;
        }
        
        /* Command input styling */
        div[data-testid="stTextInput"] input {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0.5rem;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        /* Status message styling */
        div.stAlert {
            padding: 0.5rem;
            border-radius: 4px;
        }
        
        /* Voice input area styling */
        #status {
            font-style: italic;
        }
        
        #result {
            padding: 0.5rem;
            border-radius: 4px;
            background-color: #f5f5f5;
            min-height: 30px;
        }
        
        /* Voice button styling */
        #startButton {
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
        }
        
        #startButton:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
    </style>
    """, unsafe_allow_html=True)
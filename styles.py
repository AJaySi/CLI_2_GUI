import streamlit as st

def apply_styles():
    # Apply custom CSS
    st.markdown("""
    <style>
    /* Terminal-like styling */
    .stTextInput input {
        font-family: 'Courier New', monospace;
        background-color: #0e1117;
        color: #fff;
        border: 1px solid #2e6f95;
    }

    /* Command output styling */
    pre {
        background-color: #0e1117;
        color: #cccccc;
        border: 1px solid #2e6f95;
        border-radius: 5px;
        padding: 10px;
        font-family: 'Courier New', monospace;
        max-height: 500px;
        overflow-y: auto;
    }

    /* Button styling */
    .stButton button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
    }

    .stButton button:hover {
        background-color: #2980b9;
    }

    .stButton button:disabled {
        background-color: #95a5a6;
        cursor: not-allowed;
    }

    /* Success message styling */
    .element-container .stSuccess {
        background-color: #27ae60;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }

    /* Error message styling */
    .element-container .stError {
        background-color: #e74c3c;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }

    /* Info message styling */
    .element-container .stInfo {
        background-color: #3498db;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }

    /* Validation feedback styling */
    .command-valid {
        border-color: #27ae60 !important;
    }

    .command-invalid {
        border-color: #e74c3c !important;
    }

    /* Sidebar styling */
    .sidebar .element-container {
        background-color: #262730;
        padding: 0.5rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }

    /* Improve output visibility */
    code {
        background-color: #1e1e1e;
        color: #f8f8f8;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        white-space: pre-wrap;
        display: block;
        overflow-x: auto;
    }

    /* Make progress bar more visible */
    .stProgress > div > div {
        height: 10px !important;
    }

    /* Suggestion styling */
    .suggestion {
        font-style: italic;
        color: #3498db;
        margin-top: 0.25rem;
    }
    </style>
    """, unsafe_allow_html=True)
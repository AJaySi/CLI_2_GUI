import streamlit as st

def apply_styles():
    # Apply custom CSS
    st.markdown("""
    <style>
    /* Base animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    /* Search input styling with animations */
    .stTextInput input {
        background-color: #2d2d2d;
        border: 1px solid #444;
        color: white;
        border-radius: 4px;
        padding: 8px 12px;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus {
        border-color: #3498db;
        box-shadow: 0 0 0 1px #3498db;
        transform: translateY(-1px);
    }

    /* Clear button styling */
    [data-testid="clear_search"] {
        height: 1.8rem !important;
        width: 1.8rem !important;
        min-height: 1.8rem !important;
        padding: 0.2rem !important;
        font-size: 0.7rem !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="clear_search"]:hover {
        transform: scale(1.1);
    }

    /* Sidebar command list styling with animations */
    .sidebar-command {
        background-color: #1e1e1e;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 4px;
        cursor: pointer;
        border: 1px solid #333;
        transition: all 0.3s ease;
        animation: slideIn 0.3s ease;
    }

    .sidebar-command:hover {
        background-color: #2d2d2d;
        border-color: #3498db;
        transform: translateX(5px);
    }

    .sidebar-command.selected {
        background-color: #2980b9;
        border-color: #3498db;
        animation: pulse 0.3s ease;
    }

    /* Search results with animations */
    .search-result {
        animation: fadeIn 0.3s ease;
        transition: all 0.3s ease;
    }

    .search-result:hover {
        transform: translateX(5px);
    }

    /* Tab styling with animations */
    .stTabs {
        background-color: #1e1e1e;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 20px;
    }

    .stTab {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border-radius: 4px !important;
        padding: 8px 16px !important;
        margin-right: 4px !important;
        border: none !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }

    .stTab[aria-selected="true"] {
        background-color: #3498db !important;
        border-color: #3498db !important;
        transform: translateY(-2px);
    }

    .stTab:hover {
        background-color: #404040 !important;
        transform: translateY(-1px);
    }

    /* Execute button with animations */
    .stButton button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    .stButton button:active {
        transform: translateY(0);
    }

    /* Category description with animations */
    .category-description {
        background-color: #2d2d2d;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
        border-left: 4px solid #3498db;
        animation: fadeIn 0.3s ease;
    }

    /* Command output with animations */
    pre {
        background-color: #1e1e1e;
        color: #f8f8f8;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        white-space: pre-wrap;
        display: block;
        overflow-x: auto;
        animation: fadeIn 0.3s ease;
        transition: all 0.3s ease;
    }

    /* Progress bar animation */
    .stProgress > div > div {
        height: 10px !important;
        transition: all 0.3s ease !important;
    }

    /* Command history with animations */
    .element-container {
        animation: fadeIn 0.3s ease;
    }

    /* Status messages with animations */
    .element-container .stSuccess,
    .element-container .stError,
    .element-container .stInfo {
        animation: fadeIn 0.3s ease;
        transition: all 0.3s ease;
    }

    /* Loading spinner styling */
    .stSpinner {
        text-align: center;
        margin: 10px 0;
    }

    /* Status indicator styling */
    .stStatus {
        border-radius: 4px;
        padding: 8px;
        margin: 8px 0;
        animation: fadeIn 0.3s ease;
    }

    /* Status complete animation */
    @keyframes statusComplete {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }

    .stStatus[data-state="complete"] {
        animation: statusComplete 0.5s ease;
    }

    /* Loading state transitions */
    .element-container {
        transition: opacity 0.3s ease;
    }

    .element-container.loading {
        opacity: 0.7;
    }

    /* Spinner animation */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .stSpinner svg {
        animation: spin 1s linear infinite;
    }
    </style>
    """, unsafe_allow_html=True)
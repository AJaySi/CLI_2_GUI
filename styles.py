import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    .stTextInput>div>div>input {
        font-family: monospace;
    }

    /* Interactive mode styling */
    [data-testid="stInfo"] {
        background-color: #f0f7ff;
        border-left: 5px solid #1c83e1;
        padding: 10px;
        border-radius: 5px;
    }

    /* Button styling */
    .stButton>button {
        font-weight: bold;
    }

        .stTextInput > div > div > input {
            background-color: #262730;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            border: 1px solid #00ff00;
        }

        .stButton > button {
            background-color: #262730;
            color: #00ff00;
            border: 1px solid #00ff00;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-family: 'Courier New', Courier, monospace;
        }

        .stButton > button:hover {
            background-color: #00ff00;
            color: #262730;
        }

        pre {
            background-color: #262730 !important;
            color: #00ff00 !important;
            padding: 1rem !important;
            border-radius: 4px !important;
            font-family: 'Courier New', Courier, monospace !important;
        }

        .error {
            color: #ff0000 !important;
        }

        .sidebar .element-container {
            background-color: #262730;
            padding: 0.5rem;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# Rest of your Streamlit app code would go here...  This is a placeholder.
st.title("Interactive Python Terminal")
command = st.text_input("Enter command:")
if st.button("Execute"):
    try:
        exec(command) #This is a very basic example and should be improved for security and error handling
        st.success("Command executed successfully!")
    except Exception as e:
        st.error(f"Error executing command: {e}")
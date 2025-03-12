import streamlit as st

def main():
    st.set_page_config(
        page_title="Test App",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("Simple Test App")
    st.write("If you can see this, the Streamlit app is working!")
    
    # Debug information
    st.write("### Debug Information")
    st.write(f"Streamlit version: {st.__version__}")
    
    import socket
    hostname = socket.gethostname()
    st.write(f"Hostname: {hostname}")
    
    import os
    st.write(f"Current working directory: {os.getcwd()}")
    
    # Add a button for interaction
    if st.button("Click me!"):
        st.success("Button clicked!")

if __name__ == "__main__":
    main()
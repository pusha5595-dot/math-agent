import streamlit as st
import sys
import threading
from time import sleep

# Configuration and backend logic
import config
from main import process_pdfs

# Basic page setup
st.set_page_config(
    page_title="Math AI Agent",
    page_icon="🧮",
    layout="centered"
)

# Custom class to hook standard output (print statements) into Streamlit
class StreamlitLogRedirect:
    def __init__(self, st_empty_element):
        self.st_empty_element = st_empty_element
        self.logs = ""
        
    def write(self, text):
        self.logs += text
        # Scrollable log box
        self.st_empty_element.code(self.logs, language="bash")
        
    def flush(self):
        pass

def render_ui():
    st.title("🧮 Google Drive Math AI Agent")
    st.markdown("Easily extract and format math PDFs into Google Docs with Gemini.")
    
    # Show Config
    with st.expander("⚙️ Current Configuration", expanded=True):
        st.write(f"**Google Drive Input Folder ID:** `{config.INPUT_FOLDER_ID}`")
        st.write(f"**Google Drive Output Docs ID:** `{config.DOCS_FOLDER_ID}`")
        st.write(f"**Gemini Model:** `{config.GEMINI_MODEL}`")
        
    st.divider()

    st.subheader("Manual Execution")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        run_button = st.button("🚀 Process PDFs Now", use_container_width=True, type="primary")
        
    log_container = st.empty()
    
    if run_button:
        with st.spinner("Agent is running..."):
            # Redirect standard print() to the Streamlit UI
            old_stdout = sys.stdout
            sys.stdout = StreamlitLogRedirect(log_container)
            
            try:
                process_pdfs()
                st.success("Processing complete!")
            except Exception as e:
                st.error(f"Error occurred: {e}")
            finally:
                # Restore original print behavior
                sys.stdout = old_stdout

if __name__ == "__main__":
    render_ui()

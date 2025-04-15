import streamlit as st
import os

# CSS for compact layout
def apply_custom_styles():
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1, h2, h3, h4 {
            margin-top: 0;
            margin-bottom: 0.5rem;
        }
        .button-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
            gap: 10px;
        }
        .stButton > button {
            width: 100%;
            border-radius: 4px;
            border: 1px solid #ddd;
            padding: 0.3rem;
            background-color: #f0f0f0;
            color: #000;
        }
        .stTextInput > div > div > input {
            padding: 0.3rem;
        }
        .checkbox-container label {
            font-size: 0.9rem;
        }
        .checkbox-container p {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0;
        }
        .section-title {
            font-weight: bold;
            margin-bottom: 0.3rem;
        }
        .info-text {
            font-size: 0.8rem;
            color: #666;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-top: 0.3rem;
            padding-bottom: 0.3rem;
        }
        hr {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def main():
    # Set page configuration with minimal padding
    st.set_page_config(page_title="Document Processing Pipeline", layout="wide", 
                      initial_sidebar_state="collapsed")
    
    # Apply custom styles
    apply_custom_styles()
    
    # Header - Minimal
    st.markdown("<h2 style='margin-top: 0; margin-bottom: 0.5rem;'>Configure and Run the Pipeline</h2>", unsafe_allow_html=True)
    
    # Tab selection
    tab1, tab2 = st.tabs(["Configure and Run the Pipeline", "About"])
    
    with tab1:
        # Project folder section
        col1, col2, col3 = st.columns([2, 1.2, 1])
        with col1:
            st.markdown("<div class='section-title'>Please select or create your project folder:</div>", unsafe_allow_html=True)
        with col2:
            st.button("Create or Open a Project", use_container_width=True)
        with col3:
            st.markdown("<div class='section-title'>Project Path:</div>", unsafe_allow_html=True)
        
        # Concepts section
        col1, col2 = st.columns([2, 1.2])
        with col1:
            st.markdown("<div class='section-title'>Enter or edit the concepts of your project:</div>", unsafe_allow_html=True)
        with col2:
            st.button("Create/Update Concepts", use_container_width=True)
        
        # Advanced Settings
        st.markdown("<div class='section-title'><u>Advanced Settings:</u></div>", unsafe_allow_html=True)
        
        # Sentence splitter
        col1, col2 = st.columns([2, 1.2])
        with col1:
            st.markdown("<div style='margin-left:20px;'>Adjust the sentence splitter</div>", unsafe_allow_html=True)
        with col2:
            st.button("Edit Sentence Rules", use_container_width=True)
        
        # Section detector
        col1, col2 = st.columns([2, 1.2])
        with col1:
            st.markdown("<div style='margin-left:20px;'>Adjust the section detector</div>", unsafe_allow_html=True)
        with col2:
            st.button("Edit Section Rules", use_container_width=True)
        
        # Negation detector
        col1, col2 = st.columns([2, 1.2])
        with col1:
            st.markdown("<div style='margin-left:20px;'>Adjust the negation detector</div>", unsafe_allow_html=True)
        with col2:
            st.button("Edit Negation Rules", use_container_width=True)
        
        # Input directory
        col1, col2, col3 = st.columns([2, 2.5, 0.5])
        with col1:
            st.markdown("<div class='section-title'>Select the directory with your input documents:</div>", unsafe_allow_html=True)
        with col2:
            st.text_input("", key="input_dir", label_visibility="collapsed")
        with col3:
            st.button("Browse", key="browse_input", use_container_width=True)
        
        # CSV checkbox
        col1, col2 = st.columns([0.5, 3.5])
        with col1:
            use_csv = st.checkbox("Use CSV as input")
        with col2:
            st.markdown("<div style='padding-top:5px;'>ℹ️</div>", unsafe_allow_html=True)
        
        # Output directory
        col1, col2, col3 = st.columns([2, 2.5, 0.5])
        with col1:
            st.markdown("<div class='section-title'>Select the directory for your output results:</div>", unsafe_allow_html=True)
        with col2:
            st.text_input("", key="output_dir", label_visibility="collapsed")
        with col3:
            st.button("Browse", key="browse_output", use_container_width=True)
        
        # Use existing output
        col1, col2 = st.columns([0.5, 3.5])
        with col1:
            use_existing = st.checkbox("Use existing output")
        with col2:
            st.markdown("<div style='padding-top:5px;'>ℹ️</div>", unsafe_allow_html=True)
        
        # Note
        st.markdown("<div class='info-text'>Note: Only .xlsx output files are accepted.</div>", unsafe_allow_html=True)
        
        # Process buttons
        col1, col2 = st.columns(2)
        with col1:
            st.button("Process Documents", use_container_width=True)
        with col2:
            st.button("Review Annotated Documents", use_container_width=True)
    
    with tab2:
        st.markdown("### About")
        st.markdown("This application helps you process and analyze documents using natural language processing.")
        st.markdown("For more information, please refer to the documentation.")

if __name__ == "__main__":
    main()
import streamlit as st
import requests
import time
import base64
from PIL import Image
import io
import os
import json

# API endpoint configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-title {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        color: #1E3A8A !important;
        margin-bottom: 1rem;
    }
    .result-container {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .reference-item {
        background-color: #E5E7EB;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        margin-bottom: 0.5rem;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        font-size: 0.8rem;
        color: #6B7280;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>⚖️ Legal AI Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Get comprehensive legal information and guidance using AI</p>", unsafe_allow_html=True)

# Initialize session state for conversation history
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'waiting_for_response' not in st.session_state:
    st.session_state.waiting_for_response = False
if 'task_id' not in st.session_state:
    st.session_state.task_id = None

# Helper function to convert conversation to API format
def prepare_conversation_history():
    # Format conversation history for the API
    api_format = []
    for msg in st.session_state.conversation_history:
        if msg["role"] == "user":
            api_format.append({
                "type": "human",
                "content": msg["content"],
                "additional_kwargs": {"timestamp": time.time()}
            })
        else:
            api_format.append({
                "type": "ai",
                "content": msg["content"],
                "additional_kwargs": {"timestamp": time.time()}
            })
    return api_format

# Sidebar for input type selection and disclaimers
with st.sidebar:
    st.markdown("<h2 class='sub-title'>Input Options</h2>", unsafe_allow_html=True)
    input_type = st.radio(
        "Select input type:",
        ["Text Query", "Upload Document Image", "Upload PDF Document"]
    )
    
    # Add a button to clear the conversation
    if st.button("Clear Conversation"):
        st.session_state.conversation = []
        st.session_state.conversation_history = []
        st.experimental_rerun()
    
    st.markdown("---")
    st.markdown("<h3>Disclaimer</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        This AI assistant provides legal information for educational purposes only. 
        It is not a substitute for professional legal advice. Always consult with 
        a qualified attorney for specific legal issues.
        """
    )
    
    st.markdown("---")
    st.markdown("<h3>About</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        The Legal AI Assistant uses advanced AI to process legal queries and 
        provide relevant information from legal documents and trusted web sources.
        """
    )

# Main content area
if input_type == "Text Query":
    query = st.text_area("Enter your legal question:", height=100, max_chars=1000)
    submit_button = st.button("Submit Query")
    
    if submit_button and query and not st.session_state.waiting_for_response:
        st.session_state.waiting_for_response = True
        
        # Add user query to conversation display
        st.session_state.conversation.append({"role": "user", "content": query})
        # Add to conversation history for API
        st.session_state.conversation_history.append({"role": "user", "content": query})
        
        with st.spinner("Processing your query..."):
            # Prepare conversation history for API
            api_conversation_history = prepare_conversation_history()
            
            # Send query to API
            response = requests.post(
                f"{API_BASE_URL}/query/text",
                json={
                    "query": query,
                    "conversation_history": api_conversation_history
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.task_id = result["task_id"]
            else:
                st.error(f"Error submitting query: {response.text}")
                st.session_state.waiting_for_response = False

elif input_type == "Upload Document Image":
    query = st.text_input("Optional: Add a specific question about the document")
    uploaded_file = st.file_uploader("Upload an image of a legal document", type=["jpg", "jpeg", "png"])
    submit_button = st.button("Process Document")
    
    if submit_button and uploaded_file and not st.session_state.waiting_for_response:
        st.session_state.waiting_for_response = True
        
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Document", width=400)
        
        # Add to conversation display
        content = f"[Uploaded a document image]" + (f" with question: {query}" if query else "")
        st.session_state.conversation.append({"role": "user", "content": content})
        # Add to conversation history for API
        st.session_state.conversation_history.append({"role": "user", "content": content})
        
        with st.spinner("Processing your document..."):
            # Prepare conversation history for API
            api_conversation_history = prepare_conversation_history()
            
            # Prepare form data
            data = {}
            if query:
                data["query"] = query
            
            # Add conversation history as JSON string
            data["conversation_history"] = json.dumps(api_conversation_history)
                
            # Send to API
            response = requests.post(
                f"{API_BASE_URL}/query/image",
                files={"image": (uploaded_file.name, uploaded_file.getvalue(), "image/jpeg")},
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.task_id = result["task_id"]
            else:
                st.error(f"Error processing document: {response.text}")
                st.session_state.waiting_for_response = False

elif input_type == "Upload PDF Document":
    query = st.text_input("Optional: Add a specific question about the document")
    uploaded_file = st.file_uploader("Upload a legal document", type=["pdf"])
    submit_button = st.button("Process Document")
    
    if submit_button and uploaded_file and not st.session_state.waiting_for_response:
        st.session_state.waiting_for_response = True
        
        # Add to conversation display
        content = f"[Uploaded a PDF document: {uploaded_file.name}]" + (f" with question: {query}" if query else "")
        st.session_state.conversation.append({"role": "user", "content": content})
        # Add to conversation history for API
        st.session_state.conversation_history.append({"role": "user", "content": content})
        
        with st.spinner("Processing your document..."):
            # Prepare conversation history for API
            api_conversation_history = prepare_conversation_history()
            
            # Prepare data
            data = {}
            if query:
                data["query"] = query
            
            # Add conversation history as JSON string
            data["conversation_history"] = json.dumps(api_conversation_history)
            
            # Send to API
            response = requests.post(
                f"{API_BASE_URL}/query/pdf",
                files={"pdf": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.task_id = result["task_id"]
            else:
                st.error(f"Error processing document: {response.text}")
                st.session_state.waiting_for_response = False

# Check for task status if waiting for response
if st.session_state.waiting_for_response and st.session_state.task_id:
    status_placeholder = st.empty()
    
    with status_placeholder.container():
        max_retries = 60  # Maximum number of retries (2 minutes at 2-second intervals)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{API_BASE_URL}/query/status/{st.session_state.task_id}")
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["status"] == "completed":
                        # Add response to conversation display
                        ai_response = result["response"]["final_response"]
                        references = result["response"]["references"]
                        
                        st.session_state.conversation.append({
                            "role": "assistant", 
                            "content": ai_response,
                            "references": references
                        })
                        
                        # Add to conversation history for API
                        st.session_state.conversation_history.append({
                            "role": "assistant", 
                            "content": ai_response
                        })
                        
                        # Update conversation history if returned from API
                        if "conversation_history" in result["response"]:
                            # This is optional - depends on if you want to use the server's version
                            # or keep managing it client-side
                            pass
                        
                        # Clear the waiting state
                        st.session_state.waiting_for_response = False
                        st.session_state.task_id = None
                        status_placeholder.empty()
                        st.experimental_rerun()
                        break
                        
                    elif result["status"] == "error":
                        error_msg = result["response"].get("error", "Unknown error")
                        st.error(f"Error processing request: {error_msg}")
                        st.session_state.waiting_for_response = False
                        st.session_state.task_id = None
                        break
                        
                    else:
                        st.write("Processing your request... Please wait.")
                        time.sleep(2)  # Poll every 2 seconds
                        retry_count += 1
                else:
                    st.error(f"Error checking status: {response.text}")
                    st.session_state.waiting_for_response = False
                    st.session_state.task_id = None
                    break
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
                st.session_state.waiting_for_response = False
                st.session_state.task_id = None
                break
        
        # If maximum retries reached
        if retry_count >= max_retries:
            st.error("Request timed out. The server is taking too long to respond.")
            st.session_state.waiting_for_response = False
            st.session_state.task_id = None

# Display conversation history
st.markdown("<h2 class='sub-title'>Conversation</h2>", unsafe_allow_html=True)

if not st.session_state.conversation:
    st.info("Start by submitting a legal question or uploading a document.")
else:
    for i, message in enumerate(st.session_state.conversation):
        if message["role"] == "user":
            st.markdown(f"<div style='background-color: #E1F5FE; padding: 10px; border-radius: 10px; margin-bottom: 10px;'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color: #F5F5F5; padding: 10px; border-radius: 10px; margin-bottom: 10px;'><strong>Legal AI:</strong> {message['content']}</div>", unsafe_allow_html=True)
            
            if "references" in message and message["references"]:
                with st.expander("References and Sources"):
                    for ref in message["references"]:
                        st.markdown(f"<div class='reference-item'>📄 {ref}</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>© 2025 Legal AI Assistant</div>", unsafe_allow_html=True)
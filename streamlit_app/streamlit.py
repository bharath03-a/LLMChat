import streamlit as st
import requests
import json
import time
from PIL import Image
import io
import base64

st.set_page_config(
    page_title="Legal AI Assistant",
    page_icon="⚖️",
    layout="wide"
)

API_BASE_URL = "http://localhost:8000"
TEXT_QUERY_ENDPOINT = f"{API_BASE_URL}/query/text"
IMAGE_QUERY_ENDPOINT = f"{API_BASE_URL}/query/image"
PDF_QUERY_ENDPOINT = f"{API_BASE_URL}/query/pdf"
STATUS_ENDPOINT = f"{API_BASE_URL}/query/status"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "waiting_for_response" not in st.session_state:
    st.session_state.waiting_for_response = False
if "task_id" not in st.session_state:
    st.session_state.task_id = None

st.markdown("""
    <style>
    .user-message {
        background-color: rgba(100, 149, 237, 0.2);  /* Cornflower blue with transparency */
        border-left: 3px solid #6495ED;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .assistant-message {
        background-color: rgba(144, 238, 144, 0.2);  /* Light green with transparency */
        border-left: 3px solid #90EE90;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .reference-box {
        background-color: rgba(255, 165, 0, 0.1);  /* Orange with transparency */
        border-left: 3px solid #FFA500;
        padding: 10px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def check_api_health():
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code == 200:
            health_data = response.json()
            return health_data.get("status") == "ok" and health_data.get("assistant_ready")
        return False
    except:
        return False

def submit_text_query(query):
    payload = {
        "query": query,
        "conversation_history": st.session_state.conversation_history
    }
    
    response = requests.post(TEXT_QUERY_ENDPOINT, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

def submit_file_query(file_data, file_type, query_text=None):
    files = {"file": file_data}
    data = {}
    
    if query_text:
        data["query"] = query_text
    
    if st.session_state.conversation_history:
        data["conversation_history"] = json.dumps(st.session_state.conversation_history)
    
    endpoint = IMAGE_QUERY_ENDPOINT if file_type == "image" else PDF_QUERY_ENDPOINT
    
    response = requests.post(
        endpoint,
        files={"image" if file_type == "image" else "pdf": file_data},
        data=data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

def check_query_status(task_id):
    response = requests.get(f"{STATUS_ENDPOINT}/{task_id}")
    if response.status_code == 200:
        task_info = response.json()
        return task_info
    else:
        st.error(f"Error checking status: {response.status_code} - {response.text}")
        return None

def get_message_info(message):
    if "type" in message:
        if message.get("type") == "human":
            return {"role": "user", "content": message.get("content", "")}
        elif message.get("type") in ["ai", "assistant"]:
            return {"role": "assistant", "content": message.get("content", ""), "references": message.get("references", [])}
    elif "role" in message:
        return message
    elif "content" in message:
        if message.get("additional_kwargs", {}).get("references"):
            return {
                "role": "assistant",
                "content": message.get("content", ""),
                "references": message.get("additional_kwargs", {}).get("references", [])
            }
        else:
            return {"role": "user", "content": message.get("content", "")}
    
    return {"role": "user", "content": str(message)}

def display_conversation():
    if not st.session_state.conversation_history:
        st.info("No conversation history yet. Ask a question to get started!")
        return

    for message in st.session_state.conversation_history:
        message_info = get_message_info(message)
        
        if message_info["role"] == "user":
            st.markdown(f"<div class='user-message'><b>You:</b> {message_info['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-message'><b>Legal Assistant:</b> {message_info['content']}</div>", unsafe_allow_html=True)
            
            if "references" in message_info and message_info["references"]:
                with st.expander("References"):
                    for i, ref in enumerate(message_info["references"]):
                        st.markdown(f"<div class='reference-box'><b>Reference {i+1}:</b> {ref}</div>", unsafe_allow_html=True)

def normalize_conversation_history(api_history):
    normalized_history = []
    for message in api_history:
        normalized_history.append(get_message_info(message))
    return normalized_history

def main():
    st.title("⚖️ Legal AI Assistant")
    
    api_healthy = check_api_health()
    if not api_healthy:
        st.error("❌ API is not available. Please check if the server is running.")
        if st.button("Retry Connection"):
            st.rerun()
        return
    
    st.success("✅ Connected to Legal AI Assistant API")
    
    tab1, tab2, tab3 = st.tabs(["Text Query", "Image Upload", "PDF Upload"])
    
    with tab1:
        text_query = st.text_area("Enter your legal question:", height=100)
        submit_text = st.button("Submit Question", key="submit_text")
        
        if submit_text and text_query:
            st.session_state.waiting_for_response = True
            
            st.session_state.conversation_history.append({
                "role": "user",
                "content": text_query
            })
            
            result = submit_text_query(text_query)
            if result:
                st.session_state.task_id = result.get("task_id")
                st.rerun()
    
    with tab2:
        uploaded_image = st.file_uploader("Upload an image of a legal document:", type=["jpg", "jpeg", "png"])
        image_query = st.text_area("Optional: Add a specific question about this document:", height=100, key="image_query")
        
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            
        submit_image = st.button("Submit Image", key="submit_image")
        
        if submit_image and uploaded_image:
            st.session_state.waiting_for_response = True
            
            content = "Uploaded an image"
            if image_query:
                content += f": {image_query}"
                
            st.session_state.conversation_history.append({
                "role": "user",
                "content": content
            })
            
            file_bytes = uploaded_image.getvalue()
            result = submit_file_query(
                (uploaded_image.name, file_bytes, f"image/{uploaded_image.type.split('/')[1]}"), 
                "image", 
                image_query
            )
            
            if result:
                st.session_state.task_id = result.get("task_id")
                st.rerun()
    
    with tab3:
        uploaded_pdf = st.file_uploader("Upload a legal PDF document:", type=["pdf"])
        pdf_query = st.text_area("Optional: Add a specific question about this document:", height=100, key="pdf_query")
        
        if uploaded_pdf:
            st.info(f"PDF Uploaded: {uploaded_pdf.name}")
            
        submit_pdf = st.button("Submit PDF", key="submit_pdf")
        
        if submit_pdf and uploaded_pdf:
            st.session_state.waiting_for_response = True
            
            content = f"Uploaded PDF: {uploaded_pdf.name}"
            if pdf_query:
                content += f": {pdf_query}"
                
            st.session_state.conversation_history.append({
                "role": "user",
                "content": content
            })
            
            file_bytes = uploaded_pdf.getvalue()
            result = submit_file_query(
                (uploaded_pdf.name, file_bytes, "application/pdf"), 
                "pdf", 
                pdf_query
            )
            
            if result:
                st.session_state.task_id = result.get("task_id")
                st.rerun()
    
    if st.session_state.waiting_for_response and st.session_state.task_id:
        with st.spinner("Processing your request..."):
            while True:
                task_info = check_query_status(st.session_state.task_id)
                
                if task_info and task_info.get("status") in ["completed", "error"]:
                    break
                    
                time.sleep(1)
            
            if task_info.get("status") == "completed" and task_info.get("response"):
                response_data = task_info.get("response", {})
                
                assistant_message = {
                    "role": "assistant",
                    "content": response_data.get("final_response", "No response received")
                }

                if "references" in response_data:
                    assistant_message["references"] = response_data.get("references", [])
                    
                st.session_state.conversation_history.append(assistant_message)
                
                if "conversation_history" in response_data:
                    api_history = response_data.get("conversation_history", [])
                    if api_history:
                        st.session_state.conversation_history = normalize_conversation_history(api_history)
                        
            elif task_info.get("status") == "error":
                error_msg = task_info.get("response", {}).get("error", "Unknown error occurred")
                st.error(f"Error: {error_msg}")
                
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": f"Sorry, an error occurred: {error_msg}"
                })
                
            st.session_state.waiting_for_response = False
            st.session_state.task_id = None
            st.rerun()

    st.divider()
    st.header("Conversation")
    display_conversation()
    
    if st.session_state.conversation_history:
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.rerun()

if __name__ == "__main__":
    main()
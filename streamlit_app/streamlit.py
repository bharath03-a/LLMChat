import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image
import io
import base64

# Set page configuration
st.set_page_config(
    page_title="Legal AI Assistant",
    page_icon="⚖️",
    layout="wide"
)

# API endpoints
API_BASE_URL = "http://localhost:8000"
TEXT_QUERY_ENDPOINT = f"{API_BASE_URL}/query/text"
IMAGE_QUERY_ENDPOINT = f"{API_BASE_URL}/query/image"
PDF_QUERY_ENDPOINT = f"{API_BASE_URL}/query/pdf"
STATUS_ENDPOINT = f"{API_BASE_URL}/query/status"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# CourtListener API class
class CourtListenerAPI:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        
    def make_request(self, endpoint, params=None):
        """Make an authenticated request to the CourtListener API"""
        headers = {
            "Authorization": f"Token {self.api_token}"
        }
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None
        
    def get_count(self, endpoint, params=None):
        """Get the count of items that match the given parameters"""
        if params is None:
            params = {}
        
        params["count"] = "on"
        result = self.make_request(endpoint, params)
        
        if result:
            return result.get("count", 0)
        return 0
        
    def get_recent_items(self, endpoint, days=30, order_by="-date_filed", limit=5, fields=None):
        """Get recent items from the specified endpoint"""
        params = {"order_by": order_by}
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            if "filed" in order_by:
                params["date_filed__gte"] = cutoff_date
            else:
                params["date_created__gte"] = cutoff_date
                
        if fields:
            params["fields"] = ",".join(fields)
            
        result = self.make_request(endpoint, params)
        
        if result and "results" in result:
            return result["results"][:limit]
        return []

    def get_high_profile_cases(self, days=365, limit=5):
        """Get recent high-profile cases without using citations API"""
        fields = ["case_name", "date_filed", "docket_id", "absolute_url", "id", "panel", "court"]
        
        # Get recent Supreme Court cases since they're typically high profile
        return self.get_recent_items(
            "clusters/", 
            days=days,
            order_by="-date_filed", 
            limit=limit,
            fields=fields
        )

# Cache functions for metrics
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_court_metrics(api_token):
    """Get metrics about courts and opinions"""
    api = CourtListenerAPI(api_token)
    
    metrics = {
        "total_opinions": api.get_count("opinions/"),
        "scotus_opinions": api.get_count("opinions/", {"cluster__docket__court": "scotus"}),
        "federal_opinions": api.get_count("opinions/", {"court__jurisdiction": "F"}),
        "state_opinions": api.get_count("opinions/", {"court__jurisdiction": "S"}),
    }
    
    # Get recent opinion count (30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    metrics["recent_opinions"] = api.get_count("opinions/", {"date_filed__gte": thirty_days_ago})
    
    return metrics

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_jurisdictions_breakdown(api_token):
    """Get a breakdown of opinions by jurisdiction"""
    api = CourtListenerAPI(api_token)
    
    jurisdictions = {
        "Federal": api.get_count("opinions/", {"court__jurisdiction": "F"}),
        "State": api.get_count("opinions/", {"court__jurisdiction": "S"}),
        "Federal Appellate": api.get_count("opinions/", {"court__jurisdiction": "FA"}),
        "Federal District": api.get_count("opinions/", {"court__jurisdiction": "FD"}),
        "Federal Special": api.get_count("opinions/", {"court__jurisdiction": "FS"}),
        "Federal Bankruptcy": api.get_count("opinions/", {"court__jurisdiction": "FB"}),
    }
    
    return jurisdictions

# Set up session state variables
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "waiting_for_response" not in st.session_state:
    st.session_state.waiting_for_response = False
if "task_id" not in st.session_state:
    st.session_state.task_id = None
if "courtlistener_api_token" not in st.session_state:
    st.session_state.courtlistener_api_token = "a33595ef07cfa9ea05bfa7009cb79cc0daee6261"

# Custom styling
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
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
    .nav-container {
        display: flex;
        justify-content: space-around;
        background-color: #f0f2f6;
        padding: 10px 0;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .nav-item {
        padding: 10px 20px;
        text-align: center;
        cursor: pointer;
        border-radius: 5px;
    }
    .nav-item:hover {
        background-color: #e0e2e6;
    }
    .selected {
        background-color: #1E90FF;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
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

# Page functions
def home_page():
    """Display the Home page with legal metrics"""
    st.title("📊 Legal Data Metrics")
    
    # Get metrics
    with st.spinner("Loading legal data metrics..."):
        metrics = get_court_metrics(st.session_state.courtlistener_api_token)
    
    # Display metrics in an attractive grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;">
        <h3>📜 Total Legal Opinions</h3>
        <h2>{:,}</h2>
        <p>Comprehensive legal database</p>
        </div>
        """.format(metrics["total_opinions"]), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;">
        <h3>⚖️ Supreme Court Cases</h3>
        <h2>{:,}</h2>
        <p>Historical SCOTUS collection</p>
        </div>
        """.format(metrics["scotus_opinions"]), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;">
        <h3>📅 Recent Filings (30 days)</h3>
        <h2>{:,}</h2>
        <p>Fresh legal content</p>
        </div>
        """.format(metrics["recent_opinions"]), unsafe_allow_html=True)
    
    # Second row of metrics
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     st.subheader("Court Jurisdiction Breakdown")
    #     jurisdictions = get_jurisdictions_breakdown(st.session_state.courtlistener_api_token)
    #     chart_data = pd.DataFrame({
    #         "Jurisdiction": list(jurisdictions.keys()),
    #         "Number of Opinions": list(jurisdictions.values())
    #     })
    #     st.bar_chart(chart_data.set_index("Jurisdiction"))
    
    # with col2:
    #     st.subheader("Recent High-Profile Cases")
    #     api = CourtListenerAPI(st.session_state.courtlistener_api_token)
    #     cases = api.get_high_profile_cases()
        
    #     if cases:
    #         cases_data = []
    #         for case in cases:
    #             court_name = case.get('court', {}).get('short_name', 'Unknown Court')
    #             cases_data.append({
    #                 "Case Name": case.get("case_name", "Unknown"),
    #                 "Filed Date": case.get("date_filed", "Unknown").split("T")[0],
    #                 "Court": court_name
    #             })
            
    #         if cases_data:
    #             df = pd.DataFrame(cases_data)
    #             st.dataframe(df, use_container_width=True)

def text_query_page():
    """Text-based query page for AI legal assistant"""
    st.title("Text Query")
    
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

def image_query_page():
    """Image-based query page for AI legal assistant"""
    st.title("Image Upload")
    
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

def pdf_query_page():
    """PDF-based query page for AI legal assistant"""
    st.title("PDF Upload")
    
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

def main():
    st.title("⚖️ Legal AI Assistant")
    
    # Initialize page selection if not already in session state
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    
    # Create navigation with st.columns
    col1, col2, col3, col4 = st.columns(4)
    
    if col1.button("🏠 Home", use_container_width=True):
        st.session_state.page = "Home"
    
    if col2.button("📝 Text Query", use_container_width=True):
        st.session_state.page = "Text Query"
    
    if col3.button("🖼️ Image", use_container_width=True):
        st.session_state.page = "Image"
    
    if col4.button("📄 PDF", use_container_width=True):
        st.session_state.page = "PDF"
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # API health check (only needed for query pages)
    api_healthy = True
    if st.session_state.page in ["Text Query", "Image", "PDF"]:
        api_healthy = check_api_health()
        if not api_healthy:
            st.error("❌ API is not available. Please check if the server is running.")
            if st.button("Retry Connection"):
                st.rerun()
            return
        else:
            st.success("✅ Connected to Legal AI Assistant API")
    
    # Show selected page
    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Text Query":
        text_query_page()
    elif st.session_state.page == "Image":
        image_query_page()
    elif st.session_state.page == "PDF":
        pdf_query_page()
    
    # Process any pending responses
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
    
    # Show conversation history if not on home page
    if st.session_state.page != "Home":
        st.divider()
        st.header("Conversation")
        display_conversation()
        
        if st.session_state.conversation_history:
            if st.button("Clear Conversation"):
                st.session_state.conversation_history = []
                st.rerun()

if __name__ == "__main__":
    main()
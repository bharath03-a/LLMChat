import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_high_profile_cases(api_token, limit=5):
    """Get recent high-profile cases"""
    api = CourtListenerAPI(api_token)
    
    # Get some recent Supreme Court cases
    fields = ["case_name", "date_filed", "absolute_url", "id"]
    cases = api.get_recent_items(
        "clusters/", 
        days=365, 
        order_by="-date_filed", 
        limit=limit,
        fields=fields
    )
    
    return cases

def add_legal_metrics_section():
    """Add a section to display legal metrics from the CourtListener API"""
    st.header("📊 Legal Data Metrics")
    
    # Store API token in session state if not already there
    if "courtlistener_api_token" not in st.session_state:
        st.session_state.courtlistener_api_token = "a33595ef07cfa9ea05bfa7009cb79cc0daee6261"
    
    # Get metrics
    with st.spinner("Loading legal data metrics..."):
        metrics = get_court_metrics(st.session_state.courtlistener_api_token)
    
    # Display metrics in an attractive grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-container">
        <h3>📜 Total Legal Opinions</h3>
        <h2>{:,}</h2>
        <p>Comprehensive legal database</p>
        </div>
        """.format(metrics["total_opinions"]), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-container">
        <h3>⚖️ Supreme Court Cases</h3>
        <h2>{:,}</h2>
        <p>Historical SCOTUS collection</p>
        </div>
        """.format(metrics["scotus_opinions"]), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-container">
        <h3>📅 Recent Filings (30 days)</h3>
        <h2>{:,}</h2>
        <p>Fresh legal content</p>
        </div>
        """.format(metrics["recent_opinions"]), unsafe_allow_html=True)
    
    # # Second row of metrics
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
    #     cases = get_high_profile_cases(st.session_state.courtlistener_api_token)
        
    #     if cases:
    #         cases_data = []
    #         for case in cases:
    #             cases_data.append({
    #                 "Case Name": case.get("case_name", "Unknown"),
    #                 "Filed Date": case.get("date_filed", "Unknown").split("T")[0]
    #             })
            
    #         if cases_data:
    #             df = pd.DataFrame(cases_data)
    #             st.dataframe(df, use_container_width=True)
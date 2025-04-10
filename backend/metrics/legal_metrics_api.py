import os
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import aiohttp

load_dotenv()

class LegalMetricsResponse(BaseModel):
    total_opinions: int
    scotus_opinions: int
    federal_opinions: int
    state_opinions: int
    recent_opinions: int

class HighProfileCase(BaseModel):
    case_name: str
    date_filed: str
    absolute_url: Optional[str] = None
    id: str

class CourtListenerAPIHandler:
    """Helper class to interact with CourtListener API"""
    
    def __init__(self, api_token=None):

        self.api_token = api_token or os.getenv("COURTLISTENER_API_TOKEN")
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
    
    async def make_request(self, endpoint, params=None):
        """Make an authenticated request to the CourtListener API"""
        headers = {
            "Authorization": f"Token {self.api_token}"
        }
        
        url = f"{self.base_url}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            print(f"CourtListener API Error: {str(e)}")
            return None
    
    async def get_count(self, endpoint, params=None):
        """Get the count of items that match the given parameters"""
        if params is None:
            params = {}
        
        params["count"] = "on"
        result = await self.make_request(endpoint, params)
        
        if result:
            return result.get("count", 0)
        return 0
    
    async def get_recent_items(self, endpoint, days=30, order_by="-date_filed", limit=5, fields=None):
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
            
        result = await self.make_request(endpoint, params)
        
        if result and "results" in result:
            return result["results"][:limit]
        return []

legal_metrics_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 3600 
}

jurisdictions_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 3600  
}

high_profile_cases_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 3600 
}

async def get_cached_data(cache_obj, fetch_func, *args, **kwargs):
    """Get data from cache or fetch it if expired"""
    current_time = time.time()
    
    if cache_obj["data"] is None or current_time - cache_obj["timestamp"] > cache_obj["ttl"]:
        data = await fetch_func(*args, **kwargs)
        cache_obj["data"] = data
        cache_obj["timestamp"] = current_time
        return data
    
    return cache_obj["data"]

async def fetch_court_metrics():
    """Fetch court metrics from CourtListener API"""
    api = CourtListenerAPIHandler()
    
    metrics = {
        "total_opinions": await api.get_count("opinions/"),
        "scotus_opinions": await api.get_count("opinions/", {"cluster__docket__court": "scotus"}),
        "federal_opinions": await api.get_count("opinions/", {"court__jurisdiction": "F"}),
        "state_opinions": await api.get_count("opinions/", {"court__jurisdiction": "S"}),
    }

    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    metrics["recent_opinions"] = await api.get_count("opinions/", {"date_filed__gte": thirty_days_ago})
    
    return metrics

async def fetch_jurisdictions_breakdown():
    """Fetch jurisdictions breakdown from CourtListener API"""
    api = CourtListenerAPIHandler()
    
    jurisdictions = {
        "Federal": await api.get_count("opinions/", {"court__jurisdiction": "F"}),
        "State": await api.get_count("opinions/", {"court__jurisdiction": "S"}),
        "Federal_Appellate": await api.get_count("opinions/", {"court__jurisdiction": "FA"}),
        "Federal_District": await api.get_count("opinions/", {"court__jurisdiction": "FD"}),
        "Federal_Special": await api.get_count("opinions/", {"court__jurisdiction": "FS"}),
        "Federal_Bankruptcy": await api.get_count("opinions/", {"court__jurisdiction": "FB"}),
    }
    
    return jurisdictions

async def fetch_high_profile_cases(limit=5):
    """Fetch high-profile cases from CourtListener API"""
    api = CourtListenerAPIHandler()
    
    # Get some recent Supreme Court cases
    fields = ["case_name", "date_filed", "absolute_url", "id"]
    cases = await api.get_recent_items(
        "clusters/", 
        days=365, 
        order_by="-date_filed", 
        limit=limit,
        fields=fields
    )
    
    return cases

def register_legal_metrics_endpoints(app):
    """Register legal metrics endpoints with the FastAPI app"""
    
    @app.get("/api/legal_metrics", response_model=LegalMetricsResponse)
    async def get_legal_metrics():
        """Get legal metrics for the dashboard"""
        metrics = await get_cached_data(legal_metrics_cache, fetch_court_metrics)
        return metrics

    @app.get("/api/jurisdictions", response_model=Dict[str, int])
    async def get_jurisdictions():
        """Get jurisdictions breakdown"""
        jurisdictions = await get_cached_data(jurisdictions_cache, fetch_jurisdictions_breakdown)
        return jurisdictions

    @app.get("/api/high_profile_cases", response_model=List[Dict[str, Any]])
    async def get_high_profile_cases(limit: int = 5):
        """Get high-profile cases"""
        high_profile_cases_cache["ttl"] = 3600
        cases = await get_cached_data(high_profile_cases_cache, fetch_high_profile_cases, limit)
        return cases
from typing import TypedDict, List, Dict, Any, Optional, Union
from langchain_core.messages import AIMessage, HumanMessage

class EnhancedAgentState(TypedDict):
    """Enhanced state management for the Legal AI Assistant"""
    input: Any
    input_type: str
    processed_input: Optional[Dict[str, Any]]
    query_details: Optional[Dict[str, Any]]
    document_search_results: Optional[List[Dict[str, Any]]]
    document_search_sufficient: Optional[bool]
    web_search_results: Optional[List[Dict[str, Any]]]
    web_search_sufficient: Optional[bool]
    need_additional_search: Optional[bool]
    final_response: Optional[str]
    references: Optional[List[str]]
    conversation_history: List[Union[HumanMessage, AIMessage]]

def determine_search_sufficiency(state: EnhancedAgentState, search_type: str, threshold: float = 7.0) -> Dict[str, Any]:
    """Determine if search results are sufficient based on relevance score"""
    if search_type == "document":
        evaluation = state.get("document_search_evaluation", {})
        relevance_score = evaluation.get("Relevance Score", 0)
        sufficient = relevance_score >= threshold
        
        return {
            "document_search_sufficient": sufficient,
            "need_additional_search": not sufficient
        }
    elif search_type == "web":
        evaluation = state.get("web_search_evaluation", {})
        relevance_score = evaluation.get("Relevance Score", 0)
        sufficient = relevance_score >= threshold
        
        return {
            "web_search_sufficient": sufficient,
            "need_additional_search": state.get("need_additional_search", True) and not sufficient
        }
    else:
        raise ValueError(f"Unsupported search type: {search_type}")
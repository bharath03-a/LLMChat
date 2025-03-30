from typing import TypedDict, List, Dict, Any, Optional, Union
from langchain_core.messages import AIMessage, HumanMessage

class EnhancedAgentState(TypedDict):
    """Enhanced state management for the Legal AI Assistant"""
    input: Any  # Raw input (text, image, PDF)
    input_type: str  # Type of input (text, image, PDF)
    processed_input: Optional[Dict[str, Any]]  # Processed input data
    query_details: Optional[Dict[str, Any]]  # Decomposed query
    document_search_results: Optional[List[Dict[str, Any]]]  # Results from document search
    document_search_sufficient: Optional[bool]  # Whether document search results are sufficient
    web_search_results: Optional[List[Dict[str, Any]]]  # Results from web search
    web_search_sufficient: Optional[bool]  # Whether web search results are sufficient
    need_additional_search: Optional[bool]  # Whether additional search is needed
    final_response: Optional[str]  # Final response content
    references: Optional[List[str]]  # References
    conversation_history: List[Union[HumanMessage, AIMessage]]  # Conversation history

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
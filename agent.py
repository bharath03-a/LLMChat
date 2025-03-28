import os
import sys
import warnings
from dotenv import load_dotenv
import asyncio

# Importing necessary libraries
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from tavily import TavilyClient
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

import networkx as nx
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

class AgentState(TypedDict):
    """
    State management for the Legal AI Assistant
    """
    input: str
    query_details: Optional[dict] = None  # Changed from query_understanding
    document_search_results: Optional[List[dict]] = None
    web_search_results: Optional[List[dict]] = None
    final_response: Optional[str] = None
    references: Optional[List[str]] = None

class LegalAIAssistant:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatGroq(
            model="llama3-70b-8192",  # Updated model name
            temperature=0.6,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Initialize Tavily Client for web search
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Query Understanding Prompt
        self.query_understanding_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at understanding and decomposing legal queries."),
            ("human", """Decompose the following query into its key components:
            - Core Legal Issue
            - Jurisdiction
            - Specific Legal Domains
            - Potential Subqueries
            
            Return a structured JSON with these details.
            
            Query: {input}""")
        ])
        
        # Document Search Prompt
        self.document_search_prompt = ChatPromptTemplate.from_messages([
            ("system", "Evaluate the relevance and comprehensiveness of search results for a legal query."),
            ("human", """Assess these document search results:
            Query Details: {query_details}
            Search Results: {document_search_results}
            
            Provide a JSON response indicating:
            - Relevance Score (0-10)
            - Key Matching Sections
            - Additional Information Needed""")
        ])
        
        # Web Search Prompt
        self.web_search_prompt = ChatPromptTemplate.from_messages([
            ("system", "Evaluate web search results for legal information."),
            ("human", """Assess these web search results:
            Query Details: {query_details}
            Web Search Results: {web_search_results}
            
            Provide a JSON response indicating:
            - Relevance Score (0-10)
            - Key Insights
            - Credibility of Sources""")
        ])
        
        # Final Response Generation Prompt
        self.final_response_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a comprehensive legal AI assistant generating precise, well-referenced responses."),
            ("human", """Generate a comprehensive legal response based on:
            Query Details: {query_details}
            Document Search: {document_search_results}
            Web Search: {web_search_results}
            
            Provide:
            - Detailed Legal Explanation
            - Procedural Guidance
            - Relevant Legal References
            - Potential Next Steps""")
        ])

    def understand_query_node(self, state: AgentState):
        """Node for understanding the query"""
        chain = self.query_understanding_prompt | self.llm | JsonOutputParser()
        query_details = chain.invoke({"input": state['input']})
        return {"query_details": query_details}

    def document_search_node(self, state: AgentState):
        """Node for searching legal documents"""
        # Placeholder: Replace with actual document search logic (e.g., Weaviate)
        document_search_results = [
            {"source": "IPC", "section": "Section 141", "content": "Unlawful Assembly Details"},
            {"source": "CrPC", "section": "Section 144", "content": "Procedure for Noise Complaints"}
        ]
        
        chain = self.document_search_prompt | self.llm | JsonOutputParser()
        document_evaluation = chain.invoke({
            "query_details": state['query_details'],
            "document_search_results": document_search_results
        })
        
        return {
            "document_search_results": document_search_results,
            "document_search_evaluation": document_evaluation
        }

    def web_search_node(self, state: AgentState):
        """Node for web searching"""
        web_search_results = self.tavily_client.search(
            query=state['input'], 
            max_results=5
        )
        
        chain = self.web_search_prompt | self.llm | JsonOutputParser()
        web_search_evaluation = chain.invoke({
            "query_details": state['query_details'],
            "web_search_results": web_search_results['results']
        })
        
        return {
            "web_search_results": web_search_results['results'],
            "web_search_evaluation": web_search_evaluation
        }

    def generate_final_response_node(self, state: AgentState):
        """Node for generating final comprehensive response"""
        chain = self.final_response_prompt | self.llm
        final_response = chain.invoke(state)
        
        return {
            "final_response": final_response.content,
            "references": [
                result['url'] for result in state.get('web_search_results', [])
            ]
        }
    
    def visualize_workflow(self):
        """Visualize the LangGraph workflow"""
        # Recreate the workflow for visualization
        workflow = StateGraph(AgentState)
        
        # Add nodes with labels
        workflow.add_node("Query Understanding", self.understand_query_node)
        workflow.add_node("Document Search", self.document_search_node)
        workflow.add_node("Web Search", self.web_search_node)
        workflow.add_node("Generate Response", self.generate_final_response_node)
        
        # Create a NetworkX graph
        nx_graph = nx.DiGraph()
        
        # Add nodes
        nx_graph.add_nodes_from([
            "Query Understanding", 
            "Document Search", 
            "Web Search", 
            "Generate Response"
        ])
        
        # Add edges
        nx_graph.add_edges_from([
            ("Query Understanding", "Document Search"),
            ("Document Search", "Web Search"),
            ("Web Search", "Generate Response")
        ])
        
        # Visualization
        plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(nx_graph, seed=42)
        nx.draw(nx_graph, pos, 
                with_labels=True, 
                node_color='skyblue', 
                node_size=3000, 
                font_size=10, 
                font_weight='bold', 
                arrows=True, 
                edge_color='gray')
        
        plt.title("Legal AI Assistant Workflow")
        plt.tight_layout()
        plt.show()

    def build_workflow(self):
        """Construct the agentic workflow using LangGraph"""
        workflow = StateGraph(AgentState)
        
        # Changed node names to be unique
        workflow.add_node("node_query_understanding", self.understand_query_node)
        workflow.add_node("node_document_search", self.document_search_node)
        workflow.add_node("node_web_search", self.web_search_node)
        workflow.add_node("node_generate_response", self.generate_final_response_node)
        
        # Define workflow edges
        workflow.set_entry_point("node_query_understanding")
        workflow.add_edge("node_query_understanding", "node_document_search")
        workflow.add_edge("node_document_search", "node_web_search")
        workflow.add_edge("node_web_search", "node_generate_response")
        workflow.set_finish_point("node_generate_response")
        
        return workflow.compile()

    async def process_query(self, query: str):
        """Async method to process user query"""
        workflow = self.build_workflow()
        initial_state = {"input": query}
        
        result = await workflow.ainvoke(initial_state)
        return result

# Example usage
async def main():
    assistant = LegalAIAssistant()
    
    # Visualize the workflow
    assistant.visualize_workflow()
    
    # Process a query
    result = await assistant.process_query("How do I deal with a noise complaint against my neighbor?")
    print("Final Response:", result['final_response'])
    print("\nReferences:", result['references'])

if __name__ == "__main__":
    asyncio.run(main())

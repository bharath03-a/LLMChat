import os
import sys
import time
import warnings
from dotenv import load_dotenv
import asyncio
from typing import Dict, Any, List, Optional, Union
from PIL import Image

# Importing necessary libraries
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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

# Import our custom modules
from document_processing import DocumentProcessor
from multimodal_handler import MultimodalInputHandler
from enhanced_agent_state import EnhancedAgentState, determine_search_sufficiency

class LegalAIAssistant:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama3-70b-8192",
            temperature=0.6,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
        self.document_processor = DocumentProcessor(documents_dir="../streamlit_app/notes/")
        self.vector_store = self.document_processor.create_vector_store()

        self.input_handler = MultimodalInputHandler()
        
        self.query_understanding_system = """You are an expert legal AI assistant specializing in understanding complex legal queries.
        Your task is to analyze the user's input and break it down into components that will guide a comprehensive legal search and response.
        Pay special attention to:
        1. Identifying the core legal issue or question
        2. Determining relevant jurisdictions
        3. Identifying specific legal domains (criminal, civil, corporate, etc.)
        4. Extracting potential subqueries that need separate investigation
        5. Identifying any time-sensitive elements
        
        Format your analysis as a structured JSON object.
        """
        
        self.document_evaluation_system = """You are an expert legal document analyst.
        Your task is to evaluate search results from a legal document database and determine if they adequately address the user's query.
        Consider:
        1. Relevance of the documents to the specific legal question
        2. Comprehensiveness of the information provided
        3. Accuracy and authority of the sources
        4. Whether the information is complete or requires additional context
        
        Assign a relevance score (0-10) and explain your reasoning.
        """
        
        self.web_evaluation_system = """You are an expert legal research analyst.
        Your task is to evaluate web search results and determine if they adequately address aspects of the user's legal query.
        Consider:
        1. Credibility of the sources (government sites, law firms, legal journals)
        2. Relevance to the specific legal question
        3. Currency of the information (especially important for evolving legal topics)
        4. Whether the results complement the document search results
        
        Assign a relevance score (0-10) and explain your reasoning.
        """
        
        self.final_response_system = """You are a comprehensive legal AI assistant tasked with providing accurate, nuanced, and helpful legal information.
        When generating your response:
        1. Focus on factual legal information and procedural guidance
        2. Clearly distinguish between established law, legal interpretation, and practical advice
        3. Include relevant citations and references to legal statutes, cases, or authorities
        4. Provide balanced perspectives where legal interpretations differ
        5. Clarify any jurisdictional limitations to your advice
        6. Include appropriate disclaimers about not providing legal advice
        
        Structure your response in a clear, logical format with headings where appropriate.
        """
        
        # Initialize prompts
        self._initialize_prompts()
    
    def _initialize_prompts(self):
        """Initialize all prompts used by the assistant"""
        # Query Understanding Prompt
        self.query_understanding_prompt = ChatPromptTemplate.from_messages([
            ("system", self.query_understanding_system),
            ("human", """Analyze the following legal query and break it down into its key components:

            {processed_input}

            Return a structured JSON with these fields:
            - core_legal_issue: The main legal question or problem
            - jurisdiction: Relevant legal jurisdiction(s) if specified or can be inferred
            - legal_domains: List of relevant legal areas (e.g., criminal, civil, property)
            - subqueries: List of related questions that might need separate investigation
            - time_sensitivity: Any urgent aspects of the query
            - key_terms: Important legal terms mentioned or implied in the query
             
            1. **First, output JSON only** without any inline comments.
            2. **After the JSON, provide explanations** in natural language.
            """)
        ])
        
        # Document Search Evaluation Prompt
        self.document_evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", self.document_evaluation_system),
            ("human", """Evaluate these document search results for the legal query:

            Query Details: {query_details}

            Document Search Results:
            {document_search_results}

            Provide a JSON response with these fields:
            - Relevance Score: (0-10)
            - Key Matching Sections: List of sections most relevant to the query
            - Information Gaps: Legal aspects of the query not covered by these documents
            - Confidence Assessment: Your confidence in the documents answering the query correctly
            """)
        ])
        
        # Web Search Evaluation Prompt
        self.web_evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", self.web_evaluation_system),
            ("human", """Evaluate these web search results for the legal query:

            Query Details: {query_details}

            Web Search Results:
            {web_search_results}

            Provide a JSON response with these fields:
            - Relevance Score: (0-10)
            - Key Insights: Main legal information found in the results
            - Source Credibility: Assessment of the credibility of the sources
            - Information Gaps: Aspects of the query not adequately addressed
            - Comparison to Document Results: How these results complement the document search
            """)
        ])
        
        # Final Response Generation Prompt
        self.final_response_prompt = ChatPromptTemplate.from_messages([
            ("system", self.final_response_system),
            ("human", """Generate a comprehensive legal response based on the following:

            Original Query: {processed_input}
            Query Analysis: {query_details}
            Document Search Results: {document_search_results}
            Web Search Results: {web_search_results}

            Your response should include:
            1. A clear explanation of the legal concepts and principles
            2. Applicable laws, regulations, or precedents
            3. Practical guidance on how to proceed
            4. Any necessary disclaimers about jurisdictional limitations
            5. References to sources used

            Remember to remain balanced, factual, and helpful while acknowledging legal complexities.
            """)
        ])
    
    def process_input_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Process the input based on its type"""
        if state.get('text_query') and state['input_type'] in ["image", "pdf"]:
            processed_input = self.input_handler.process_input(
                state['input'], 
                state['input_type'],
                text_query=state.get('text_query')
            )
        else:
            processed_input = self.input_handler.process_input(
                state['input'], 
                state['input_type']
            )

        if 'conversation_history' not in state:
            state['conversation_history'] = []
        
        return {"processed_input": processed_input}
    
    def understand_query_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for understanding the query"""
        chain = self.query_understanding_prompt | self.llm | JsonOutputParser()

        human_message = HumanMessage(
            content=state['processed_input']['content'],
            additional_kwargs={"timestamp": time.time()}
        )
        state['conversation_history'].append(human_message)
        max_history_size = 10 
        if len(state['conversation_history']) > max_history_size:
            state['conversation_history'] = state['conversation_history'][-max_history_size:]

        recent_context = state['conversation_history'][-3:]

        context_enhanced_query = state['processed_input']['content']
        query_details = chain.invoke({"processed_input": context_enhanced_query})
        
        return {
            "query_details": query_details,
            "conversation_history": state['conversation_history']
        }

    def document_search_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for searching legal documents"""
        key_terms = state['query_details'].get('key_terms', [])
        core_issue = state['query_details'].get('core_legal_issue', '')
        
        search_query = f"{core_issue} {' '.join(key_terms)}"

        search_results = self.vector_store.similarity_search_with_score(
            query=search_query,
            k=5,
        )

        document_search_results = [
            {
                "source": result[0].metadata.get('source', 'Unknown'),
                "page": result[0].metadata.get('page', 0),
                "relevance_score": result[1],
                "content": result[0].page_content
            }
            for result in search_results
        ]

        chain = self.document_evaluation_prompt | self.llm | JsonOutputParser()
        document_evaluation = chain.invoke({
            "query_details": state['query_details'],
            "document_search_results": document_search_results
        })
        
        return {
            "document_search_results": document_search_results,
            "document_search_evaluation": document_evaluation
        }

    def evaluate_doc_search_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for evaluating document search results and deciding next steps"""
        return determine_search_sufficiency(state, "document")

    def web_search_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for web searching"""
        core_issue = state['query_details'].get('core_legal_issue', '')
        jurisdiction = state['query_details'].get('jurisdiction', '')
        
        web_query = f"{core_issue} legal {jurisdiction}"
        
        web_search_results = self.tavily_client.search(
            query=web_query, 
            max_results=5,
            search_depth="advanced"
        )
        
        chain = self.web_evaluation_prompt | self.llm | JsonOutputParser()
        web_search_evaluation = chain.invoke({
            "query_details": state['query_details'],
            "web_search_results": web_search_results['results']
        })
        
        return {
            "web_search_results": web_search_results['results'],
            "web_search_evaluation": web_search_evaluation
        }

    def evaluate_web_search_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for evaluating web search results and deciding next steps"""
        return determine_search_sufficiency(state, "web")

    def generate_final_response_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for generating final comprehensive response"""
        recent_conversation = state['conversation_history'][-5:]

        chain = self.final_response_prompt | self.llm
        final_response = chain.invoke({
            "processed_input": state['processed_input']['content'],
            "query_details": state['query_details'],
            "document_search_results": state['document_search_results'],
            "web_search_results": state['web_search_results'],
            "recent_conversation": recent_conversation
        })

        ai_message = AIMessage(
            content=final_response.content,
            additional_kwargs={"timestamp": time.time()}
        )
        state['conversation_history'].append(ai_message)
        
        references = []
        
        for doc in state.get('document_search_results', []):
            source = doc.get('source', '')
            page = doc.get('page', '')
            if source and source not in references:
                references.append(f"{source} (Page {page})")
        
        for result in state.get('web_search_results', []):
            url = result.get('url', '')
            if url and url not in references:
                references.append(url)
        
        return {
            "final_response": final_response.content,
            "references": references,
            "conversation_history": state['conversation_history']
        }
    
    def additional_search_node(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """Node for performing additional searches when needed"""

        doc_eval = state.get('document_search_evaluation', {})
        web_eval = state.get('web_search_evaluation', {})
        
        info_gaps_doc = doc_eval.get('Information Gaps', [])
        info_gaps_web = web_eval.get('Information Gaps', [])
        

        all_gaps = info_gaps_doc + info_gaps_web
        
        additional_results = []
        for gap in all_gaps:
            if isinstance(gap, str) and gap.strip():
                try:
                    gap_results = self.tavily_client.search(
                        query=f"{gap} legal information {state['query_details'].get('jurisdiction', '')}",
                        max_results=2,
                        search_depth="advanced"
                    )
                    additional_results.extend(gap_results['results'])
                except Exception as e:
                    print(f"Error in additional search: {e}")
        
        current_web_results = state.get('web_search_results', [])
        combined_results = current_web_results + additional_results

        seen_urls = set()
        unique_results = []
        for result in combined_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return {
            "web_search_results": unique_results[:8],
            "need_additional_search": False 
        }
    
    def should_perform_additional_search(self, state: EnhancedAgentState) -> str:
        """Decision node to determine if additional search is needed"""
        if state.get("need_additional_search", False):
            return "additional_search"
        return "generate_response"
    
    def build_workflow(self):
        """Construct the agentic workflow using LangGraph with decision points"""
        workflow = StateGraph(EnhancedAgentState)
        
        # Add all nodes
        workflow.add_node("process_input", self.process_input_node)
        workflow.add_node("understand_query", self.understand_query_node)
        workflow.add_node("document_search", self.document_search_node)
        workflow.add_node("evaluate_doc_search", self.evaluate_doc_search_node)
        workflow.add_node("web_search", self.web_search_node)
        workflow.add_node("evaluate_web_search", self.evaluate_web_search_node)
        workflow.add_node("additional_search", self.additional_search_node)
        workflow.add_node("generate_response", self.generate_final_response_node)
        
        # Define workflow edges with decision points
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "understand_query")
        workflow.add_edge("understand_query", "document_search")
        workflow.add_edge("document_search", "evaluate_doc_search")
        
        # Decision after document search
        workflow.add_conditional_edges(
            "evaluate_doc_search",
            self.should_perform_additional_search,
            {
                "additional_search": "additional_search",
                "generate_response": "web_search"
            }
        )
        
        workflow.add_edge("web_search", "evaluate_web_search")
        
        # Decision after web search
        workflow.add_conditional_edges(
            "evaluate_web_search",
            self.should_perform_additional_search,
            {
                "additional_search": "additional_search",
                "generate_response": "generate_response"
            }
        )
        
        workflow.add_edge("additional_search", "generate_response")
        workflow.set_finish_point("generate_response")
        
        return workflow.compile()
    
    def visualize_workflow(self, graph: StateGraph):
        """Visualize the LangGraph workflow with decision points and save it to a file."""
        
        try:
            img = Image(graph.get_graph().draw_mermaid_png())
            with open("mermaid_graph.png", "wb") as f:
                f.write(img.data)
            print("Image saved as mermaid_graph.png")
        except Exception as e:
            print("Error:", e)

    async def process_query(self, query: Any, input_type: str = "text", text_query: str = "", conversation_history=None):
        """Async method to process user query with any input type"""
        workflow = self.build_workflow()
        initial_state = {
            "input": query,
            "input_type": input_type,
            "text_query": text_query, 
            "conversation_history": conversation_history or []
        }
        
        result = await workflow.ainvoke(initial_state)
        return result
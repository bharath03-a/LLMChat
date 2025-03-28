import os
import sys
import logging
import asyncio
from typing import TypedDict, List, Optional, Union, Dict, Any
from dotenv import load_dotenv

# Multimodal and file handling
import base64
import magic  # for MIME type detection
import pypdf  # for PDF parsing
from PIL import Image
import pytesseract  # for OCR

# Import libraries
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document

# Vector DB and Search
import weaviate
from tavily import TavilyClient

# Workflow
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_ai_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AgentState(TypedDict):
    """
    Enhanced state management for Legal AI Assistant
    """
    input: str
    input_type: str  # text, image, pdf, etc.
    query_details: Optional[dict] = None
    document_search_results: Optional[List[dict]] = None
    vector_search_results: Optional[List[Document]] = None
    web_search_results: Optional[List[dict]] = None
    extracted_text: Optional[str] = None
    final_response: Optional[str] = None
    references: Optional[List[str]] = None
    error: Optional[str] = None

class LegalAIAssistant:
    def __init__(self):
        # Initialize components with error handling
        try:
            # LLM Initialization
            self.llm = ChatGroq(
                model="llama3-70b-8192",
                temperature=0.6,
                api_key=os.getenv("GROQ_API_KEY")
            )

            # Tavily Web Search
            self.tavily_client = TavilyClient(
                api_key=os.getenv("TAVILY_API_KEY")
            )

            # Weaviate Vector Database
            self.weaviate_client = weaviate.Client(
                url=os.getenv("WEAVIATE_URL"),
                auth_client_secret=weaviate.AuthApiKey(
                    api_key=os.getenv("WEAVIATE_API_KEY")
                )
            )

            # Logging initialization
            logger.info("Legal AI Assistant initialized successfully")

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise

        # Prompts (similar to previous implementation)
        self.query_understanding_prompt = ChatPromptTemplate.from_messages([
            ("system", "Expert legal query decomposition assistant."),
            ("human", """Decompose this legal query:
            - Core Legal Issue
            - Jurisdiction
            - Legal Domains
            
            Query: {input}""")
        ])

    def extract_text_from_input(self, input_data: Union[str, bytes], input_type: str) -> str:
        """
        Extract text from different input types
        """
        try:
            if input_type == 'text':
                return input_data
            
            elif input_type == 'image':
                # Convert base64 to image and use OCR
                image = Image.open(base64.b64decode(input_data))
                return pytesseract.image_to_string(image)
            
            elif input_type == 'pdf':
                # PDF text extraction
                pdf_reader = pypdf.PdfReader(base64.b64decode(input_data))
                return "\n".join([page.extract_text() for page in pdf_reader.pages])
            
            else:
                logger.warning(f"Unsupported input type: {input_type}")
                return ""
        
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return ""

    def vector_search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Perform vector search in Weaviate
        """
        try:
            results = (
                self.weaviate_client.query
                .get("LegalDocument", ["text", "source", "section"])
                .with_hybrid(query, alpha=0.75)
                .with_limit(top_k)
                .do()
            )
            
            # Transform results to Document format
            vector_docs = [
                Document(
                    page_content=doc['text'],
                    metadata={
                        'source': doc.get('source', 'Unknown'),
                        'section': doc.get('section', 'Unspecified')
                    }
                ) for doc in results.get('data', {}).get('Get', {}).get('LegalDocument', [])
            ]
            
            return vector_docs
        
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    def understand_query_node(self, state: AgentState):
        """Enhanced query understanding with error handling"""
        try:
            # Preprocess input based on type
            if state['input_type'] != 'text':
                state['extracted_text'] = self.extract_text_from_input(
                    state['input'], 
                    state['input_type']
                )
            
            # Query understanding
            chain = self.query_understanding_prompt | self.llm | JsonOutputParser()
            query_details = chain.invoke({
                "input": state.get('extracted_text', state['input'])
            })
            
            return {"query_details": query_details}
        
        except Exception as e:
            logger.error(f"Query understanding error: {e}")
            return {"error": str(e)}

    def vector_search_node(self, state: AgentState):
        """Enhanced vector search with sophisticated retrieval"""
        try:
            # Perform vector search using query details
            query = state['query_details'].get('core_legal_issue', state['input'])
            vector_results = self.vector_search(query)
            
            return {
                "vector_search_results": vector_results
            }
        
        except Exception as e:
            logger.error(f"Vector search node error: {e}")
            return {"error": str(e)}

    def web_search_node(self, state: AgentState):
        """Enhanced web search with context-aware retrieval"""
        try:
            # Use query details for more precise web search
            query = state['query_details'].get('core_legal_issue', state['input'])
            
            web_search_results = self.tavily_client.search(
                query=query, 
                max_results=5,
                include_domains=['legal.com', 'gov.in', 'barandbench.com']  # Domain filtering
            )
            
            return {
                "web_search_results": web_search_results['results']
            }
        
        except Exception as e:
            logger.error(f"Web search node error: {e}")
            return {"error": str(e)}

    def generate_response_node(self, state: AgentState):
        """Comprehensive response generation"""
        try:
            # Combine vector search and web search results
            final_context = "\n\n".join([
                doc.page_content for doc in state.get('vector_search_results', [])
            ] + [
                result['content'] for result in state.get('web_search_results', [])
            ])
            
            # Generate response
            response_prompt = ChatPromptTemplate.from_messages([
                ("system", "Comprehensive legal response generator"),
                ("human", f"""Generate a detailed legal response:
                Query: {state['input']}
                Query Details: {state['query_details']}
                Context: {final_context}
                
                Provide a thorough, referenced response.""")
            ])
            
            response_chain = response_prompt | self.llm
            final_response = response_chain.invoke(state)
            
            return {
                "final_response": final_response.content,
                "references": [
                    result.get('url', '') for result in state.get('web_search_results', [])
                ]
            }
        
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {"error": str(e)}

    def build_workflow(self):
        """Construct robust agentic workflow"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("node_query_understanding", self.understand_query_node)
        workflow.add_node("node_vector_search", self.vector_search_node)
        workflow.add_node("node_web_search", self.web_search_node)
        workflow.add_node("node_generate_response", self.generate_response_node)
        
        # Workflow edges with error handling
        workflow.set_entry_point("node_query_understanding")
        workflow.add_edge("node_query_understanding", "node_vector_search")
        workflow.add_edge("node_vector_search", "node_web_search")
        workflow.add_edge("node_web_search", "node_generate_response")
        workflow.set_finish_point("node_generate_response")
        
        return workflow.compile()

    async def process_query(self, query: str, input_type: str = 'text'):
        """Async query processing with comprehensive error handling"""
        try:
            workflow = self.build_workflow()
            initial_state = {
                "input": query,
                "input_type": input_type
            }
            
            result = await workflow.ainvoke(initial_state)
            
            if result.get('error'):
                logger.error(f"Workflow processing error: {result['error']}")
                return {"error": result['error']}
            
            return result
        
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return {"error": str(e)}

# Helper function to upload documents to Weaviate
def upload_legal_documents_to_weaviate(client, documents):
    """
    Upload legal documents to Weaviate vector database
    
    :param client: Weaviate client
    :param documents: List of dictionaries with 'text', 'source', 'section'
    """
    try:
        # Batch import documents
        with client.batch as batch:
            for doc in documents:
                batch.add_data_object(
                    data_object={
                        "text": doc['text'],
                        "source": doc.get('source', 'Unknown'),
                        "section": doc.get('section', 'Unspecified')
                    },
                    class_name="LegalDocument"
                )
        logger.info(f"Uploaded {len(documents)} legal documents")
    except Exception as e:
        logger.error(f"Document upload error: {e}")

# Main execution
async def main():
    # Initialize assistant
    assistant = LegalAIAssistant()
    
    # Example query processing
    result = await assistant.process_query(
        "What are the legal remedies for noise pollution in residential areas?",
        input_type='text'
    )
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    else:
        print("Final Response:", result.get('final_response', 'No response generated'))
        print("\nReferences:", result.get('references', []))

if __name__ == "__main__":
    asyncio.run(main())
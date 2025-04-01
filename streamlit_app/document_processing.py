import os
import dotenv
from typing import List, Any

import weaviate
from weaviate.classes.init import Auth

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

dotenv.load_dotenv()

class DocumentProcessor:
    """Process legal documents and create vector store"""
    
    def __init__(self, documents_dir: str = "./notes"):
        self.documents_dir = documents_dir
        self.weaviate_url = os.environ.get("WEAVIATE_URL")
        self.weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
    def load_documents(self) -> List[Any]:
        """Load documents from the directory"""
        try:
            loader = DirectoryLoader(
                self.documents_dir,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            documents = loader.load()
            print(f"Loaded {len(documents)} documents.")
            return documents
        except Exception as e:
            print(f"Error loading documents: {e}")
            return []
    
    def process_documents(self) -> List[Any]:
        """Split documents into chunks"""
        documents = self.load_documents()
        chunks = self.text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks
    
    def create_vector_store(self) -> WeaviateVectorStore:
        """Create and populate vector store with documents using LangChain's WeaviateVectorStore"""
        
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.weaviate_url,
            auth_credentials=Auth.api_key(self.weaviate_api_key),
        )
        
        chunks = self.process_documents()
        
        if client.collections.exists("LegalDocuments"):
            client.collections.delete("LegalDocuments")
        
        vector_store = WeaviateVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            client=client,
            index_name="LegalDocuments", 
            text_key="content",
            by_text=False
        )
        
        print(f"Successfully imported {len(chunks)} chunks into Weaviate")
        return vector_store
    
    def query_store(self, query: str, vector_store: WeaviateVectorStore, k: int = 5):
        """Query the vector store for similar documents"""
        docs = vector_store.similarity_search(query, k=k)
        return docs
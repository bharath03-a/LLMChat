import os
import dotenv
from typing import List, Any

import weaviate
from weaviate.classes.init import Auth
import weaviate.classes.config as wvc
from weaviate.classes.config import Configure

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
    
    def create_vector_store(self, weaviate_url: str) -> WeaviateVectorStore:
        """Create and populate vector store with latest Weaviate API v4"""
        
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(self.weaviate_api_key),
        )
        
        # Check if collection exists and create if not
        if not client.collections.exists("LegalDocument"):
            client.collections.create(
                "LegalDocument",
                vectorizer_config=[
                    Configure.NamedVectors.text2vec_weaviate(
                        name="content_vector",
                        source_properties=["content"],
                        model="Snowflake/snowflake-arctic-embed-l-v2.0",
                    )
                ],
                properties=[
                    wvc.Property(name="content", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="source", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="page", data_type=wvc.DataType.INT),
                    wvc.Property(name="metadata", data_type=wvc.DataType.TEXT)
                ]
            )
        
        chunks = self.process_documents()
        collection = client.collections.get("LegalDocument")
        
        # Batch import the document chunks
        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                batch.add_object(
                    properties={
                        "content": chunk.page_content,
                        "source": chunk.metadata.get("source", ""),
                        "page": chunk.metadata.get("page", 0),
                        "metadata": str(chunk.metadata)
                    }
                )
                if batch.number_errors > 10:
                    print("Batch import stopped due to excessive errors.")
                    break
        
        failed_objects = collection.batch.failed_objects
        if failed_objects:
            print(f"Number of failed imports: {len(failed_objects)}")
            print(f"First failed object: {failed_objects[0]}")
        
        # Create and return the LangChain vector store
        vector_store = WeaviateVectorStore(
            client=client,
            index_name="LegalDocument",
            text_key="content",
            embedding=self.embeddings
        )
        
        return vector_store
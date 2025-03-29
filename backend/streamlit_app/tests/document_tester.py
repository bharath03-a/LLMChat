# test_document_processing.py
from ..document_processing import DocumentProcessor
import os


# Test with a sample PDF
sample_pdf_path = "/Users/bharathvelamala/Documents/LLM/LLMChat/backend/streamlit_app/notes/Thinking_Like_a_Lawyer.pdf"
if os.path.exists(sample_pdf_path):
    processor = DocumentProcessor(documents_dir="/Users/bharathvelamala/Documents/LLM/LLMChat/backend/streamlit_app/notes/")
    # Test vector storage
    processor.create_vector_store(weaviate_url=os.environ.get("WEAVIATE_URL"))
    print("Vectors stored successfully")
import os
from typing import Dict, Any, Optional, List, Union
import tempfile
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from io import BytesIO

class MultimodalInputHandler:
    """Handle different types of inputs (text, image, file)"""
    
    def __init__(self):
        # Configure pytesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'<path_to_tesseract_executable>'
        pass
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """Process plain text input"""
        return {
            "type": "text",
            "content": text,
            "metadata": {}
        }
    
    def process_image(self, image_data: Union[str, bytes, Image.Image], text_query: Optional[str] = "") -> Dict[str, Any]:
        """Process image input using OCR"""
        if isinstance(image_data, str):
            image = Image.open(image_data)
        elif isinstance(image_data, bytes):
            image = Image.open(BytesIO(image_data))
        else:
            image = image_data
            
        extracted_text = pytesseract.image_to_string(image)
        content = extracted_text
        if text_query:
            content = f"Image content: {extracted_text}\n\nUser query: {text_query}"
        
        return {
            "type": "image",
            "content": content,
            "metadata": {
                "original_format": "image",
                "image_size": image.size,
                "extracted_text": extracted_text,
                "user_query": text_query,
                "image_mode": image.mode
            }
        }
    
    def process_pdf(self, pdf_data: Union[str, bytes], text_query: Optional[str] = "") -> Dict[str, Any]:
        """Process PDF input"""
        if isinstance(pdf_data, bytes):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_data)
                temp_file_path = temp_file.name
                
            try:
                loader = PyPDFLoader(temp_file_path)
                documents = loader.load()

                full_text = "\n".join(doc.page_content for doc in documents)
                content = full_text
                if text_query:
                    content = f"PDF content: {full_text}\n\nUser query: {text_query}"
                
                return {
                    "type": "pdf",
                    "content": content,
                    "metadata": {
                        "original_format": "pdf",
                        "page_count": len(documents),
                        "documents": documents,
                        "extracted_text": full_text,
                        "user_query": text_query
                    }
                }
            finally:
                os.unlink(temp_file_path)
        else:
            loader = PyPDFLoader(pdf_data)
            documents = loader.load()
            
            full_text = "\n".join(doc.page_content for doc in documents)

            content = full_text
            if text_query:
                content = f"PDF content: {full_text}\n\nUser query: {text_query}"
            
            return {
                "type": "pdf",
                "content": content,
                "metadata": {
                    "original_format": "pdf",
                    "page_count": len(documents),
                    "documents": documents,
                    "extracted_text": full_text,
                    "user_query": text_query
                }
            }
    
    def process_input(self, input_data: Any, input_type: str, text_query: Optional[str] = "") -> Dict[str, Any]:
        """Process any input based on its type"""
        if input_type == "text":
            return self.process_text(input_data)
        elif input_type == "image":
            return self.process_image(input_data, text_query)
        elif input_type == "pdf":
            return self.process_pdf(input_data, text_query)
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
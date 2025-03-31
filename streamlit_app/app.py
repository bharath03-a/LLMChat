import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import base64
from io import BytesIO
from PIL import Image
import time

load_dotenv()

# Import our Legal AI Assistant
from legal_ai_assistant import LegalAIAssistant

# Global variables
legal_assistant = None
active_tasks = {}

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global legal_assistant
    legal_assistant = LegalAIAssistant(os.getenv("WEAVIATE_URL"))
    print("Legal AI Assistant initialized")
    
    # Start task cleanup
    cleanup_task = asyncio.create_task(cleanup_tasks())
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown logic
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Initialize FastAPI with lifespan
app = FastAPI(title="Legal AI Assistant API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextQueryRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, Any]]] = None

class QueryResponse(BaseModel):
    task_id: str
    status: str
    response: Optional[Dict[str, Any]] = None

@app.post("/query/text", response_model=QueryResponse)
async def text_query(background_tasks: BackgroundTasks, request: TextQueryRequest):
    """Process a text-based legal query"""
    if not legal_assistant:
        raise HTTPException(status_code=503, detail="Legal AI Assistant not initialized")
    
    # Generate task ID
    task_id = f"task_{int(time.time())}"
    
    # Store the initial task status
    active_tasks[task_id] = {"status": "processing", "response": None}
    
    # Process the query asynchronously
    background_tasks.add_task(
        process_query_async,
        task_id,
        request.query,
        "text",
        None,
        request.conversation_history
    )
    
    return QueryResponse(task_id=task_id, status="processing")

@app.post("/query/image", response_model=QueryResponse)
async def image_query(
    background_tasks: BackgroundTasks, 
    image: UploadFile = File(...), 
    query: str = Form(None),
    conversation_history: str = Form(None)
):
    """Process an image-based legal query (e.g., a document photo)"""
    if not legal_assistant:
        raise HTTPException(status_code=503, detail="Legal AI Assistant not initialized")
    
    # Read the image file
    contents = await image.read()
    try:
        img = Image.open(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    
    # Generate task ID
    task_id = f"task_{int(time.time())}"
    
    # Store the initial task status
    active_tasks[task_id] = {"status": "processing", "response": None}
    
    # Parse conversation history if provided
    history = None
    if conversation_history:
        try:
            import json
            history = json.loads(conversation_history)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid conversation history format: {str(e)}")
    
    # Process the query asynchronously
    background_tasks.add_task(
        process_query_async,
        task_id,
        img,
        "image",
        query,
        history
    )
    
    return QueryResponse(task_id=task_id, status="processing")

@app.post("/query/pdf", response_model=QueryResponse)
async def pdf_query(
    background_tasks: BackgroundTasks, 
    pdf: UploadFile = File(...), 
    query: str = Form(None),
    conversation_history: str = Form(None)
):
    """Process a PDF-based legal query"""
    if not legal_assistant:
        raise HTTPException(status_code=503, detail="Legal AI Assistant not initialized")
    
    # Read the PDF file
    contents = await pdf.read()
    if not pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")
    
    # Generate task ID
    task_id = f"task_{int(time.time())}"
    
    # Store the initial task status
    active_tasks[task_id] = {"status": "processing", "response": None}
    
    # Parse conversation history if provided
    history = None
    if conversation_history:
        try:
            import json
            history = json.loads(conversation_history)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid conversation history format: {str(e)}")
    
    # Process the query asynchronously
    background_tasks.add_task(
        process_query_async,
        task_id,
        contents,
        "pdf",
        query,
        history
    )
    
    return QueryResponse(task_id=task_id, status="processing")

@app.get("/query/status/{task_id}", response_model=QueryResponse)
async def query_status(task_id: str):
    """Check the status of a processing task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = active_tasks[task_id]
    return QueryResponse(
        task_id=task_id,
        status=task_info["status"],
        response=task_info.get("response")
    )

async def process_query_async(task_id: str, query_data: Any, input_type: str, text_query: str = None, conversation_history: List[Dict[str, Any]] = None):
    """Process a query asynchronously and update the task status"""
    try:
        # If there's both input data and a text query, we need to handle differently
        if text_query and input_type in ["image", "pdf"]:
            # Process the query with combined input
            result = await legal_assistant.process_query(
                query_data, 
                input_type, 
                text_query=text_query,
                conversation_history=conversation_history
            )
        else:
            # Process normally
            result = await legal_assistant.process_query(
                query_data, 
                input_type,
                conversation_history=conversation_history
            )
        
        # Update task status
        active_tasks[task_id] = {
            "status": "completed",
            "response": {
                "final_response": result.get("final_response", ""),
                "references": result.get("references", []),
                "query_details": result.get("query_details", {}),
                "conversation_history": result.get("conversation_history", [])
            }
        }
    except Exception as e:
        # Update task status with error
        active_tasks[task_id] = {
            "status": "error",
            "response": {"error": str(e)}
        }
        print(f"Error processing task {task_id}: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "assistant_ready": legal_assistant is not None}

async def cleanup_tasks():
    """Periodically clean up old tasks"""
    while True:
        await asyncio.sleep(3600)  # Clean up every hour
        current_time = time.time()
        task_ids = list(active_tasks.keys())
        for task_id in task_ids:
            # Extract timestamp from task_id (assuming format task_timestamp)
            try:
                timestamp = int(task_id.split("_")[1])
                if current_time - timestamp > 86400:  # Older than 24 hours
                    del active_tasks[task_id]
            except (IndexError, ValueError):
                pass

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
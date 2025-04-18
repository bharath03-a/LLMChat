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

from metrics.legal_metrics_api import register_legal_metrics_endpoints
from agent.legal_ai_assistant import LegalAIAssistant

legal_assistant = None
active_tasks = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global legal_assistant
    legal_assistant = LegalAIAssistant()
    print("Legal AI Assistant initialized")
    cleanup_task = asyncio.create_task(cleanup_tasks())
    
    yield
    
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Legal AI Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_legal_metrics_endpoints(app)

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
    
    task_id = f"task_{int(time.time())}"

    active_tasks[task_id] = {"status": "processing", "response": None}

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

    contents = await image.read()
    try:
        img = Image.open(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    task_id = f"task_{int(time.time())}"
    
    active_tasks[task_id] = {"status": "processing", "response": None}

    history = None
    if conversation_history:
        try:
            import json
            history = json.loads(conversation_history)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid conversation history format: {str(e)}")
    
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
    
    contents = await pdf.read()
    if not pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")
    
    task_id = f"task_{int(time.time())}"

    active_tasks[task_id] = {"status": "processing", "response": None}

    history = None
    if conversation_history:
        try:
            import json
            history = json.loads(conversation_history)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid conversation history format: {str(e)}")

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
        if text_query and input_type in ["image", "pdf"]:
            result = await legal_assistant.process_query(
                query_data, 
                input_type, 
                text_query=text_query,
                conversation_history=conversation_history
            )
        else:
            result = await legal_assistant.process_query(
                query_data, 
                input_type,
                conversation_history=conversation_history
            )

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
        await asyncio.sleep(3600)
        current_time = time.time()
        task_ids = list(active_tasks.keys())
        for task_id in task_ids:
            try:
                timestamp = int(task_id.split("_")[1])
                if current_time - timestamp > 86400:
                    del active_tasks[task_id]
            except (IndexError, ValueError):
                pass

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
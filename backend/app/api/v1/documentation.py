"""Documentation API endpoints for generating solution documentation."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import traceback
from ...core.orchestrator import AgentOrchestrator
from ...auth.deps import get_current_active_user
from ...db.models import User, Task, Document
from ...db.database import get_db
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# Configure logging
logger = logging.getLogger("api.documentation")

# Create router
router = APIRouter()

# Create orchestrator
orchestrator = AgentOrchestrator()

# SSE client connections
client_connections = {}
completed_documentations = {}
pending_generations = set()

class DocumentationRequest(BaseModel):
    """Model for documentation generation request."""
    task_id: str

@router.post("/generate")
async def generate_documentation(
    request: DocumentationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate documentation for a completed solution.
    
    Args:
        request: Documentation generation request
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Status of the documentation generation request
    """
    task_id = request.task_id
    
    pending_generations.add(task_id)
    return {"status": "Documentation generation pending", "task_id": task_id}


async def process_documentation_request(task_id: str, solution_data: Dict[str, Any], db: Session):
    """Process documentation request in the background.
    
    Args:
        task_id: Unique task identifier
        solution_data: Solution data to generate documentation for
    """
    import json
    logger.info(f"Processing documentation request for task {task_id}")
    client_id = f"{task_id}_doc"
    
    try:        # Define callback for SSE updates
        def update_callback(status: str, progress: Optional[float] = None):
            for queue in client_connections.get(client_id, []):
                update_data = {
                    "status": status,
                    "progress": progress,
                    "content": status  # Include content field for frontend compatibility
                }
                queue.put_nowait({
                    "event": "update",
                    "data": json.dumps(update_data)  # JSON-serialize like we do for complete events
                })
          # Generate documentation
        documentation_result = await orchestrator.generate_documentation(
            task_id=task_id,
            solution_data=solution_data,
            phase_callback=update_callback
        )
        
        # Send completion event with documentation result
        for queue in client_connections.get(client_id, []):
            # Log the structure of documentation_result for debugging
            logger.info(f"Documentation result type: {type(documentation_result)}")
            if isinstance(documentation_result, dict):
                logger.info(f"Documentation result keys: {documentation_result.keys()}")
                
            # Extract the actual documentation content
            doc_content = ""
            if isinstance(documentation_result, dict) and "documentation" in documentation_result:
                doc_content = documentation_result["documentation"]
                logger.info(f"Extracted documentation content (first 100 chars): {doc_content[:100]}...")
            else:
                doc_content = str(documentation_result)
                logger.info(f"Using string representation of documentation (first 100 chars): {doc_content[:100]}...")            # Create the completion event data
            
            complete_event_data = {
                "status": "completed",
                "documentation": doc_content
            }

            new_doc = Document(
                id=str(uuid4()),
                task_id=task_id,
                content=doc_content
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
            
            # Log what we're about to send
            logger.info(f"Sending completion event with data keys: {complete_event_data.keys()}")
            logger.info(f"Document content length: {len(doc_content)}")
            
            # Convert data to JSON string
            json_data = json.dumps(complete_event_data)
            logger.info(f"JSON serialized data length: {len(json_data)}")
            
            # Send the event
            complete_event = {
                "event": "complete",
                "data": json_data
            }
            
            logger.info(f"Sending event: complete to client for task {task_id}")
            queue.put_nowait(complete_event)
            
        logger.info(f"Documentation generation completed for task {task_id}")
        
    except Exception as e:
        logger.error(f"Error in documentation generation process: {str(e)}")
        # Send error event
        for queue in client_connections.get(client_id, []):
            queue.put_nowait({
                "event": "error",
                "data": {
                    "status": "error",
                    "message": str(e)
                }
            })


@router.get("/events/{task_id}")
async def documentation_events(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """SSE endpoint for documentation generation events."""
    client_id = f"{task_id}_doc"
    logger.info(f"New client connected to documentation events for task {task_id}")
    
    # Create queue for this client
    queue = asyncio.Queue()
    
    # Register connection
    if client_id not in client_connections:
        client_connections[client_id] = []
    client_connections[client_id].append(queue)
    
    # Send initial connection event
    import json
    
    connection_event = {
        "event": "connected",
        "data": json.dumps({"status": "connected"})
    }
    
    logger.info(f"Sending event: connected to client for task {task_id}")
    await queue.put(connection_event)
    
    # Check if documentation is already completed for this task
    if task_id in pending_generations:
        pending_generations.remove(task_id)
        # Lấy task từ DB (hoặc truyền từ client nếu cần)
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            # Chạy background task generate
            asyncio.create_task(
                process_documentation_request(
                    task_id=task_id,
                    solution_data={
                        "requirements": task.requirements,
                        "solution": task.solution,
                        "language": task.language,
                        "explanation": task.explanation,
                        "code_files": task.code_files,
                        "detailed_status": task.detailed_status
                    },
                    db=db
                )
            )
    
    # Event generator function
    async def event_generator():        
        try:
            while True:
                # Exit if client disconnects
                if await request.is_disconnected():
                    break
                
                # Get message from queue
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=10.0)
                    # Log when sending a non-ping event
                    if message.get("event") not in ["ping"]:
                        logger.info(f"Sending event: {message.get('event')} to client for task {task_id}")
                    yield message
                except asyncio.TimeoutError:
                    # Send keep-alive event every second
                    yield {
                        "event": "ping",
                        "data": ""
                    }
        except Exception as e:
            logger.error(f"Error in documentation events stream: {str(e)}")
        finally:
            # Clean up when client disconnects
            if client_id in client_connections and queue in client_connections[client_id]:
                client_connections[client_id].remove(queue)
                if not client_connections[client_id]:
                    del client_connections[client_id]
            logger.info(f"Client disconnected from documentation events for task {task_id}")
    
    return EventSourceResponse(event_generator())

@router.get("/history")
async def get_code_history(
    db: Session = Depends(get_db)
):
    """
    Get history of solved tasks (code/documentation).
    Returns a list of tasks that have documentation.
    """
    # Lấy tất cả document, join với Task để lấy thêm thông tin nếu cần
    docs = db.query(Document).all()
    history = []
    for doc in docs:
        # Nếu muốn lấy thêm thông tin task, join hoặc truy vấn thêm
        task = db.query(Task).filter(Task.id == doc.task_id).first()
        history.append({
            "document_id": doc.id,
            "task_id": doc.task_id,
            "content": doc.content,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
        })
    return {"status": "success", "history": history}

@router.get("/{task_id}")
async def get_documentation(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get documentation for a specific task.
    
    Args:
        task_id: The ID of the task to get documentation for
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The documentation content if available
    """
    logger.info(f"Documentation request for task {task_id}")
    
    # Get the task from the database
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Ensure the user owns this task
    if task.user_id != current_user.id:
        logger.error(f"User {current_user.username} does not own task {task_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if documentation exists
    if not hasattr(task, 'documentation') or task.documentation is None:
        logger.info(f"No documentation found for task {task_id}")
        return {"status": "not_found", "message": "No documentation has been generated for this task"}
    
    logger.info(f"Returning documentation for task {task_id}")
    return {
        "status": "success",
        "documentation": task.documentation
    }

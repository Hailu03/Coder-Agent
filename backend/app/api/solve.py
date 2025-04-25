"""API routes for solving coding problems.

This module defines the API routes for submitting and retrieving coding problem solutions.
"""

from fastapi import APIRouter, Body, HTTPException, Request, Response, BackgroundTasks
from fastapi.routing import APIRoute
from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Callable
import logging
import json
import uuid
from datetime import datetime

from ..core.orchestrator import AgentOrchestrator
from ..models.models import TaskStatus

# Configure logging
logger = logging.getLogger("api.solve")

# Custom route class to handle OPTIONS requests properly
class CORSRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Any:
            # Handle OPTIONS requests explicitly
            if request.method == "OPTIONS":
                logger.info(f"Handling OPTIONS request to {request.url.path}")
                return Response(
                    content=json.dumps({}),
                    status_code=200,
                    media_type="application/json",
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    },
                )
            return await original_route_handler(request)

        return custom_route_handler

# Create router with custom route class
router = APIRouter(route_class=CORSRoute)

# In-memory storage for tasks (in a production environment, this would be a database)
tasks = {}

# Request models
class SolveRequest(BaseModel):
    """Model for problem-solving requests."""
    requirements: str
    language: str
    additional_context: Optional[str] = None

# Response models
class TaskResponse(BaseModel):
    """Model for task response."""
    task_id: str
    status: TaskStatus
    created_at: str
    detailed_status: Optional[Dict[str, Any]] = None

class SolutionResponse(BaseModel):
    """Model for solution response."""
    task_id: str
    status: TaskStatus
    solution: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    code_files: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None
    detailed_status: Optional[Dict[str, Any]] = None

@router.post("/", response_model=TaskResponse)
async def solve_problem(request: Request, background_tasks: BackgroundTasks, data: SolveRequest = Body(...)):
    """Submit a problem to be solved.
    
    Args:
        request: The HTTP request
        background_tasks: FastAPI background tasks
        data: The problem details
        
    Returns:
        Task information with a unique ID
    """
    try:
        logger.info(f"Received solve request: {data}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task entry
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "created_at": datetime.now().isoformat(),
            "requirements": data.requirements,
            "language": data.language,
            "additional_context": data.additional_context,
            "solution": None,
            "explanation": None,
            "code_files": None,
            "error": None,
            "detailed_status": {
                "phase": "planning",
                "progress": 0
            }
        }
        
        # Process in background
        background_tasks.add_task(
            process_solution_task,
            task_id=task_id,
            requirements=data.requirements,
            language=data.language,
            additional_context=data.additional_context
        )
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=tasks[task_id]["created_at"],
            detailed_status=tasks[task_id]["detailed_status"]
        )
    
    except Exception as e:
        logger.error(f"Error processing solve request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )

@router.get("/{task_id}", response_model=SolutionResponse)
async def get_solution(request: Request, task_id: str):
    """Get the solution for a specific task.
    
    Args:
        request: The HTTP request
        task_id: The unique ID of the task
        
    Returns:
        The solution if available
    """
    try:
        if task_id not in tasks:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
        
        task = tasks[task_id]
        
        return SolutionResponse(
            task_id=task_id,
            status=task["status"],
            solution=task.get("solution"),
            explanation=task.get("explanation"),
            code_files=task.get("code_files"),
            error=task.get("error"),
            detailed_status=task.get("detailed_status")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving solution for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve solution: {str(e)}"
        )

@router.get("/task/{task_id}", response_model=SolutionResponse)
async def get_solution_alternative_path(request: Request, task_id: str):
    """Alternative endpoint to get the solution for a specific task.
    This endpoint exists for compatibility with the frontend.
    
    Args:
        request: The HTTP request
        task_id: The unique ID of the task
        
    Returns:
        The solution if available
    """
    return await get_solution(request, task_id)

@router.post("/task/{task_id}/cancel", response_model=Dict[str, str])
async def cancel_task(request: Request, task_id: str):
    """Cancel a running task.
    
    Args:
        request: The HTTP request
        task_id: The unique ID of the task
        
    Returns:
        Status message
    """
    try:
        if task_id not in tasks:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
        
        task = tasks[task_id]
        
        # Only allow cancellation of pending or processing tasks
        if task["status"] in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            task["status"] = TaskStatus.FAILED
            task["error"] = "Task cancelled by user"
            logger.info(f"Task {task_id} cancelled by user")
            return {"message": "Task cancelled successfully"}
        else:
            return {"message": f"Task already in {task['status']} state, cannot cancel"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )

async def process_solution_task(task_id: str, requirements: str, language: str, additional_context: Optional[str] = None):
    """Process a solution task in the background.
    
    Args:
        task_id: The unique ID of the task
        requirements: The problem requirements
        language: The programming language
        additional_context: Additional context for the problem
    """
    try:
        # Update task status
        tasks[task_id]["status"] = TaskStatus.PROCESSING
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        
        # Set up phase listener to update detailed status
        def phase_update_callback(phase: str, progress: Optional[float] = None):
            if task_id in tasks:
                tasks[task_id]["detailed_status"] = {
                    "phase": phase,
                    "progress": progress or 0
                }
                logger.info(f"Task {task_id} phase updated: {phase}")
        
        # Solve the problem
        solution = await orchestrator.solve_problem(
            requirements=requirements,
            language=language,
            additional_context=additional_context,
            phase_callback=phase_update_callback
        )
        
        # Update task with solution
        tasks[task_id].update({
            "status": TaskStatus.COMPLETED,
            "solution": solution.get("solution"),
            "explanation": solution.get("explanation"),
            "code_files": solution.get("code_files"),
            "detailed_status": {"phase": "completed", "progress": 100}
        })
        
        logger.info(f"Task {task_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        # Update task with error
        tasks[task_id].update({
            "status": TaskStatus.FAILED,
            "error": str(e),
            "detailed_status": {"phase": "failed", "progress": 0}
        })
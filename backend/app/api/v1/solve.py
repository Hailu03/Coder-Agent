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

from ...core.orchestrator import AgentOrchestrator
from ...models.models import TaskStatus, SolveRequest, TaskResponse, SolutionResponse

# Configure logging
logger = logging.getLogger("api.solve")

# Create router 
router = APIRouter()

# In-memory storage for tasks (in a production environment, this would be a database)
tasks = {}

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

@router.get("/task/{task_id}", response_model=SolutionResponse)
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
        
        # Get the code and other solution details
        solution_code = solution.get("solution", {}).get("code", "")
        problem_analysis = solution.get("solution", {}).get("problem_analysis", "")
        file_structure = solution.get("solution", {}).get("file_structure", {})
        
        # Create properly formatted solution dictionary for the response
        solution_dict = {
            "code": solution_code,
            "analysis": problem_analysis,
            "language": language,
            "approach": solution.get("solution", {}).get("approach", []),
            "libraries": solution.get("solution", {}).get("libraries", []),
            "best_practices": solution.get("solution", {}).get("best_practices", []),
        }
        
        # Convert file_structure dictionary to a list of file dictionaries
        code_files_list = []
        if isinstance(file_structure, dict):
            # Handle files from file_structure
            if "files" in file_structure and isinstance(file_structure["files"], list):
                for file_info in file_structure["files"]:
                    if isinstance(file_info, dict):
                        code_files_list.append({
                            "path": file_info.get("path", "main.py"),
                            "content": solution_code,
                            "description": file_info.get("description", ""),
                        })
            
            # If no files specified, create a default one
            if not code_files_list:
                code_files_list.append({
                    "path": f"main.{language}",
                    "content": solution_code,
                    "description": "Main solution file",
                })
        
        # Update task with solution
        tasks[task_id].update({
            "status": TaskStatus.COMPLETED,
            "solution": solution_dict,
            "explanation": problem_analysis,
            "code_files": code_files_list,
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
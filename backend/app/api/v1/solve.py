"""API routes for solving coding problems.

This module defines the API routes for submitting and retrieving coding problem solutions.
"""

from fastapi import APIRouter, Body, HTTPException, Request, Response, BackgroundTasks, Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Callable
import logging
import json
import uuid
import asyncio
import time  # Add this import
from datetime import datetime
from sqlalchemy.orm import Session

from ...core.orchestrator import AgentOrchestrator
from ...models.models import TaskStatus, SolveRequest, TaskResponse, SolutionResponse
from ...auth.deps import get_current_active_user
from ...db.models import User, Task
from ...db.database import get_db
from .events import task_status_update

# Configure logging
logger = logging.getLogger("api.solve")

# Create router 
router = APIRouter()

@router.post("/", response_model=TaskResponse)
async def solve_problem(
    request: Request, 
    background_tasks: BackgroundTasks, 
    data: SolveRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a problem to be solved.
    
    Args:
        request: The HTTP request
        background_tasks: FastAPI background tasks
        data: The problem details
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Task information with a unique ID
    """
    try:
        logger.info(f"Received solve request from user {current_user.username}: {data}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task entry in database
        detailed_status = {"phase": "planning", "progress": 0}
        
        db_task = Task(
            id=task_id,
            user_id=current_user.id,
            status=TaskStatus.PENDING,
            requirements=data.requirements,
            language=data.language,
            additional_context=data.additional_context,
            detailed_status=detailed_status
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
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
            created_at=db_task.created_at.isoformat(),
            detailed_status=detailed_status
        )
    
    except Exception as e:
        logger.error(f"Error processing solve request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )

@router.get("/task/{task_id}", response_model=SolutionResponse)
async def get_solution(
    request: Request, 
    task_id: str, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the solution for a specific task.
    
    Args:
        request: The HTTP request
        task_id: The unique ID of the task
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The solution if available
    """
    try:
        # Query task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
        
        # Verify that the task belongs to the requesting user
        if task.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this task"
            )
        
        return SolutionResponse(
            task_id=task_id,
            status=task.status,
            solution=task.solution,
            explanation=task.explanation,
            code_files=task.code_files,
            error=task.error,
            detailed_status=task.detailed_status
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
async def cancel_task(
    request: Request, 
    task_id: str, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a running task.
    
    Args:
        request: The HTTP request
        task_id: The unique ID of the task
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Status message
    """
    try:
        # Query task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
        
        # Verify that the task belongs to the requesting user
        if task.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to cancel this task"
            )
        
        # Only allow cancellation of pending or processing tasks
        if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            task.status = TaskStatus.FAILED
            task.error = "Task cancelled by user"
            task.detailed_status = {"phase": "cancelled", "progress": 0}
            
            # Save changes to database
            db.commit()
            
            logger.info(f"Task {task_id} cancelled by user {current_user.username}")
            return {"message": "Task cancelled successfully"}
        else:
            return {"message": f"Task already in {task.status} state, cannot cancel"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )

@router.get("/history", response_model=List[dict])
async def get_task_history(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get the task history for the current user.
    
    Args:
        request: The HTTP request
        current_user: The authenticated user
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        
    Returns:
        List of tasks with basic information
    """
    try:
        # Query tasks from database
        tasks = db.query(Task).filter(
            Task.user_id == current_user.id
        ).order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
        
        # Format task data for response
        result = []
        for task in tasks:
            result.append({
                "task_id": task.id,
                "status": task.status,
                "language": task.language,
                "requirements": task.requirements[:100] + "..." if len(task.requirements) > 100 else task.requirements,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed": task.status == TaskStatus.COMPLETED,
                "detailed_status": task.detailed_status
            })
            
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving task history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve task history: {str(e)}"
        )

async def process_solution_task(task_id: str, requirements: str, language: str, additional_context: Optional[str] = None):
    """Process a solution task in the background.
    
    Args:
        task_id: The unique ID of the task
        requirements: The problem requirements
        language: The programming language
        additional_context: Additional context for the problem
    """
    # Create DB session for background task
    from ...db.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found in database")
            return
        
        # Update task status
        task.status = TaskStatus.PROCESSING
        db.commit()
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
          # Set up phase listener to update detailed status and send SSE updates
        def phase_update_callback(phase: str, progress: Optional[float] = None):
            nonlocal task, db
            try:
                # Need to refresh task to prevent stale data issues
                db.refresh(task)
                
                # Create a more detailed status message
                detailed_status = {
                    "phase": phase,
                    "progress": progress or 0
                }
                task.detailed_status = detailed_status
                db.commit()
                
                # Create a sync version of the task_status_update call to ensure it completes
                # before returning from this callback
                loop = asyncio.get_event_loop()
                update_future = asyncio.run_coroutine_threadsafe(
                    task_status_update(
                        task_id=task_id,
                        user_id=task.user_id,
                        status=task.status,
                        detailed_status=detailed_status
                    ),
                    loop
                )
                
                # Add small delay to ensure the update is processed before continuing
                time.sleep(0.05)
                
                logger.info(f"Task {task_id} phase updated: {phase}, progress: {progress}")
            except Exception as e:
                logger.error(f"Error updating task phase: {str(e)}", exc_info=True)
        
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
        file_structure = solution.get("solution", {}).get("file_structure", {})        # Create properly formatted solution dictionary for the response
        solution_dict = {
            "code": solution_code,
            "problem_analysis": problem_analysis,  # Changed key from "analysis" to "problem_analysis" to match frontend
            "language": language,
            "approach": solution.get("solution", {}).get("approach", []),
            "libraries": solution.get("solution", {}).get("libraries", []),
            "best_practices": solution.get("solution", {}).get("best_practices", []),
            "performance_considerations": solution.get("solution", {}).get("performance_considerations", []),
            "file_structure": file_structure,  # Store the full file structure
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
        task.solution = solution_dict
        task.explanation = problem_analysis
        task.code_files = code_files_list
        detailed_status = {"phase": "completed", "progress": 100}
        task.detailed_status = detailed_status
        task.status = TaskStatus.COMPLETED
        
        db.commit()
        
        # Instead of using create_task, directly await the task_status_update call
        # to ensure it's processed before returning
        try:
            await task_status_update(
                task_id=task_id,
                user_id=task.user_id,
                status=TaskStatus.COMPLETED,
                detailed_status=detailed_status
            )
            
            # Small delay to ensure the update is processed
            await asyncio.sleep(0.5)
            
            logger.info(f"Task {task_id} completed successfully and notification sent")
        except Exception as notify_error:
            logger.error(f"Error sending completion notification: {str(notify_error)}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}", exc_info=True)
        try:
            # Update task with error
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                detailed_status = {"phase": "failed", "progress": 0}
                task.detailed_status = detailed_status
                db.commit()
                
                # Directly await the failure notification
                await task_status_update(
                    task_id=task_id,
                    user_id=task.user_id,
                    status=TaskStatus.FAILED,
                    detailed_status=detailed_status
                )
                
                # Small delay to ensure the update is processed
                await asyncio.sleep(0.5)
                
                logger.info(f"Task {task_id} failure notification sent")
        except Exception as db_error:
            logger.error(f"Error updating task failure status: {str(db_error)}", exc_info=True)
    finally:
        db.close()
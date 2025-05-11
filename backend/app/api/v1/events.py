"""API routes for real-time events.

This module defines the API routes for Server-Sent Events (SSE) for real-time updates.
"""

from fastapi import APIRouter, Request, Response, Depends
from sse_starlette.sse import EventSourceResponse
from typing import Dict
import asyncio
import logging
import json
import uuid
from datetime import datetime

from ...auth.deps import get_current_active_user, get_current_user, oauth2_scheme, get_user_from_token_param
from ...db.models import User
from ...db.database import get_db
from ...models.models import TaskStatus

# Configure logging
logger = logging.getLogger("api.events")

# Create router 
router = APIRouter()

# Store active connections by user ID and client ID
ACTIVE_CONNECTIONS: Dict[str, Dict[str, asyncio.Queue]] = {}

async def task_status_update(task_id: str, user_id: int, status: TaskStatus, detailed_status: dict = None):
    """
    Send task status updates to connected clients.
    
    Args:
        task_id: The task ID
        user_id: The user ID
        status: The task status
        detailed_status: Detailed status information
    """
    try:
        user_id_str = str(user_id)
        if user_id_str in ACTIVE_CONNECTIONS:
            # Prepare the message
            message = {
                "task_id": task_id,
                "status": status,
                "detailed_status": detailed_status or {}
            }
            
            # Log more details about the update being sent
            logger.info(f"Sending task update for task {task_id} to user {user_id}, phase: {detailed_status.get('phase') if detailed_status else 'unknown'}")
            
            # Count active connections for this user
            connection_count = len(ACTIVE_CONNECTIONS[user_id_str])
            if connection_count == 0:
                logger.warning(f"No active connections for user {user_id_str}")
                return
                
            # Send to all connections for this user
            for client_id, client_queue in ACTIVE_CONNECTIONS[user_id_str].items():
                try:
                    await client_queue.put(message)
                    logger.debug(f"Task update put in queue for client {client_id}")
                except Exception as client_error:
                    logger.error(f"Error sending to client {client_id}: {str(client_error)}")
            
            logger.info(f"Task update sent for task {task_id} to user {user_id} ({connection_count} connections)")
        else:
            logger.warning(f"No active connections found for user {user_id}")
    except Exception as e:
        logger.error(f"Error in task_status_update: {str(e)}")

@router.get("/task-updates")
async def task_updates(
    request: Request, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint for SSE task updates with token in header.
    
    Args:
        request: The HTTP request
        current_user: The authenticated user from authorization header
        
    Returns:
        EventSourceResponse for SSE events
    """
    user_id = str(current_user.id)
    client_id = str(uuid.uuid4())
    
    # Initialize user's connection dictionary if it doesn't exist
    if user_id not in ACTIVE_CONNECTIONS:
        ACTIVE_CONNECTIONS[user_id] = {}
    
    # Create a queue for this connection
    queue = asyncio.Queue()
    ACTIVE_CONNECTIONS[user_id][client_id] = queue
    
    logger.info(f"New SSE connection established for user {user_id}, client {client_id}")
    
    async def event_generator():
        try:
            # Send initial connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({"message": "Connected to task updates stream"})
            }
            
            # Wait for messages
            while True:
                if await request.is_disconnected():
                    logger.info(f"Client {client_id} disconnected")
                    break
                
                try:
                    # Wait for a message with a timeout
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield {
                        "event": "task_update",
                        "data": json.dumps(message)
                    }
                    logger.debug(f"SSE message sent to client {client_id}")
                except asyncio.TimeoutError:
                    # Send a keepalive message every second
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now().isoformat()})
                    }
                    logger.debug(f"Ping sent to client {client_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream: {str(e)}")
        finally:
            # Clean up connection when done
            if user_id in ACTIVE_CONNECTIONS and client_id in ACTIVE_CONNECTIONS[user_id]:
                del ACTIVE_CONNECTIONS[user_id][client_id]
                if not ACTIVE_CONNECTIONS[user_id]:
                    del ACTIVE_CONNECTIONS[user_id]
                logger.info(f"Removed SSE connection for user {user_id}, client {client_id}")
    
    return EventSourceResponse(event_generator())

@router.get("/task-updates-token")
async def task_updates_with_token(
    request: Request,
    token: str,
    current_user: User = Depends(get_user_from_token_param)
):
    """
    Endpoint for SSE task updates with token in query parameter.
    This is specifically for EventSource connections which can't set Authorization headers.
    
    Args:
        request: The HTTP request
        token: Auth token provided as query parameter
        current_user: The authenticated user from token query param
        
    Returns:
        EventSourceResponse for SSE events
    """
    user_id = str(current_user.id)
    client_id = str(uuid.uuid4())
    
    # Initialize user's connection dictionary if it doesn't exist
    if user_id not in ACTIVE_CONNECTIONS:
        ACTIVE_CONNECTIONS[user_id] = {}
    
    # Create a queue for this connection
    queue = asyncio.Queue()
    ACTIVE_CONNECTIONS[user_id][client_id] = queue
    
    logger.info(f"New SSE connection established for user {user_id}, client {client_id}")
    
    async def event_generator():
        try:
            # Send initial connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({"message": "Connected to task updates stream"})
            }
            
            # Wait for messages
            while True:
                if await request.is_disconnected():
                    logger.info(f"Client {client_id} disconnected")
                    break
                
                try:
                    # Wait for a message with a timeout
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield {
                        "event": "task_update",
                        "data": json.dumps(message)
                    }
                    logger.debug(f"SSE message sent to client {client_id}")
                except asyncio.TimeoutError:
                    # Send a keepalive message every second
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now().isoformat()})
                    }
                    logger.debug(f"Ping sent to client {client_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream: {str(e)}")
        finally:
            # Clean up connection when done
            if user_id in ACTIVE_CONNECTIONS and client_id in ACTIVE_CONNECTIONS[user_id]:
                del ACTIVE_CONNECTIONS[user_id][client_id]
                if not ACTIVE_CONNECTIONS[user_id]:
                    del ACTIVE_CONNECTIONS[user_id]
                logger.info(f"Removed SSE connection for user {user_id}, client {client_id}")
    
    return EventSourceResponse(event_generator())

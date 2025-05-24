"""
API endpoints for chat interaction with the collaborative coding agent system.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...agents.chat_agent import ChatAgent
from ...services.ai_service import get_ai_service
from ...core.config import settings
from ...db.models import Task, Conversation, Message, User
from ...db.database import SessionLocal, get_db
from ...auth.deps import get_current_user

# Configure logging
logger = logging.getLogger("api.chat")

router = APIRouter()

# Initialize chat agent with the configured AI service
chat_agent = ChatAgent(ai_service=get_ai_service())

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    task_id: Optional[str] = None
    conversation_id: Optional[str] = None
    code_context: Optional[str] = None
    language: Optional[str] = None
    error_message: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    code: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    type: str = "text"  # Can be "text", "code", "error", "action"

@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Send a message to the chat agent and get a response.
    
    Args:
        request: The chat request containing the user's message and context
        db: Database session
        current_user: The authenticated user making the request
        
    Returns:
        Response from the chat agent
    """
    logger.info(f"Received chat message from user {current_user.username}: {request.message[:50]}...")
    
    # Prepare task context if task_id is provided
    task = None
    if request.task_id:
        task = db.query(Task).filter(Task.id == request.task_id).first()
    
    # Get or create conversation
    conversation = None
    if request.conversation_id:
        # Use existing conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation if none specified and we have task_id
        if request.task_id:
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                user_id=current_user.id,
                task_id=request.task_id,
                title=f"Task Discussion - {request.task_id[:8]}",
                status="active"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"New conversation created with ID: {conversation_id}")
    
    # Save user message to database
    if conversation:
        user_message_id = str(uuid.uuid4())        
        user_message = Message(
            id=user_message_id,
            conversation_id=conversation.id,
            sender="user",
            content=request.message,
            message_type="text",
            message_metadata={
                "code_context": request.code_context,
                "language": request.language,
                "error_message": request.error_message
            }
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        logger.info(f"User message saved with ID: {user_message_id}")
    
    # Prepare the request for the chat agent
    agent_request = {
        "message": request.message,
        "task": task
    }
    
    # Add optional context if provided
    if request.code_context:
        agent_request["code_context"] = request.code_context
    if request.language:
        agent_request["language"] = request.language
    if request.error_message:
        agent_request["error_message"] = request.error_message
        
    try:
        # Process the message through the chat agent
        agent_response = await chat_agent.process(agent_request)
        
        # Prepare the response based on the agent's response type
        response_type = agent_response.get("type", "text")
        
        response = {
            "message": agent_response.get("message", ""),
            "type": response_type,
            "conversation_id": conversation.id if conversation else None
        }
        
        # Add code if available
        if "code" in agent_response:
            response["code"] = agent_response["code"]
        elif "fixed_code" in agent_response:
            response["code"] = agent_response["fixed_code"]
        elif "improved_code" in agent_response:
            response["code"] = agent_response["improved_code"]
            
        # Add actions if needed
        if response_type == "code_fix" or response_type == "code_improvement" or response_type == "implementation":
            response["actions"] = [
                {
                    "type": "copy_code",
                    "label": "Copy Code"
                },
                {
                    "type": "execute_code",
                    "label": "Execute Code"                }
            ]
            
        # Save agent response to database
        if conversation:
            agent_message_id = str(uuid.uuid4())
            
            # Determine agent type based on response type
            agent_type = "system"
            if response_type in ["code_fix", "code_improvement", "implementation"]:
                agent_type = "developer"
            elif response_type == "general_answer":
                agent_type = "researcher"
                agent_message = Message(
                    id=agent_message_id,
                    conversation_id=conversation.id,
                    sender="agent",
                    agent_type=agent_type,
                    content=agent_response.get("message", ""),
                    message_type="code" if "code" in response else "text",
                    message_metadata=agent_response
                )
            db.add(agent_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# WebSocket connection for real-time chat
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted. Token: {'***' if token else 'None'}")
    
    try:
        logger.info(f"WebSocket connection established with token: {'***' if token else 'None'}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "message": "WebSocket connected successfully",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse the message                
                request_data = json.loads(data)
                message = request_data.get("message", "")
                task_id = request_data.get("task_id")
                conversation_id = request_data.get("conversation_id")
                
                logger.info(f"Received WebSocket message: {message[:50]}... for task_id: {task_id}, conversation_id: {conversation_id}")
                
                # Send immediate acknowledgment
                await websocket.send_json({
                    "type": "acknowledgment", 
                    "message": "Message received, processing...",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Process message directly (not as background task to avoid connection issues)
                await process_ws_message(websocket, data, task_id)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket.send_json({"error": "Invalid JSON format"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({"error": f"Error: {str(e)}"})
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
            pass

async def process_ws_message(websocket: WebSocket, message: str, task_id: Optional[str] = None):
    """Process a message received through WebSocket in the background."""
    db = SessionLocal()
    try:
        # Parse message to get more data if it's a JSON string
        message_data = {}
        user_message_content = message
        conversation_id = None
        code_context = None
        language = None
        
        if isinstance(message, str) and message.strip().startswith('{'):
            try:
                message_data = json.loads(message)
                user_message_content = message_data.get("message", message)
                conversation_id = message_data.get("conversation_id")
                code_context = message_data.get("code_context")
                language = message_data.get("language")
            except:
                logger.warning("Failed to parse message as JSON, treating as plain text")
                
        # Prepare task context if task_id is provided
        task = None
        if task_id:
            # Get task from database
            task = db.query(Task).filter(Task.id == task_id).first()
            logger.info(f"Task retrieved: {task}")
            if not task:
                await websocket.send_json({"error": "Task not found"})
                return
                
        # Get or create conversation if we have conversation_id or task_id
        conversation = None
        if conversation_id:
            # Use existing conversation
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                logger.info(f"Using existing conversation: {conversation_id}")
            else:
                logger.warning(f"Conversation not found: {conversation_id}")
                
        elif task_id:
            # Create new conversation for this task
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                user_id=1,  # Default user ID for WebSocket (should be improved with real authentication)
                task_id=task_id,
                title=f"WebSocket Chat - {task_id[:8]}",
                status="active"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"Created new conversation: {conversation_id}")
            
        # Save user message to database if we have a conversation
        if conversation:
            user_message_id = str(uuid.uuid4())
            user_message = Message(
                id=user_message_id,
                conversation_id=conversation.id,
                sender="user",
                content=user_message_content,
                message_type="text",
                message_metadata={
                    "code_context": code_context,
                    "language": language
                }
            )
            db.add(user_message)
            db.commit()
            logger.info(f"Saved WebSocket user message to database with ID: {user_message_id}")
        
        # Process the message
        agent_request = {"message": user_message_content, "task": task}
        if code_context:
            agent_request["code_context"] = code_context
        if language:
            agent_request["language"] = language
            
        agent_response = await chat_agent.process(agent_request)
        logger.info(f"Agent response type: {agent_response.get('type')}")
          # Prepare comprehensive response
        response_data = {
            "message": agent_response.get("message", ""),
            "type": agent_response.get("type", "text"),
            "timestamp": datetime.now().isoformat()
        }
        # Add code if available (check all possible code fields)
        code = (agent_response.get("code") or 
                agent_response.get("fixed_code") or 
                agent_response.get("improved_code") or "")
        if code:
            response_data["code"] = code
            # Also add the specific field names that frontend expects
            if agent_response.get("improved_code"):
                response_data["improved_code"] = agent_response.get("improved_code")
            if agent_response.get("fixed_code"):
                response_data["fixed_code"] = agent_response.get("fixed_code")
            
        # Add improvements info if available
        if agent_response.get("improvements_made"):
            response_data["improvements_made"] = agent_response.get("improvements_made")
            
        # Add changes info if available  
        if agent_response.get("changes_made"):
            response_data["changes_made"] = agent_response.get("changes_made")
            
        # Add solution update flag
        if agent_response.get("solution_updated"):
            response_data["solution_updated"] = True
            
        # Add all updated fields if available
        for key in ["updated_explanation", "updated_approach", "updated_best_practices", "updated_problem_analysis"]:
            if agent_response.get(key):
                response_data[key] = agent_response.get(key)        # Save agent response to database if we have a conversation
        if conversation:
            agent_message_id = str(uuid.uuid4())
            
            # Determine agent type based on response type
            response_type = agent_response.get("type", "text")
            agent_type = "system"
            if response_type in ["code_fix", "code_improvement", "implementation"]:
                agent_type = "developer"
            elif response_type == "general_answer":
                agent_type = "researcher"
                
            # Create agent message in database
            agent_message = Message(
                id=agent_message_id,
                conversation_id=conversation.id,
                sender="agent",
                agent_type=agent_type,
                content=agent_response.get("message", ""),
                message_type="code" if code else "text",
                message_metadata=agent_response
            )
            db.add(agent_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
            # Add conversation_id to the response
            response_data["conversation_id"] = conversation.id
            
            logger.info(f"Saved WebSocket agent message to database with ID: {agent_message_id}")
        
        # Send the response back to the client
        logger.info(f"Sending WebSocket response: {response_data.get('type')} with code: {bool(code)}")
        await websocket.send_json(response_data)
        logger.info("WebSocket response sent successfully, continuing to listen...")
        
    except Exception as e:
        logger.error(f"Error processing WebSocket message: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({"error": f"Error processing message: {str(e)}"})
        except Exception as send_error:
            logger.error(f"Error sending error response: {send_error}")
    finally:
        db.close()

"""Data models for the Collaborative Coding Agents application.

This module defines the database models and Pydantic models for the application.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum, auto
from datetime import datetime


class TaskStatus(str, Enum):
    """Enum representing the status of a task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(str, Enum):
    """Enum representing the type of message."""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    FILE = "file"


class AgentType(str, Enum):
    """Enum representing the type of agent."""
    PLANNER = "planner"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    TESTER = "tester"
    SYSTEM = "system"


class SettingsUpdateRequest(BaseModel):
    """Model for settings update requests."""
    ai_provider: Optional[str] = None
    api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None

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


# Conversation and Message models
class ConversationCreate(BaseModel):
    """Model for creating a new conversation."""
    task_id: Optional[str] = None
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Model for conversation response."""    
    id: str
    user_id: int
    task_id: Optional[str] = None
    title: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = 0
    last_message: Optional[str] = None


class MessageCreate(BaseModel):
    """Model for creating a new message."""
    conversation_id: str
    sender: str  # 'user' or 'agent'
    agent_type: Optional[AgentType] = None
    content: str
    message_type: MessageType = MessageType.TEXT
    message_metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Model for message response."""
    id: str
    conversation_id: str
    sender: str
    agent_type: Optional[str] = None
    content: str
    message_type: str
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ConversationWithMessages(BaseModel):
    """Model for conversation with messages."""
    id: str
    user_id: int
    task_id: Optional[str] = None
    title: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse]


class AttachmentCreate(BaseModel):
    """Model for creating message attachment."""
    message_id: str
    file_name: str
    file_type: str
    file_size: int


class AttachmentResponse(BaseModel):
    """Model for attachment response."""
    id: str
    message_id: str
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime
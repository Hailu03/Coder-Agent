"""Data models for the Collaborative Coding Agents application.

This module defines the database models and Pydantic models for the application.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum, auto


class TaskStatus(str, Enum):
    """Enum representing the status of a task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SettingsUpdateRequest(BaseModel):
    """Model for settings update requests."""
    ai_provider: Optional[str] = None
    api_key: Optional[str] = None
    serper_api_key: Optional[str] = None

class Agent(BaseModel):
    """Model representing an AI agent."""
    name: str
    description: str


class Task(BaseModel):
    """Model representing a coding task."""
    id: str
    requirements: str
    language: str = "python"
    status: TaskStatus = TaskStatus.PENDING
    

class Solution(BaseModel):
    """Model representing a solution to a coding problem."""
    problem_analysis: str = ""
    approach: List[str] = Field(default_factory=list)
    code: str = ""
    file_structure: Dict[str, Any] = Field(default_factory=dict)
    language: str = "python"
    libraries: List[str] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)
    performance_considerations: List[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Model representing a response from an agent."""
    agent: str
    type: str
    content: Dict[str, Any] = Field(default_factory=dict)

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


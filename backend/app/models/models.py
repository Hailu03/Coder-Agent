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
"""Base Agent module for the Collaborative Coding Agents application.

This module defines the base Agent class that all specialized agents will inherit from.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional

from ..services.ai_service import AIService

# Configure logging
logger = logging.getLogger("agents.base")


class Agent(ABC):
    """Abstract base class for specialized AI agents."""
    
    def __init__(self, name: str, ai_service: AIService):
        """Initialize the agent.
        
        Args:
            name: The name of the agent
            ai_service: AI service for interacting with language models
        """
        self.name = name
        self.ai_service = ai_service
        logger.info(f"Initialized agent: {name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and generate output.
        
        Args:
            input_data: The input data for the agent to process
            
        Returns:
            Processed output data
        """
        pass
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text using the AI service.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated text
        """
        return await self.ai_service.generate_text(prompt)
    
    async def generate_structured_output(self, prompt: str, output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output using the AI service.
        
        Args:
            prompt: The input prompt
            output_schema: The expected output schema
            
        Returns:
            Structured output as a dictionary
        """
        return await self.ai_service.generate_structured_output(prompt, output_schema)
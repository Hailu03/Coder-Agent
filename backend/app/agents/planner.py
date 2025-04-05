"""Planner Agent module for the Collaborative Coding Agents application.

This module defines the Planner Agent that analyzes problems and creates solution plans.
"""

import logging
from typing import Dict, Any, List

from .base import Agent
from ..services.ai_service import AIService
from ..utils import clean_language_name

# Configure logging
logger = logging.getLogger("agents.planner")


class PlannerAgent(Agent):
    """Agent responsible for analyzing problems and creating solution plans."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the Planner Agent.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__(name="PlannerAgent", ai_service=ai_service)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process problem requirements and create a solution plan.
        
        Args:
            input_data: Contains the problem requirements and language preference
            
        Returns:
            Solution plan including problem analysis, approach, and requirements
        """
        requirements = input_data.get("requirements", "")
        language = clean_language_name(input_data.get("language", "python"))
        
        logger.info(f"Planning solution for problem in {language}")
        
        prompt = f"""
        You are an expert software architecture and design specialist. I need you to analyze the following programming problem and create a detailed solution plan.
        
        PROBLEM REQUIREMENTS:
        {requirements}
        
        TARGET LANGUAGE: {language}
        
        Please provide a comprehensive analysis of the problem and a detailed solution plan that includes:
        1. A clear problem statement and understanding of the requirements
        2. Key algorithms, data structures, or design patterns that would be appropriate
        3. High-level approach, breaking down the solution into logical steps
        4. Any potential edge cases or challenges to consider
        5. Required libraries or frameworks that would be helpful
        6. Any performance considerations
        
        Structure your response as a JSON object for easy parsing.
        """
        
        # Output schema for structured response
        output_schema = {
            "problem_analysis": "string",
            "approach": ["string"],
            "recommended_libraries": ["string"],
            "data_structures": ["string"],
            "algorithms": ["string"],
            "design_patterns": ["string"],
            "edge_cases": ["string"],
            "performance_considerations": ["string"]
        }
        
        response = await self.generate_structured_output(prompt, output_schema)
        
        if not response:
            logger.warning("Failed to generate structured plan, falling back to text generation")
            text_response = await self.generate_text(prompt)
            return {
                "problem_analysis": text_response,
                "approach": [],
                "recommended_libraries": [],
                "data_structures": [],
                "algorithms": [],
                "design_patterns": [],
                "edge_cases": [],
                "performance_considerations": []
            }
        
        return response
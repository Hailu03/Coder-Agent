"""Document Generator Agent module for the Collaborative Coding Agents application.

This module defines a specialized AI agent responsible for generating detailed documentation
for coding solutions.
"""

import logging
from typing import Dict, Any, List, Optional

from .base import Agent
from ..services.ai_service import AIService

# Configure logging
logger = logging.getLogger("agents.documenter")


class DocumenterAgent(Agent):
    """Agent specialized in generating comprehensive documentation for code solutions."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the Document Generator Agent.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__("DocumenterAgent", ai_service)
        logger.info("Document Generator Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed documentation for the provided solution.
        
        Args:
            input_data: Dictionary containing:
                - requirements: Original problem requirements
                - planning: Output from the planning phase
                - research: Output from the research phase
                - implementation: Generated code solution
                - testing: Testing results and analysis
                - language: The programming language used
        
        Returns:
            Dictionary containing the generated documentation
        """
        logger.info("Generating comprehensive documentation")
        
        # Extract input data
        requirements = input_data.get("requirements", "")
        planning = input_data.get("planning", {}).get("plan", "")
        research = input_data.get("research", {}).get("research_findings", "")
        implementation = input_data.get("implementation", {}).get("code", "")
        testing = input_data.get("testing", {}).get("test_results", "")
        language = input_data.get("language", "python")
        
        # Construct prompt for the AI service
        prompt = f"""
        As a technical documentation specialist, create comprehensive documentation for the following code solution:
        
        ## REQUIREMENTS:
        {requirements}
        
        ## PLANNING:
        {planning}
        
        ## RESEARCH:
        {research}
        
        ## IMPLEMENTATION:
        ```{language}
        {implementation}
        ```
        
        ## TESTING:
        {testing}
        
        Generate a professional, detailed documentation report in markdown format that includes:
        
        1. Executive Summary - Brief overview of the problem and solution
        2. Problem Statement - Detailed description of the requirements and constraints
        3. Solution Approach - Explanation of the planning and research process
        4. Technical Implementation - Detailed walkthrough of the code with explanations of key components, algorithms, and design patterns used
        5. Testing and Validation - Discussion of testing methodology and results
        6. Future Improvements - Potential enhancements or optimizations
        
        Format the documentation with proper markdown, including headings, code blocks, lists, and emphasis where appropriate.
        **MUST** not cover all document sections in ````markdown ... ``` code blocks.
        Instead, use code blocks only for the code snippets and keep the rest in plain text.
        The tone should be professional and educational, suitable for technical stakeholders.
        
        Ensure that the documentation is clear, concise, and easy to understand for a technical audience.
        """
        
        # Get response from AI service
        response = await self.ai_service.generate_text(
            prompt=prompt,
        )
        if response.startswith("```markdown"):
            response = response.strip()
            response = response[len("```markdown"):-3]

        
        logger.info("Documentation generation completed")
        
        # Return the generated documentation
        return {
            "documentation": response.strip(),
            "format": "markdown"
        }

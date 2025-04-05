"""Agent Orchestrator module for the Collaborative Coding Agents application.

This module defines the orchestration mechanism that coordinates the collaborative 
workflow between different specialized agents.
"""

import logging
import asyncio
import html
from typing import Dict, Any, List, Optional

from ..agents.planner import PlannerAgent
from ..agents.researcher import ResearchAgent
from ..agents.code_generator import CodeGeneratorAgent
from ..services.ai_service import get_ai_service
from ..utils import clean_language_name
from ..models.models import Solution

# Configure logging
logger = logging.getLogger("core.orchestrator")


class AgentOrchestrator:
    """Orchestrator that coordinates the collaborative workflow between agents."""
    
    def __init__(self):
        """Initialize the Agent Orchestrator with specialized agents."""
        # Initialize AI service
        self.ai_service = get_ai_service()
        
        # Initialize specialized agents
        self.planner_agent = PlannerAgent(self.ai_service)
        self.research_agent = ResearchAgent(self.ai_service)
        self.code_generator_agent = CodeGeneratorAgent(self.ai_service)
        
        logger.info("Agent Orchestrator initialized")
    
    async def solve_problem(self, requirements: str, language: str = "python", additional_context: Optional[str] = None) -> Dict[str, Any]:
        """Solve a programming problem through collaborative agent workflow.
        
        Args:
            requirements: The programming problem requirements
            language: The target programming language
            additional_context: Additional context or constraints for the problem
            
        Returns:
            Solution object with code, approach, and analysis
        """
        try:
            # Clean the language name
            clean_lang = clean_language_name(language)
            logger.info(f"Starting problem-solving workflow for language: {clean_lang}")
            
            # Combine requirements with additional context if provided
            full_requirements = requirements
            if additional_context:
                full_requirements = f"{requirements}\n\nAdditional Context:\n{additional_context}"
            
            # Phase 1: Planning
            planning_input = {
                "requirements": full_requirements,
                "language": clean_lang
            }
            
            logger.info("Phase 1: Planning solution approach")
            plan_result = await self.planner_agent.process(planning_input)
            
            # Phase 2: Research
            research_input = {
                "requirements": full_requirements,
                "language": clean_lang,
                "plan": plan_result
            }
            
            logger.info("Phase 2: Researching relevant information")
            research_result = await self.research_agent.process(research_input)
            
            # Phase 3: Code Generation
            code_gen_input = {
                "requirements": full_requirements,
                "language": clean_lang,
                "plan": plan_result,
                "research": research_result
            }
            
            logger.info("Phase 3: Generating code solution")
            code_result = await self.code_generator_agent.process(code_gen_input)
            
            # Unescape any HTML entities in the code
            # This ensures that code with special characters like < > " is properly formatted
            code = code_result.get("code", "")
            if code:
                code = html.unescape(code)  # Convert any HTML entities back to their original characters
            
            # Compile the final solution
            solution = {
                "problem_analysis": plan_result.get("problem_analysis", ""),
                "approach": plan_result.get("approach", []),
                "code": code,  # Use the unescaped code
                "file_structure": code_result.get("file_structure", {}),
                "language": clean_lang,
                "libraries": code_result.get("libraries", []),
                "best_practices": code_result.get("best_practices", []),
                "performance_considerations": plan_result.get("performance_considerations", [])
            }
            
            logger.info("Successfully generated solution")
            
            return {
                "status": "success",
                "solution": solution
            }
        
        except Exception as e:
            logger.error(f"Error in problem-solving workflow: {str(e)}")
            return {
                "status": "failed",
                "error": f"Error generating solution: {str(e)}",
                "solution": {}
            }
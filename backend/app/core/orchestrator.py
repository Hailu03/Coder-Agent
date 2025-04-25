"""Agent Orchestrator module for the Collaborative Coding Agents application.

This module defines the orchestration mechanism that coordinates the collaborative 
workflow between different specialized agents.
"""

import logging
import asyncio
import html
import re
from typing import Dict, Any, List, Optional, Callable

from ..agents.planner import PlannerAgent
from ..agents.researcher import ResearchAgent
from ..agents.code_generator import CodeGeneratorAgent
from ..agents.test_executor import TestExecutionAgent
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
        self.test_executor_agent = TestExecutionAgent(self.ai_service)
        
        logger.info("Agent Orchestrator initialized")
    
    async def solve_problem(
        self, 
        requirements: str, 
        language: str = "python", 
        additional_context: Optional[str] = None,
        phase_callback: Optional[Callable[[str, Optional[float]], None]] = None
    ) -> Dict[str, Any]:
        """Solve a programming problem through collaborative agent workflow.
        
        Args:
            requirements: The programming problem requirements
            language: The target programming language
            additional_context: Additional context or constraints for the problem
            phase_callback: Optional callback function to report phase progress
            
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
            
            # Update phase status
            if phase_callback:
                phase_callback("planning", 10)
            
            # Phase 1: Planning
            planning_input = {
                "requirements": full_requirements,
                "language": clean_lang
            }
            
            logger.info("Phase 1: Planning solution approach")
            plan_result = await self.planner_agent.process(planning_input)
            
            # Update phase status
            if phase_callback:
                phase_callback("research", 30)
            
            # Phase 2: Research
            research_input = {
                "requirements": full_requirements,
                "language": clean_lang,
                "plan": plan_result
            }
            
            logger.info("Phase 2: Researching relevant information")
            research_result = await self.research_agent.process(research_input)
            
            # Update phase status
            if phase_callback:
                phase_callback("code_generation", 50)
            
            # Phase 3: Code Generation
            code_gen_input = {
                "requirements": full_requirements,
                "language": clean_lang,
                "plan": plan_result,
                "research": research_result
            }
            
            logger.info("Phase 3: Generating code solution")
            code_result = await self.code_generator_agent.process(code_gen_input)
            
            # Generate test cases based on requirements and code analysis
            test_cases = await self._generate_test_cases(full_requirements, code_result.get("code", ""), clean_lang)
            
            # Update phase status
            if phase_callback:
                phase_callback("test_execution", 70)
            
            # Phase 4: Test Execution 
            test_execution_result = None
            if test_cases:
                logger.info(f"Phase 4: Executing {len(test_cases)} test cases")
                test_input = {
                    "code": code_result.get("code", ""),
                    "language": clean_lang,
                    "test_cases": test_cases
                }
                
                test_execution_result = await self.test_executor_agent.process(test_input)
                logger.info(f"Test execution completed: {test_execution_result.get('passed', False)}")
            
            # Prepare agent responses for collaboration
            agent_responses = [
                {
                    "agent": "PlannerAgent",
                    "type": "planning_result",
                    **plan_result
                },
                {
                    "agent": "ResearchAgent",
                    "type": "research_result",
                    **research_result
                },
                {
                    "agent": "CodeGeneratorAgent",
                    "type": "code_generation_result",
                    "code": code_result.get("code", ""),
                    "language": clean_lang,
                    **code_result
                }
            ]
            
            # Add test execution results if available
            if test_execution_result:
                agent_responses.append({
                    "agent": "TestExecutionAgent",
                    "type": "test_execution_result",
                    **test_execution_result
                })
            
            # Update phase status
            if phase_callback:
                phase_callback("refinement", 85)
            
            # Phase 5: Refinement (Collaboration between agents to refine the code)
            logger.info("Phase 5: Refining code through agent collaboration")
            collaboration_result = await self.code_generator_agent.collaborate(agent_responses)
            
            # Use refined code if available, otherwise use the original code
            if collaboration_result and collaboration_result.get("refined_code"):
                logger.info("Using refined code from collaboration phase")
                refined_code = collaboration_result.get("refined_code", "")
                refined_file_structure = collaboration_result.get("file_structure", code_result.get("file_structure", {}))
                
                # Update code result with refined code
                code = refined_code
                file_structure = refined_file_structure
                
                # If tests failed initially, run tests again on the refined code
                if test_execution_result and not test_execution_result.get("passed", False) and test_cases:
                    logger.info("Re-running tests on refined code")
                    test_input = {
                        "code": code,
                        "language": clean_lang,
                        "test_cases": test_cases
                    }
                    
                    test_execution_result = await self.test_executor_agent.process(test_input)
                    logger.info(f"Refined code test results: {test_execution_result.get('passed', False)}")
            else:
                logger.info("Using original code (collaboration did not produce refined code)")
                code = code_result.get("code", "")
                file_structure = code_result.get("file_structure", {})
            
            # Unescape any HTML entities in the code
            if code:
                code = html.unescape(code)  # Convert any HTML entities back to their original characters
            
            # Update phase status
            if phase_callback:
                phase_callback("completed", 100)
            
            # Compile the final solution
            solution = {
                "problem_analysis": plan_result.get("problem_analysis", ""),
                "approach": plan_result.get("approach", []),
                "code": code,  # Use the refined or original code
                "file_structure": file_structure,
                "language": clean_lang,
                "libraries": code_result.get("libraries", []),
                "best_practices": code_result.get("best_practices", []),
                "performance_considerations": plan_result.get("performance_considerations", [])
            }
            
            # Add test results if available
            if test_execution_result:
                solution["test_results"] = test_execution_result
            
            logger.info("Successfully generated solution")
            
            return {
                "status": "success",
                "solution": solution
            }
        
        except Exception as e:
            logger.error(f"Error in problem-solving workflow: {str(e)}")
            if phase_callback:
                phase_callback("failed", 0)
                
            return {
                "status": "failed",
                "error": f"Error generating solution: {str(e)}",
                "solution": {}
            }
    
    async def _generate_test_cases(self, requirements: str, code: str, language: str) -> List[Dict[str, Any]]:
        """Generate comprehensive test cases for the given problem and code.
        
        Args:
            requirements: The problem requirements 
            code: The generated code solution
            language: The programming language
            
        Returns:
            List of test cases with varying difficulty levels
        """
        # First extract any explicit test cases from the requirements
        test_cases = self._extract_test_cases_from_requirements(requirements)
        
        # If we have fewer than 3 test cases, generate additional ones
        if len(test_cases) < 3:
            try:
                # Prepare a prompt for the AI to generate additional test cases with varying difficulty
                prompt = f"""
                Based on the following problem requirements and solution code, generate {5 - len(test_cases)} additional test cases with varying difficulty (easy, medium, hard).
                
                REQUIREMENTS:
                {requirements}
                
                CODE SOLUTION:
                ```{language}
                {code}
                ```
                
                For each test case, provide:
                1. A brief description of what the test case is checking
                2. An input value
                3. The expected output
                4. The difficulty level (easy, medium, or hard)
                
                Make sure to include edge cases, boundary conditions, and special cases.
                Format each test case as a JSON object with fields: "description", "input", "expected_output", and "difficulty".
                """
                
                # Generate test cases using AI service
                response = await self.ai_service.generate_structured_output(
                    prompt=prompt,
                    output_schema={
                        "type": "object",
                        "properties": {
                            "test_cases": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "input": {"type": "string"},
                                        "expected_output": {"type": "string"},
                                        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]}
                                    },
                                    "required": ["description", "input", "expected_output", "difficulty"]
                                }
                            }
                        },
                        "required": ["test_cases"]
                    }
                )
                
                # Add the generated test cases to our list
                if response and "test_cases" in response:
                    for idx, test_case in enumerate(response["test_cases"]):
                        test_cases.append({
                            "description": f"{test_case['description']} (Difficulty: {test_case['difficulty']})",
                            "input": test_case["input"],
                            "expected_output": test_case["expected_output"]
                        })
            except Exception as e:
                logger.error(f"Error generating additional test cases: {str(e)}")
        
        # Ensure we have at least one test case
        if not test_cases:
            # Add a simple test case as fallback
            test_cases.append({
                "description": "Basic functionality test",
                "input": "Test input",
                "expected_output": "Expected output"
            })
        
        return test_cases
    
    def _extract_test_cases_from_requirements(self, requirements: str) -> List[Dict[str, Any]]:
        """Extract test cases from requirements text.
        
        Args:
            requirements: The problem requirements text
            
        Returns:
            List of extracted test cases
        """
        test_cases = []
        
        # Look for common test case patterns in the requirements
        
        # Pattern 1: "Example: Input: X Output: Y" format
        example_pattern = r"Example[s]?[\s\d]*:[\s\n]*(Input[\s\n]*:[\s\n]*(.+?)[\s\n]*Output[\s\n]*:[\s\n]*(.+?)(?=Example|$))"
        example_matches = re.finditer(example_pattern, requirements, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(example_matches):
            test_cases.append({
                "description": f"Example {i+1}",
                "input": match.group(2).strip(),
                "expected_output": match.group(3).strip()
            })
        
        # Pattern 2: "Test Case: X => Y" format
        test_case_pattern = r"Test Case[\s\d]*:[\s\n]*(.+?)[\s\n]*=>[\s\n]*(.+?)[\s\n]*(?=Test Case|$)"
        test_case_matches = re.finditer(test_case_pattern, requirements, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(test_case_matches):
            test_cases.append({
                "description": f"Test Case {i+1}",
                "input": match.group(1).strip(),
                "expected_output": match.group(2).strip()
            })
        
        # Pattern 3: Table format with "Input" and "Output" columns
        # This is more complex and might need a more sophisticated parser in a real implementation
        
        return test_cases
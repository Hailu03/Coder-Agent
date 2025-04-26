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
            test_cases_code = await self._generate_test_cases_code(full_requirements, code_result.get("code", ""), clean_lang)
    
            # Update phase status
            if phase_callback:
                phase_callback("test_execution", 70)
            
            # Phase 4: Test Execution 
            test_execution_result = None
            if test_cases_code:
                logger.info(f"Phase 4: Executing test cases")
                test_input = {
                    "code": test_cases_code,
                    "language": clean_lang,
                }
                
                test_execution_result = await self.test_executor_agent.process(test_input)
                logger.info(f"Test execution summary: {test_execution_result.get('summary', '')}")
                logger.info(f"Test Exection Result: {test_execution_result.get('result','')}")
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
                if test_execution_result and not test_execution_result.get("passed", False):
                    logger.info("Re-running tests on refined code")
                    
                    # Generate new test cases for the refined code
                    refined_test_cases_code = await self._generate_test_cases_code(full_requirements, code, clean_lang)
                    
                    test_input = {
                        "code": refined_test_cases_code,
                        "language": clean_lang
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
    
    async def _generate_test_cases_code(self, requirements: str, code: str, language: str) -> str:
        """Generate a complete test script with solution code and test cases.
        
        Args:
            requirements: The problem requirements 
            code: The generated code solution
            language: The programming language
            
        Returns:
            A complete test script with solution code and test cases
        """
        logger.info(f"Generating test cases for the {language} code solution")

        # First extract any explicit test cases from the requirements
        test_cases = self._extract_test_cases_from_requirements(requirements)
        logger.info(f"Test cases extracted:\n {test_cases}")
        
        try:
            # Prepare language-specific instructions for testing
            if language.lower() in ["python", "py"]:
                test_framework = "unittest framework"
                file_description = "Python script"
            elif language.lower() in ["javascript", "js", "node", "nodejs"]:
                test_framework = "Jest or Mocha testing framework"
                file_description = "JavaScript file"
            elif language.lower() == "java":
                test_framework = "JUnit framework" 
                file_description = "Java file"
            elif language.lower() in ["c", "cpp", "c++"]:
                test_framework = "testing code using assertions"
                file_description = f"{language} file"
            else:
                # Default to Python for unknown languages
                test_framework = "testing framework appropriate for the language"
                file_description = f"{language} code file"
                
            # Prepare a prompt for the AI to generate a complete test script
            prompt = f"""
            Based on the following problem requirements and solution code, create a complete executable test script.
            
            REQUIREMENTS:
            {requirements}
            
            CODE SOLUTION:
            ```{language}
            {code}
            ```
            
            Create a SINGLE self-contained {file_description} that:
            1. First defines the solution code exactly as provided above
            2. Then defines a {test_framework} to test the solution 
            3. Creates test cases including the following extracted from requirements: 
            {test_cases}
            4. Adds additional test cases to cover edge cases and special situations
            5. Has a main section that runs all tests and reports success/failure for each test
            6. Prints clear output showing test results, expected vs actual values, and any errors
            
            The output should be formatted to help identify:
            - Which test failed
            - What was expected vs what was received
            - Helpful error messages explaining potential bugs
            
            The script should be 100% runnable as-is with no dependencies outside the standard library.
            
            Format your response as a single {file_description} with no additional text or markdown.
            """
            
            # Generate the complete test script using AI service
            complete_test_script = await self.ai_service.generate_text(prompt)
            
            # Clean up the response to ensure it's just the code
            markdown_pattern = f"```{language}"
            if markdown_pattern.lower() in complete_test_script.lower():
                # Look for language-specific code block
                start_idx = re.search(f"```{language}", complete_test_script, re.IGNORECASE)
                if start_idx:
                    start = start_idx.end()
                else:
                    start = complete_test_script.find("```") + 3
            elif "```" in complete_test_script:
                start = complete_test_script.find("```") + 3
            else:
                start = 0
                
            end = complete_test_script.rfind("```")
            if end != -1:
                complete_test_script = complete_test_script[start:end].strip()
            else:
                complete_test_script = complete_test_script[start:].strip()
                
            return complete_test_script

        except Exception as e:
            logger.error(f"Error generating complete test script: {str(e)}")
            # Return a basic test with just the solution code
            return f"// Solution code for {language}\n{code}\n\n// Basic test runner\nconsole.log('Error generating test cases')" if language.lower() in ["javascript", "js"] else f"# Solution code\n{code}\n\n# Basic test runner\nif __name__ == '__main__':\n    print('Error generating test cases')"
    
    def _extract_test_cases_from_requirements(self, requirements: str) -> List[Dict[str, Any]]:
        logger.info("Extracting test cases from requirements")
        test_cases = []
        
        # Pattern 1: "Example: Input: X Output: Y" format
        example_pattern = r"Example[s]?[\s\d]*:[\s\n]*(Input[\s\n]*:[\s\n]*(.+?)[\s\n]*Output[\s\n]*:[\s\n]*(.+?)(?=Example|Constraint|$))"
        example_matches = re.finditer(example_pattern, requirements, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(example_matches):
            # Clean the output - remove any trailing constraints or explanations
            raw_output = match.group(3).strip()
            
            # First split by Constraint
            clean_output = re.split(r"\s*\n+\s*Constraint", raw_output, flags=re.IGNORECASE)[0].strip()
            
            # Then also split by Explanation
            clean_output = re.split(r"\s*\n+\s*Explanation:", clean_output, flags=re.IGNORECASE)[0].strip()
            
            test_cases.append({
                "description": f"Example {i+1}",
                "input": match.group(2).strip(),
                "expected_output": clean_output
            })
            logger.info(f"Extracted test case {i+1}: {test_cases[-1]}")
    
        return test_cases
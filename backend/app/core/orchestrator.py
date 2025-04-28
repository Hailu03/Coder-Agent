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
from ..agents.developer import DeveloperAgent
from ..agents.tester import TesterAgent
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
        self.code_generator_agent = DeveloperAgent(self.ai_service)
        self.test_executor_agent = TesterAgent(self.ai_service)
        
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
            logger.info(f"Planning result: {plan_result}")
            
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
            logger.info(f"Research result: {research_result}")
            
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
            test_cases_code = await self.test_executor_agent._generate_test_cases_code(full_requirements, code_result.get("code", ""), clean_lang)
    
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
                    "agent": "DeveloperAgent",
                    "type": "code_generation_result",
                    "code": code_result.get("code", ""),
                    "language": clean_lang,
                    **code_result
                }
            ]
            
            # Add test execution results if available
            if test_execution_result:
                agent_responses.append({
                    "agent": "TesterAgent",
                    "type": "test_execution_result",
                    **test_execution_result
                })

            # Nếu test đầu đã pass thì bỏ qua refine
            if test_execution_result and test_execution_result.get('passed', False):
                code = code_result.get("code", "")
                file_structure = code_result.get("file_structure", {})
                if phase_callback:
                    phase_callback("completed", 100)
            else:
                # Update phase status
                if phase_callback:
                    phase_callback("refinement", 85)
                # Thêm cơ chế tự động refine code khi test không pass
                max_refine_attempts = 3  # Số lần refine tối đa
                refine_count = 0
                code = code_result.get("code", "")
                file_structure = code_result.get("file_structure", {})
                while refine_count < max_refine_attempts:
                    # Phase 5: Refinement (Collaboration between agents to refine the code)
                    if refine_count == 0:
                        logger.info("Phase 5: Refining code through agent collaboration")
                    else:
                        logger.info(f"Phase 5: Refine attempt {refine_count + 1}/{max_refine_attempts}")
                        if phase_callback:
                            phase_callback(f"refinement_{refine_count + 1}", 85 + (refine_count * 5))
                    # Cập nhật code trong agent_responses nếu đã có refinement trước đó
                    if refine_count > 0:
                        for i, response in enumerate(agent_responses):
                            if response.get("type") == "code_generation_result":
                                agent_responses[i]["code"] = code
                    try:
                        collaboration_result = await self.code_generator_agent.collaborate(agent_responses)
                        # Use refined code if available
                        if collaboration_result and collaboration_result.get("refined_code"):
                            logger.info(f"Using refined code from collaboration attempt {refine_count + 1}")
                            refined_code = collaboration_result.get("refined_code", "")
                            refined_file_structure = collaboration_result.get("file_structure", file_structure)
                            # Update code result with refined code
                            code = refined_code
                            file_structure = refined_file_structure
                            logger.info(f"Re-running tests on refined code (attempt {refine_count + 1})")
                            # Generate new test cases for the refined code
                            refined_test_cases_code = await self.test_executor_agent._generate_test_cases_code(
                                full_requirements, code, clean_lang
                            )
                            test_input = {
                                "code": refined_test_cases_code,
                                "language": clean_lang
                            }
                            test_execution_result = await self.test_executor_agent.process(test_input)
                            test_passed = test_execution_result.get('passed', False)
                            logger.info(f"Refined code test results (attempt {refine_count + 1}): {test_passed}")
                            # Thêm kết quả test mới vào agent_responses để refine lần tiếp theo nếu cần
                            for i, response in enumerate(agent_responses):
                                if response.get("type") == "test_execution_result":
                                    agent_responses[i] = {
                                        "agent": "TesterAgent",
                                        "type": "test_execution_result",
                                        **test_execution_result
                                    }
                                    break
                            else:
                                # Nếu không có test_execution_result trước đó, thêm mới
                                agent_responses.append({
                                    "agent": "TesterAgent",
                                    "type": "test_execution_result",
                                    **test_execution_result
                                })
                            # Nếu tests đã pass, thoát khỏi vòng lặp
                            if test_passed:
                                logger.info(f"All tests passed after {refine_count + 1} refinement attempts")
                                break
                        else:
                            logger.info(f"Refinement attempt {refine_count + 1} did not produce new code")
                            break
                        refine_count += 1
                    except Exception as e:
                        logger.error(f"Error during refinement attempt {refine_count + 1}: {str(e)}")
                        break
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
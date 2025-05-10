"""Code Generator Agent module for the Collaborative Coding Agents application.

This module defines the Code Generator Agent that produces clean, optimized code.
"""

import json
import logging
import re
from typing import Dict, List, Any
from .base import Agent
from ..core.config import settings
from ..services.ai_service import AIService
from ..utils import clean_language_name

# Configure logging
logger = logging.getLogger("agents.code_generator")


class DeveloperAgent(Agent):
    """Agent responsible for generating clean, optimized code."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the Code Generator Agent.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__(name="DeveloperAgent", ai_service=ai_service)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on problem requirements, plan, and research.
        
        Args:
            input_data: Contains problem requirements, plan, research, and language
            
        Returns:
            Generated code and supporting information
        """
        requirements = input_data.get("requirements", "")
        language = clean_language_name(input_data.get("language", "python"))
        
        # Đảm bảo plan là dictionary
        plan = input_data.get("plan", {})
        if not isinstance(plan, dict):
            logger.warning(f"Plan is not a dictionary, converting to empty dict: {type(plan)}")
            plan = {}
        
        # Đảm bảo research là dictionary
        research = input_data.get("research", {})
        if not isinstance(research, dict):
            logger.warning(f"Research is not a dictionary, converting to empty dict: {type(research)}")
            research = {}
        
        logger.info(f"Generating code solution in {language}")
        
        # Extract key elements from the plan
        problem_analysis = plan.get("problem_analysis", "")
        approach = plan.get("approach", [])
        approach_text = "\n".join([f"- {step}" for step in approach]) if isinstance(approach, list) else approach
        recommended_libraries = plan.get("recommended_libraries", [])
        algorithms = plan.get("algorithms", [])
        data_structures = plan.get("data_structures", [])
        edge_cases = plan.get("edge_cases", [])
        performance_considerations = plan.get("performance_considerations", [])
        
        # Extract research findings
        libraries_info = research.get("libraries", [])
        best_practices = research.get("best_practices", [])
        code_examples = research.get("code_examples", [])
        
        # Compile best practices
        if isinstance(best_practices, list):
            best_practices_text = "\n".join([f"- {practice}" for practice in best_practices])
        else:
            best_practices_text = str(best_practices)
        
        # Compile libraries information
        libraries_text = ""
        if isinstance(libraries_info, list):
            for lib in libraries_info:
                if isinstance(lib, dict):
                    lib_name = lib.get("name", "")
                    lib_description = lib.get("description", "")
                    lib_usage = lib.get("usage_example", "")
                    
                    if lib_name:
                        libraries_text += f"\n## {lib_name}\n"
                        if lib_description:
                            libraries_text += f"{lib_description}\n"
                        if lib_usage:
                            libraries_text += f"Example usage:\n{lib_usage}\n"
                elif isinstance(lib, str):
                    libraries_text += f"\n## {lib}\n"
        elif isinstance(libraries_info, dict):
            for lib_name, lib_data in libraries_info.items():
                libraries_text += f"\n## {lib_name}\n"
                if isinstance(lib_data, dict):
                    lib_description = lib_data.get("description", "")
                    if lib_description:
                        libraries_text += f"{lib_description}\n"
                    
                    examples = lib_data.get("examples", [])
                    if examples and isinstance(examples, list):
                        for ex in examples:
                            if isinstance(ex, dict):
                                ex_code = ex.get("code", "")
                                if ex_code:
                                    libraries_text += f"Example usage:\n{ex_code}\n"
        
        # Compile examples from research
        examples_text = ""
        if isinstance(code_examples, list):
            for example in code_examples:
                if isinstance(example, dict):
                    example_desc = example.get("description", "")
                    example_code = example.get("code", "")
                    
                    if example_desc and example_code:
                        examples_text += f"\n## {example_desc}\n{example_code}\n"
                elif isinstance(example, str):
                    examples_text += f"\n{example}\n"
        
        prompt = f"""
        You are an expert {language} developer. I need you to generate clean, optimized code for the following problem:
        
        PROBLEM REQUIREMENTS:
        {requirements}
        
        PROBLEM ANALYSIS:
        {problem_analysis}
        
        APPROACH:
        {approach_text}
        
        KEY LIBRARIES TO USE:
        {', '.join(recommended_libraries) if isinstance(recommended_libraries, list) else str(recommended_libraries)}
        
        KEY ALGORITHMS:
        {', '.join(algorithms) if isinstance(algorithms, list) else str(algorithms)}
        
        KEY DATA STRUCTURES:
        {', '.join(data_structures) if isinstance(data_structures, list) else str(data_structures)}
        
        EDGE CASES TO HANDLE:
        {', '.join(edge_cases) if isinstance(edge_cases, list) else str(edge_cases)}
        
        PERFORMANCE CONSIDERATIONS:
        {', '.join(performance_considerations) if isinstance(performance_considerations, list) else str(performance_considerations)}
        
        BEST PRACTICES TO FOLLOW:
        {best_practices_text if best_practices_text else 'Follow standard coding best practices for ' + language}
        
        LIBRARIES INFORMATION:
        {libraries_text if libraries_text else 'No specific library information available'}
        
        CODE EXAMPLES FOR REFERENCE:
        {examples_text if examples_text else 'No specific code examples available'}
        
        Please provide a complete code solution with:
        1. Well-structured, clean, and optimized code in both runtime and memory-wise
        2. Appropriate error handling
        3. Clear comments explaining complex parts
        4. Any necessary helper functions or classes
        5. A recommended file structure if the solution spans multiple files
        
        Structure your response as a JSON object for easy parsing.
        """
        
        # Output schema for structured response
        output_schema = {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "explanation": {"type": "string"},
                "libraries": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "best_practices": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "file_structure": {
                    "type": "object",
                    "properties": {
                        "directories": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "description": {"type": "string"}
                                },
                                "required": ["path", "description"],
                                "additionalProperties": False
                            }
                        },
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "description": {"type": "string"},
                                    "components": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["path", "description", "components"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["directories", "files"],
                    "additionalProperties": False
                }
            },
            "required": ["code", "explanation", "libraries", "best_practices", "file_structure"],
            "additionalProperties": False
        }
        
        response = await self.generate_structured_output(prompt, output_schema)

        # strip any markdown code block formatting from the code
        response["code"] = self.strip_markdown_code_block(response["code"])
        
        if not response:
            logger.warning("Failed to generate structured code response, falling back to text generation")
            text_response = await self.generate_text(prompt)
            return {
                "code": text_response,
                "explanation": "",
                "libraries": [],
                "best_practices": [],
                "file_structure": {}
            }
        
        # Ensure the code field exists
        if "code" not in response:
            logger.warning("No code field in response, using explanation as code")
            response["code"] = response.get("explanation", "// No code generated")
        
        # Format the response
        formatted_response = {
            "code": response.get("code", ""),
            "explanation": response.get("explanation", ""),
            "libraries": response.get("libraries", []),
            "best_practices": response.get("best_practices", []),
            "file_structure": response.get("file_structure", {})
        }
        
        return formatted_response
    
    async def collaborate(self, other_agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Refine the code based on feedback from other agents.
        
        Args:
            other_agent_responses: Responses from other agents
            
        Returns:
            Dictionary with refined code
        """
        # Extract the latest code generation result
        code = None
        language = "python"
        
        for response in other_agent_responses:
            if response.get("type") == "code_generation_result":
                code = response.get("code", "")
                language = response.get("language", "python")
                break
        
        if not code:
            logger.warning("No code found to refine in collaboration phase")
            return {"message": "No code found to refine", "refined_code": None}
        
        # Extract insights from planner and researcher agents
        planning_insights = []
        research_insights = []
        test_insights = []
        
        for response in other_agent_responses:
            agent_name = response.get("agent", "Unknown")
            agent_type = response.get("type", "")
            
            # Skip our own responses
            if agent_name == self.name or agent_type == "code_generation_result":
                continue
                
            # Categorize feedback by agent type
            if "planner" in agent_name.lower():
                # Extract approach, algorithms, data structures etc.
                approach = response.get("approach", [])
                algorithms = response.get("algorithms", [])
                data_structures = response.get("data_structures", [])
                edge_cases = response.get("edge_cases", [])
                performance = response.get("performance_considerations", [])
                
                if approach or algorithms or data_structures or edge_cases or performance:
                    planning_insights.append({
                        "approach": approach,
                        "algorithms": algorithms,
                        "data_structures": data_structures,
                        "edge_cases": edge_cases,
                        "performance": performance
                    })
            elif "research" in agent_name.lower():
                # Extract libraries, best practices, code examples
                libraries = response.get("libraries", [])
                best_practices = response.get("best_practices", [])
                code_examples = response.get("code_examples", [])
                
                if libraries or best_practices or code_examples:
                    research_insights.append({
                        "libraries": libraries,
                        "best_practices": best_practices,
                        "code_examples": code_examples
                    })
            elif "tester" in agent_name.lower():
                test_results = response.get("output", [])
                test_summary = response.get("summary", [])
                time = response.get("time", [])
                error = response.get("error", [])

                test_insights.append({
                    "test_results": test_results,
                    "test_summary": test_summary,
                    "execution_time": time,
                    "error": error
                })
            else:
                # Generic feedback from other types of agents
                planning_insights.append({"content": response})
        
        if not planning_insights and not research_insights and not test_insights:
            logger.warning("No relevant feedback found during collaboration")
            return {"message": "No relevant feedback found", "refined_code": None}
        
        # Format planning insights
        planning_text = ""
        if planning_insights:
            planning_text = "PLANNING INSIGHTS:\n"
            for insight in planning_insights:
                if "approach" in insight:
                    approaches = insight.get("approach", [])
                    if approaches:
                        planning_text += "Approach:\n" + "\n".join([f"- {a}" for a in approaches]) + "\n\n"
                
                if "algorithms" in insight:
                    algorithms = insight.get("algorithms", [])
                    if algorithms:
                        planning_text += "Algorithms:\n" + "\n".join([f"- {a}" for a in algorithms]) + "\n\n"
                
                if "data_structures" in insight:
                    ds = insight.get("data_structures", [])
                    if ds:
                        planning_text += "Data Structures:\n" + "\n".join([f"- {d}" for d in ds]) + "\n\n"
                
                if "edge_cases" in insight:
                    cases = insight.get("edge_cases", [])
                    if cases:
                        planning_text += "Edge Cases:\n" + "\n".join([f"- {c}" for c in cases]) + "\n\n"
                
                if "performance" in insight:
                    perf = insight.get("performance", [])
                    if perf:
                        planning_text += "Performance Considerations:\n" + "\n".join([f"- {p}" for p in perf]) + "\n\n"
                
                if "content" in insight:
                    planning_text += f"General feedback:\n{json.dumps(insight['content'], indent=2)}\n\n"
        
        # Format research insights
        research_text = ""
        if research_insights:
            research_text = "RESEARCH INSIGHTS:\n"
            for insight in research_insights:
                if "libraries" in insight:
                    libraries = insight.get("libraries", [])
                    if libraries:
                        research_text += "Recommended Libraries:\n"
                        for lib in libraries:
                            if isinstance(lib, dict):
                                name = lib.get("name", "")
                                desc = lib.get("description", "")
                                usage = lib.get("usage_example", "")
                                
                                if name:
                                    research_text += f"- {name}\n"
                                    if desc:
                                        research_text += f"  Description: {desc}\n"
                                    if usage:
                                        research_text += f"  Example: {usage}\n"
                            elif isinstance(lib, str):
                                research_text += f"- {lib}\n"
                        research_text += "\n"
                
                if "best_practices" in insight:
                    practices = insight.get("best_practices", [])
                    if practices:
                        research_text += "Best Practices:\n" + "\n".join([f"- {p}" for p in practices]) + "\n\n"
                
                if "code_examples" in insight:
                    examples = insight.get("code_examples", [])
                    if examples:
                        research_text += "Code Examples:\n"
                        for ex in examples:
                            if isinstance(ex, dict):
                                desc = ex.get("description", "")
                                code_ex = ex.get("code", "")
                                
                                if desc:
                                    research_text += f"Example: {desc}\n"
                                if code_ex:
                                    research_text += f"```{language}\n{code_ex}\n```\n\n"
        
        # Format test insights
        test_text = f"""TEST INSIGHTS:
        Test Results:
        {test_insights[0].get('test_results', '') if test_insights else 'No test results available'}

        Analyze Test Results:
        {test_insights[0].get('summary', '') if test_insights else 'No summary available'}

        Execution Time:
        {test_insights[0].get('execution_time', '') if test_insights else 'No execution time available'}

        Error when executing:
        {test_insights[0].get('error', '') if test_insights else 'No error information available'}
        """


        # Format a prompt to refine the code based on insights
        refine_prompt = f"""
        You are an expert {language} developer. Refine and optimize the following code based on collaborative feedback from multiple AI agents:
        
        CURRENT CODE:
        ```{language}
        {code}
        ```
        
        {planning_text}
        
        {research_text}

        {test_text}
        
        INSTRUCTIONS:
        1. Improve the code structure and organization
        2. Optimize algorithms and data structures for better performance
        3. Enhance error handling and edge case management
        4. Improve the readability and maintainability
        5. Fix any bugs or potential issues
        6. Ensure the code follows clean code principles and design patterns
        7. Incorporate the insights from planning and research agents
        
        Generate the improved code implementation. Format the code using proper indentation and organization.
        Include useful comments to explain your changes and any complex logic.
        """
        
        logger.info("Generating refined code through agent collaboration")
        
        # Generate refined code using the AI service - CHANGED: generate_code to generate_text
        refined_code = await self.ai_service.generate_text(refine_prompt)
        
        refined_code = self.strip_markdown_code_block(refined_code)
        
        # Extract file structure from the refined code
        file_structure = await self._extract_file_structure(refined_code, language)
        
        return {
            "refined_code": refined_code,
            "file_structure": file_structure,
            "type": "refined_code_result",
            "agent": self.name,
            "language": language
        }
    
    def strip_markdown_code_block(self, text: str) -> str:
        """Remove markdown code block formatting from text.
        
        Args:
            text: The text that may contain markdown code blocks
            
        Returns:
            The text with markdown code block formatting removed
        """
        # Nhận diện code block markdown có hoặc không có tên ngôn ngữ
        code_blocks = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", text)
        if code_blocks:
            # Nếu có nhiều code block, lấy cái đầu tiên
            return code_blocks[0].strip()
        # Nếu không có code block, trả về text gốc
        return text.strip()
    
    async def _extract_file_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Extract file structure from generated code.
        
        Args:
            code: The generated code
            language: The programming language
            
        Returns:
            Dictionary with the recommended file structure
        """
        extract_prompt = f"""
        Analyze the following {language} code and recommend a file structure for organizing it:
        
        ```{language}
        {code}
        ```
        
        INSTRUCTIONS:
        1. Identify logical modules, classes, and functions that should be in separate files
        2. Suggest an appropriate directory structure
        3. For each file, specify which code components should be included
        4. Consider the best practices for {language} project organization
        
        Format the response as a JSON object with the following structure:
        {{
            "files": [
                {{
                    "path": "relative/path/to/file.ext",
                    "description": "Description of the file's purpose",
                    "components": ["Class1", "Function2", "etc"]
                }}
            ],
            "directories": [
                {{
                    "path": "relative/path/to/directory",
                    "description": "Description of the directory's purpose"
                }}
            ]
        }}
        """
        
        # Get response from AI service
        response = await self.ai_service.generate_text(extract_prompt)
        
        try:
            # Try to parse the response as JSON
            if isinstance(response, str):
                # Extract JSON if it's embedded in markdown code blocks
                if "```json" in response:
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    response = response[start:end].strip()
                elif "```" in response:
                    start = response.find("```") + 3
                    end = response.find("```", start)
                    response = response[start:end].strip()
                
                file_structure = json.loads(response)
            else:
                file_structure = response
                
            return file_structure
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {response}")
            
            # If we couldn't parse as JSON, return a default structure
            return {
                "files": [
                    {
                        "path": f"main.{self._get_file_extension(language)}",
                        "description": "Main file containing the entire solution",
                        "components": ["All components"]
                    }
                ],
                "directories": []
            }
    
    def _get_file_extension(self, language: str) -> str:
        """Get the file extension for a given programming language.
        
        Args:
            language: The programming language
            
        Returns:
            The file extension
        """
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "c#": "cs",
            "c++": "cpp",
            "c": "c",
            "go": "go",
            "ruby": "rb",
            "php": "php",
            "swift": "swift",
            "kotlin": "kt",
            "rust": "rs",
            "scala": "scala"
        }
        
        return extensions.get(language.lower(), "txt")
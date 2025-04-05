"""Code Generator Agent module for the Collaborative Coding Agents application.

This module defines the Code Generator Agent that produces clean, optimized code.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .base import Agent
from ..core.config import settings
from ..services.ai_service import GeminiService, OpenAIService
from ..services.ai_service import AIService
from ..utils import clean_language_name, format_code_with_language

# Configure logging
logger = logging.getLogger("agents.code_generator")


class CodeGeneratorAgent(Agent):
    """Agent responsible for generating clean, optimized code."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the Code Generator Agent.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__(name="CodeGeneratorAgent", ai_service=ai_service)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on problem requirements, plan, and research.
        
        Args:
            input_data: Contains problem requirements, plan, research, and language
            
        Returns:
            Generated code and supporting information
        """
        requirements = input_data.get("requirements", "")
        language = clean_language_name(input_data.get("language", "python"))
        plan = input_data.get("plan", {})
        research = input_data.get("research", {})
        
        logger.info(f"Generating code solution in {language}")
        
        # Extract key elements from the plan
        problem_analysis = plan.get("problem_analysis", "")
        approach = plan.get("approach", [])
        approach_text = "\n".join([f"- {step}" for step in approach])
        recommended_libraries = plan.get("recommended_libraries", [])
        algorithms = plan.get("algorithms", [])
        data_structures = plan.get("data_structures", [])
        edge_cases = plan.get("edge_cases", [])
        performance_considerations = plan.get("performance_considerations", [])
        
        # Extract research findings
        libraries_info = research.get("libraries", [])
        algorithms_info = research.get("algorithms", [])
        best_practices = research.get("best_practices", [])
        code_examples = research.get("code_examples", [])
        
        # Compile best practices
        best_practices_text = "\n".join([f"- {practice}" for practice in best_practices])
        
        # Compile libraries information
        libraries_text = ""
        for lib in libraries_info:
            lib_name = lib.get("name", "")
            lib_description = lib.get("description", "")
            lib_usage = lib.get("usage_example", "")
            
            if lib_name:
                libraries_text += f"\n## {lib_name}\n"
                if lib_description:
                    libraries_text += f"{lib_description}\n"
                if lib_usage:
                    libraries_text += f"Example usage:\n{lib_usage}\n"
        
        # Compile examples from research
        examples_text = ""
        for example in code_examples:
            example_desc = example.get("description", "")
            example_code = example.get("code", "")
            
            if example_desc and example_code:
                examples_text += f"\n## {example_desc}\n{example_code}\n"
        
        prompt = f"""
        You are an expert {language} developer. I need you to generate clean, optimized code for the following problem:
        
        PROBLEM REQUIREMENTS:
        {requirements}
        
        PROBLEM ANALYSIS:
        {problem_analysis}
        
        APPROACH:
        {approach_text}
        
        KEY LIBRARIES TO USE:
        {', '.join(recommended_libraries) if recommended_libraries else 'No specific libraries required'}
        
        KEY ALGORITHMS:
        {', '.join(algorithms) if algorithms else 'No specific algorithms required'}
        
        KEY DATA STRUCTURES:
        {', '.join(data_structures) if data_structures else 'No specific data structures required'}
        
        EDGE CASES TO HANDLE:
        {', '.join(edge_cases) if edge_cases else 'No specific edge cases identified'}
        
        PERFORMANCE CONSIDERATIONS:
        {', '.join(performance_considerations) if performance_considerations else 'No specific performance considerations identified'}
        
        BEST PRACTICES TO FOLLOW:
        {best_practices_text if best_practices else 'Follow standard coding best practices for ' + language}
        
        LIBRARIES INFORMATION:
        {libraries_text if libraries_text else 'No specific library information available'}
        
        CODE EXAMPLES FOR REFERENCE:
        {examples_text if examples_text else 'No specific code examples available'}
        
        Please provide a complete solution with:
        1. Well-structured, clean, and optimized code
        2. Appropriate error handling
        3. Clear comments explaining complex parts
        4. Any necessary helper functions or classes
        5. A recommended file structure if the solution spans multiple files
        
        Structure your response as a JSON object for easy parsing.
        """
        
        # Output schema for structured response
        output_schema = {
            "code": "string",
            "explanation": "string",
            "libraries": ["string"],
            "best_practices": ["string"],
            "file_structure": {
                "directories": [{
                    "path": "string",
                    "description": "string"
                }],
                "files": [{
                    "path": "string",
                    "description": "string",
                    "components": ["string"]
                }]
            }
        }
        
        response = await self.generate_structured_output(prompt, output_schema)
        
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
            return {"message": "No code found to refine", "refined_code": None}
        
        # Extract feedback from other agents
        feedback = []
        for response in other_agent_responses:
            agent_name = response.get("agent", "Unknown")
            agent_type = response.get("type", "")
            
            # Don't include our own responses
            if agent_name != self.name and agent_type != "code_generation_result":
                feedback.append({
                    "agent": agent_name,
                    "content": response
                })
        
        if not feedback:
            return {"message": "No relevant feedback found", "refined_code": None}
        
        # Format a prompt to refine the code based on feedback
        refine_prompt = f"""
        Refine and optimize the following {language} code based on feedback from other agents:
        
        CURRENT CODE:
        ```{language}
        {code}
        ```
        
        FEEDBACK:
        {json.dumps(feedback, indent=2)}
        
        INSTRUCTIONS:
        1. Improve the code structure and organization
        2. Optimize algorithms and data structures for better performance
        3. Enhance error handling and edge case management
        4. Improve the readability and maintainability
        5. Fix any bugs or potential issues
        6. Ensure the code follows clean code principles and OOP design patterns
        
        Generate the improved code implementation. Format the code using proper indentation and organization.
        """
        
        # Generate refined code using the AI service
        refined_code = await self.ai_service.generate_code(refine_prompt, language)
        
        # Extract file structure from the refined code
        file_structure = await self._extract_file_structure(refined_code, language)
        
        return {
            "refined_code": refined_code,
            "file_structure": file_structure,
            "type": "refined_code_result",
            "agent": self.name,
            "language": language
        }
    
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
            self.logger.error(f"Failed to parse AI response as JSON: {response}")
            
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
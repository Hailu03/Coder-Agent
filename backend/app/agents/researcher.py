"""Researcher Agent module for the Collaborative Coding Agents application.

This module defines the Researcher Agent that gathers information from external sources.
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional

from .base import Agent
from ..services.ai_service import AIService
from ..utils import clean_language_name
from ..services.mcp import MCPServer

# Configure logging
logger = logging.getLogger("agents.researcher")

class ResearchAgent(Agent):
    """Agent responsible for gathering information from external sources."""
    
    def __init__(self, ai_service: AIService, mcp_server: Optional[MCPServer] = None):
        """Initialize the Researcher Agent.
        
        Args:
            ai_service: AI service for interacting with language models
            mcp_server: Optional MCP server for accessing external code information
        """
        super().__init__(name="ResearchAgent", ai_service=ai_service)
        self.mcp_server = mcp_server or MCPServer()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Research additional information related to the problem.
        
        Args:
            input_data: Contains problem requirements, plan, and language
            
        Returns:
            Research findings including relevant algorithms, libraries, and examples
        """
        requirements = input_data.get("requirements", "")
        language = clean_language_name(input_data.get("language", "python"))
        plan = input_data.get("plan", {})
        
        # Extract key elements from the plan
        problem_analysis = plan.get("problem_analysis", "")
        approach = plan.get("approach", [])
        recommended_libraries = plan.get("recommended_libraries", [])
        algorithms = plan.get("algorithms", [])
        data_structures = plan.get("data_structures", [])
        design_patterns = plan.get("design_patterns", [])
        edge_cases = plan.get("edge_cases", [])
        performance_considerations = plan.get("performance_considerations", [])
        
        logger.info(f"Starting research for {language} solution")
        
        # Validate MCP server connection first to avoid multiple connection errors
        connection_ok = await self.mcp_server.validate_connection()
        if not connection_ok:
            logger.warning("MCP server connection failed. Using AI service without web search.")
        
        # Research results containers
        libraries_info = []
        best_practices = []
        code_examples = []
        summary = {}
        
        # Create a list of research tasks
        research_tasks = []
        
        # 1. Research recommended libraries
        if recommended_libraries:
            if isinstance(recommended_libraries, list):
                for lib in recommended_libraries:
                    if lib:
                        research_tasks.append(self._safe_research_task(self._research_library(lib, language), f"library {lib}"))
            elif isinstance(recommended_libraries, str):
                research_tasks.append(self._safe_research_task(self._research_library(recommended_libraries, language), f"library {recommended_libraries}"))
        
        # 2. Research algorithms
        if algorithms:
            if isinstance(algorithms, list):
                for algo in algorithms:
                    if algo:
                        research_tasks.append(self._safe_research_task(self._research_algorithm(algo, language), f"algorithm {algo}"))
            elif isinstance(algorithms, str):
                research_tasks.append(self._safe_research_task(self._research_algorithm(algorithms, language), f"algorithm {algorithms}"))
        
        # 3. Research data structures
        if data_structures:
            if isinstance(data_structures, list):
                for ds in data_structures:
                    if ds:
                        research_tasks.append(self._safe_research_task(self._research_data_structure(ds, language), f"data structure {ds}"))
            elif isinstance(data_structures, str):
                research_tasks.append(self._safe_research_task(self._research_data_structure(data_structures, language), f"data structure {data_structures}"))
        
        # 4. Research design patterns
        if design_patterns:
            if isinstance(design_patterns, list):
                for pattern in design_patterns:
                    if pattern:
                        research_tasks.append(self._safe_research_task(self._research_design_pattern(pattern, language), f"design pattern {pattern}"))
            elif isinstance(design_patterns, str):
                research_tasks.append(self._safe_research_task(self._research_design_pattern(design_patterns, language), f"design pattern {design_patterns}"))
        
        # 5. Research performance considerations
        if performance_considerations:
            research_tasks.append(self._safe_research_task(self._research_performance(performance_considerations, language), "performance considerations"))
            
        # 6. Research best practices for language
        research_tasks.append(self._safe_research_task(self._research_best_practices(language), f"{language} best practices"))
        
        # Process all research tasks concurrently with error handling
        research_results = await asyncio.gather(*research_tasks)
        
        # Process research results and categorize them
        for result in research_results:
            if not result:
                continue
                
            if "topic_type" in result:
                topic_type = result["topic_type"]
                if topic_type == "library":
                    libraries_info.append(result["data"])
                elif topic_type == "algorithm":
                    code_examples.append(result["data"])
                elif topic_type == "data_structure":
                    code_examples.append(result["data"])
                elif topic_type == "design_pattern":
                    best_practices.append(result["data"])
                elif topic_type == "best_practice":
                    best_practices.append(result["data"])
                elif topic_type == "performance":
                    performance_info = result["data"]
                    if performance_info not in best_practices:
                        best_practices.append(performance_info)
            
            # Add to summary
            if "summary" in result and result["summary"]:
                topic = result.get("topic", "")
                if topic:
                    summary[topic] = result["summary"]
        
        # If no external research was successful, generate information using AI model knowledge
        if not libraries_info and not best_practices and not code_examples:
            logger.warning("No research results obtained. Generating information using AI model knowledge.")
            try:
                # Generate research using AI knowledge
                ai_research = await self._generate_ai_knowledge_research(requirements, language, plan)
                if ai_research:
                    libraries_info.extend(ai_research.get("libraries", []))
                    best_practices.extend(ai_research.get("best_practices", []))
                    code_examples.extend(ai_research.get("code_examples", []))
                    summary.update(ai_research.get("summary", {}))
            except Exception as e:
                logger.error(f"Error generating AI knowledge research: {e}")
        
        # Create research report
        return {
            "libraries": libraries_info,
            "best_practices": best_practices,
            "code_examples": code_examples,
            "summary": summary,
            "language": language
        }
    
    async def _research_library(self, library: str, language: str) -> Dict[str, Any]:
        """Research a specific library for the given language.
        
        Args:
            library: Library name to research
            language: Programming language
            
        Returns:
            Structured research findings
        """
        logger.info(f"Researching library: {library} for {language}")
        search_query = f"{library} library in {language} programming tutorial examples usage"
        
        try:
            # Search using MCP Server
            search_results = await self.mcp_server.search(search_query)
            
            if "error" in search_results:
                logger.error(f"Error searching for library {library}: {search_results['error']}")
                return None
                
            # Summarize search results
            summarize_prompt = f"""
            I need a concise summary of the "{library}" library in {language} programming.
            
            Based on the following search results, provide:
            1. A brief description (1-2 sentences)
            2. Key features or functions (3-5 points)
            3. A short code example showing basic usage
            4. When to use this library (1-2 sentences)
            
            Search results:
            {json.dumps(search_results, indent=2)}
            
            Return your response in JSON format with these fields:
            {{
                "name": "Name of the library",
                "description": "Brief description",
                "key_features": ["feature1", "feature2", ...],
                "usage_example": "Code example showing usage",
                "when_to_use": "When to use this library"
            }}
            """
            
            summary = await self.ai_service.generate_structured_output(summarize_prompt, {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "key_features": {"type": "array", "items": {"type": "string"}},
                    "usage_example": {"type": "string"},
                    "when_to_use": {"type": "string"}
                }
            })
            
            # Create simplified summary
            simple_summary = f"{library}: {summary.get('description', '')}. {summary.get('when_to_use', '')}"
            logger.info(f"Library summary: {simple_summary}")

            return {
                "topic": library,
                "topic_type": "library",
                "summary": simple_summary,
                "data": summary
            }
            
        except Exception as e:
            logger.error(f"Error in _research_library: {e}")
            return None
            
    async def _research_algorithm(self, algorithm: str, language: str) -> Dict[str, Any]:
        """Research a specific algorithm.
        
        Args:
            algorithm: Algorithm name to research
            language: Programming language
            
        Returns:
            Structured research findings
        """
        logger.info(f"Researching algorithm: {algorithm} in {language}")
        search_query = f"{algorithm} algorithm implementation in {language} explanation"
        
        try:
            # Search using MCP Server
            search_results = await self.mcp_server.search(search_query)
            
            if "error" in search_results:
                logger.error(f"Error searching for algorithm {algorithm}: {search_results['error']}")
                return None
                
            # Summarize search results
            summarize_prompt = f"""
            I need a concise summary of the "{algorithm}" algorithm, with implementation in {language}.
            
            Based on the following search results, provide:
            1. A brief description of the algorithm (1-2 sentences)
            2. Time and space complexity
            3. Key characteristics or use cases
            4. A code implementation in {language}
            
            Search results:
            {json.dumps(search_results, indent=2)}
            
            Return your response in JSON format with these fields:
            {{
                "algorithm_name": "Name of the algorithm",
                "description": "Brief description",
                "complexity": "Time and space complexity",
                "use_cases": ["use case 1", "use case 2", ...],
                "code_implementation": "Code example implementing the algorithm in {language}"
            }}
            """
            
            summary = await self.ai_service.generate_structured_output(summarize_prompt, {
                "type": "object",
                "properties": {
                    "algorithm_name": {"type": "string"},
                    "description": {"type": "string"},
                    "complexity": {"type": "string"},
                    "use_cases": {"type": "array", "items": {"type": "string"}},
                    "code_implementation": {"type": "string"}
                }
            })
            
            # Create simplified summary
            simple_summary = f"{algorithm}: {summary.get('description', '')}. Complexity: {summary.get('complexity', '')}"
            logger.info(f"Algorithm summary: {simple_summary}")

            return {
                "topic": algorithm,
                "topic_type": "algorithm",
                "summary": simple_summary,
                "data": {
                    "description": f"**{algorithm}**: {summary.get('description', '')}",
                    "code": summary.get('code_implementation', ''),
                    "complexity": summary.get('complexity', '')
                }
            }
            
        except Exception as e:
            logger.error(f"Error in _research_algorithm: {e}")
            return None
            
    async def _research_data_structure(self, data_structure: str, language: str) -> Dict[str, Any]:
        """Research a specific data structure.
        
        Args:
            data_structure: Data structure to research
            language: Programming language
            
        Returns:
            Structured research findings
        """
        logger.info(f"Researching data structure: {data_structure} in {language}")
        search_query = f"{data_structure} data structure in {language} implementation example"
        
        try:
            # Search using MCP Server
            search_results = await self.mcp_server.search(search_query)
            
            if "error" in search_results:
                logger.error(f"Error searching for data structure {data_structure}: {search_results['error']}")
                return None
                
            # Summarize search results
            summarize_prompt = f"""
            I need a concise summary of the "{data_structure}" data structure in {language}.
            
            Based on the following search results, provide:
            1. A brief description (1-2 sentences)
            2. Operations and their time complexities
            3. A code example implementing this data structure in {language}
            4. Common use cases
            
            Search results:
            {json.dumps(search_results, indent=2)}
            
            Return your response in JSON format with these fields:
            {{
                "data_structure": "Name of the data structure",
                "description": "Brief description",
                "operations": [
                    {{"operation": "operation name", "complexity": "time complexity"}}
                ],
                "code_example": "Example implementation in {language}",
                "use_cases": ["use case 1", "use case 2", ...]
            }}
            """
            
            summary = await self.ai_service.generate_structured_output(summarize_prompt, {
                "type": "object",
                "properties": {
                    "data_structure": {"type": "string"},
                    "description": {"type": "string"},
                    "operations": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string"},
                            "complexity": {"type": "string"}
                        }
                    }},
                    "code_example": {"type": "string"},
                    "use_cases": {"type": "array", "items": {"type": "string"}}
                }
            })
            
            # Create simplified summary
            simple_summary = f"{data_structure}: {summary.get('description', '')}"
            logger.info(f"Data structure summary: {simple_summary}")

            return {
                "topic": data_structure,
                "topic_type": "data_structure",
                "summary": simple_summary,
                "data": {
                    "description": f"**{data_structure}**: {summary.get('description', '')}",
                    "code": summary.get('code_example', '')
                }
            }
            
        except Exception as e:
            logger.error(f"Error in _research_data_structure: {e}")
            return None
    
    async def _research_design_pattern(self, pattern: str, language: str) -> Dict[str, Any]:
        """Research a specific design pattern.
        
        Args:
            pattern: Design pattern to research
            language: Programming language
            
        Returns:
            Structured research findings
        """
        logger.info(f"Researching design pattern: {pattern} in {language}")
        search_query = f"{pattern} design pattern in {language} implementation example"
        
        try:
            # Search using MCP Server
            search_results = await self.mcp_server.search(search_query)
            
            if "error" in search_results:
                logger.error(f"Error searching for design pattern {pattern}: {search_results['error']}")
                return None
                
            # Summarize search results
            summarize_prompt = f"""
            I need a concise summary of the "{pattern}" design pattern in {language}.
            
            Based on the following search results, provide:
            1. A brief description (1-2 sentences)
            2. When to use this pattern
            3. A code example implementing this pattern in {language}
            4. Benefits and drawbacks
            
            Search results:
            {json.dumps(search_results, indent=2)}
            
            Return your response in JSON format with these fields:
            {{
                "pattern_name": "Name of the design pattern",
                "category": "Creational/Structural/Behavioral",
                "description": "Brief description",
                "when_to_use": "When to use this pattern",
                "code_example": "Example implementation in {language}",
                "benefits": ["benefit1", "benefit2", ...],
                "drawbacks": ["drawback1", "drawback2", ...]
            }}
            """
            
            summary = await self.ai_service.generate_structured_output(summarize_prompt, {
                "type": "object",
                "properties": {
                    "pattern_name": {"type": "string"},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "when_to_use": {"type": "string"},
                    "code_example": {"type": "string"},
                    "benefits": {"type": "array", "items": {"type": "string"}},
                    "drawbacks": {"type": "array", "items": {"type": "string"}}
                }
            })
            
            # Create simplified summary
            simple_summary = f"{pattern} ({summary.get('category', '')}): {summary.get('description', '')}. {summary.get('when_to_use', '')}"
            
            # Create best practice
            best_practice = f"Use the {pattern} pattern when {summary.get('when_to_use', '')}"
            logger.info(f"Design pattern summary: {simple_summary}")
            
            return {
                "topic": pattern,
                "topic_type": "design_pattern",
                "summary": simple_summary,
                "data": best_practice
            }
            
        except Exception as e:
            logger.error(f"Error in _research_design_pattern: {e}")
            return None
    
    async def _research_performance(self, considerations: Any, language: str) -> Dict[str, Any]:
        """Research performance considerations.
        
        Args:
            considerations: Performance considerations to research
            language: Programming language
            
        Returns:
            Structured research findings
        """
        logger.info(f"Researching performance considerations in {language}")
        
        # Convert considerations to a string for search
        if isinstance(considerations, list):
            consideration_str = " ".join(considerations)
        else:
            consideration_str = str(considerations)
            
        search_query = f"{consideration_str} performance optimization in {language} programming"
        
        try:
            # Search using MCP Server
            search_results = await self.mcp_server.search(search_query)
            
            if "error" in search_results:
                logger.error(f"Error searching for performance considerations: {search_results['error']}")
                return None
                
            # Summarize search results
            summarize_prompt = f"""
            I need concise performance optimization tips for {language} based on these considerations: {consideration_str}.
            
            Based on the following search results, provide:
            1. 3-5 key performance optimization techniques
            2. Specific approaches for {language}
            3. Tools or libraries for performance monitoring/optimization
            
            Search results:
            {json.dumps(search_results, indent=2)}
            
            Return your response in JSON format with these fields:
            {{
                "optimization_tips": ["tip1", "tip2", ...],
                "language_specific": ["specific approach 1", "specific approach 2", ...],
                "tools": ["tool1", "tool2", ...]
            }}
            """
            
            summary = await self.ai_service.generate_structured_output(summarize_prompt, {
                "type": "object",
                "properties": {
                    "optimization_tips": {"type": "array", "items": {"type": "string"}},
                    "language_specific": {"type": "array", "items": {"type": "string"}},
                    "tools": {"type": "array", "items": {"type": "string"}}
                }
            })
            
            # Combine tips into a list
            all_tips = []
            
            if "optimization_tips" in summary and isinstance(summary["optimization_tips"], list):
                all_tips.extend(summary["optimization_tips"])
                
            if "language_specific" in summary and isinstance(summary["language_specific"], list):
                all_tips.extend(summary["language_specific"])
            
            # Create simplified summary
            simple_summary = "Performance considerations: " + "; ".join(all_tips[:3]) + "..."
            logger.info(f"Performance summary: {simple_summary}")
            
            return {
                "topic": "performance_optimization",
                "topic_type": "performance",
                "summary": simple_summary,
                "data": all_tips
            }
            
        except Exception as e:
            logger.error(f"Error in _research_performance: {e}")
            return None
    
    async def _research_best_practices(self, language: str) -> Dict[str, Any]:
        """Research best practices for a programming language.
        
        Args:
            language: Programming language
            
        Returns:
            Structured research findings
        """
        logger.info(f"Researching best practices for {language}")
        search_query = f"best practices for {language} programming"
        
        try:
            # Search using MCP Server
            search_results = await self.mcp_server.search(search_query)
            
            if "error" in search_results:
                logger.error(f"Error searching for best practices: {search_results['error']}")
                return None
                
            # Summarize search results
            summarize_prompt = f"""
            I need a concise list of best practices for {language} programming.
            
            Based on the following search results, provide:
            1. 5-8 key best practices for {language}
            2. When each practice should be applied
            
            Search results:
            {json.dumps(search_results, indent=2)}
            
            Return your response in JSON format with these fields:
            {{
                "best_practices": [
                    {{"practice": "description of the best practice", "context": "when to apply it"}}
                ]
            }}
            """
            
            summary = await self.ai_service.generate_structured_output(summarize_prompt, {
                "type": "object",
                "properties": {
                    "best_practices": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "practice": {"type": "string"},
                            "context": {"type": "string"}
                        }
                    }}
                }
            })
            
            # Extract best practices
            best_practices = []
            if "best_practices" in summary and isinstance(summary["best_practices"], list):
                for bp in summary["best_practices"]:
                    if isinstance(bp, dict) and "practice" in bp:
                        practice = bp["practice"]
                        context = bp.get("context", "")
                        
                        if context:
                            best_practices.append(f"{practice} ({context})")
                        else:
                            best_practices.append(practice)
            
            # Create simplified summary
            simple_summary = f"{language} best practices: " + "; ".join(best_practices[:3]) + "..."
            logger.info(f"Best practices summary: {simple_summary}")
            
            return {
                "topic": f"{language}_best_practices",
                "topic_type": "best_practice",
                "summary": simple_summary,
                "data": best_practices
            }
            
        except Exception as e:
            logger.error(f"Error in _research_best_practices: {e}")
            return None
    
    async def _generate_ai_knowledge_research(self, requirements: str, language: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research findings using the AI model's built-in knowledge when web search fails.
        
        Args:
            requirements: Problem requirements
            language: Programming language
            plan: The plan created by the planner agent
            
        Returns:
            Research findings generated from the AI model's knowledge
        """
        logger.info(f"Generating research findings using AI model knowledge for {language}")
        
        # Extract key elements from the plan for context
        problem_analysis = plan.get("problem_analysis", "")
        approach = plan.get("approach", [])
        recommended_libraries = plan.get("recommended_libraries", [])
        algorithms = plan.get("algorithms", [])
        data_structures = plan.get("data_structures", [])
        design_patterns = plan.get("design_patterns", [])
        
        # Format the approach for the prompt
        approach_text = ""
        if isinstance(approach, list):
            approach_text = "\n".join([f"- {step}" for step in approach])
        else:
            approach_text = str(approach)
        
        # Create a comprehensive prompt for the AI
        generate_prompt = f"""
        Based on your knowledge and without using external resources, please provide research information for implementing a solution to this problem:
        
        REQUIREMENTS:
        {requirements}
        
        PROBLEM ANALYSIS:
        {problem_analysis}
        
        APPROACH:
        {approach_text}
        
        TARGET LANGUAGE: {language}
        
        RECOMMENDED LIBRARIES: {', '.join(recommended_libraries) if isinstance(recommended_libraries, list) else str(recommended_libraries)}
        
        ALGORITHMS: {', '.join(algorithms) if isinstance(algorithms, list) else str(algorithms)}
        
        DATA STRUCTURES: {', '.join(data_structures) if isinstance(data_structures, list) else str(data_structures)}
        
        DESIGN PATTERNS: {', '.join(design_patterns) if isinstance(design_patterns, list) else str(design_patterns)}
        
        Please provide the following information:
        1. Detailed information about the recommended libraries (features, use cases, code examples)
        2. Best practices for implementing the solution in {language}
        3. Code examples for key algorithms and data structures
        4. Performance considerations for the approach
        
        Return your response in JSON format with these fields:
        {{
            "libraries": [
                {{
                    "name": "library name",
                    "description": "brief description",
                    "key_features": ["feature1", "feature2"],
                    "usage_example": "code example"
                }}
            ],
            "best_practices": [
                "best practice 1",
                "best practice 2"
            ],
            "code_examples": [
                {{
                    "description": "description of code example",
                    "code": "code implementation"
                }}
            ],
            "summary": {{
                "key_topic1": "summary about topic1",
                "key_topic2": "summary about topic2"
            }}
        }}
        """
        
        try:
            # Generate structured response from AI model
            research_output = await self.ai_service.generate_structured_output(generate_prompt, {
                "type": "object",
                "properties": {
                    "libraries": {
                        "type": "array", 
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "key_features": {"type": "array", "items": {"type": "string"}},
                                "usage_example": {"type": "string"}
                            }
                        }
                    },
                    "best_practices": {"type": "array", "items": {"type": "string"}},
                    "code_examples": {
                        "type": "array", 
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "code": {"type": "string"}
                            }
                        }
                    },
                    "summary": {"type": "object"}
                }
            })
            
            logger.info("Successfully generated research findings using AI knowledge")
            return research_output
            
        except Exception as e:
            logger.error(f"Error generating AI knowledge research: {e}")
            # Return minimal research findings on failure
            return {
                "libraries": [],
                "best_practices": [f"Follow standard {language} programming conventions"],
                "code_examples": [],
                "summary": {}
            }
    
    async def _safe_research_task(self, coro: asyncio.Future, task_name: str) -> Optional[Dict[str, Any]]:
        """Wrap a research coroutine to handle exceptions and prevent task group failures.
        
        Args:
            coro: The coroutine to be executed as a task
            task_name: A string identifier for the task, used in logging
            
        Returns:
            The result of the coroutine, or None if an error occurred
        """
        try:
            result = await coro
            return result
        except Exception as e:
            logger.error(f"Error during research task '{task_name}': {e}")
            return None


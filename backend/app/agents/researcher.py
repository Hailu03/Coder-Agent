"""Researcher Agent module for the Collaborative Coding Agents application.

This module defines the Researcher Agent that gathers information from external sources.
"""

import logging
import json
import re
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional

from .base import Agent
from ..services.ai_service import AIService
from ..services.mcp import WebSearchClient
from ..utils import clean_language_name

# Configure logging
logger = logging.getLogger("agents.researcher")


class ResearchAgent(Agent):
    """Agent responsible for gathering information from external sources."""
    
    def __init__(self, ai_service: AIService, web_search_client: Optional[WebSearchClient] = None):
        """Initialize the Researcher Agent.
        
        Args:
            ai_service: AI service for interacting with language models
            web_search_client: Optional web search client for accessing external information
        """
        super().__init__(name="ResearchAgent", ai_service=ai_service)
        self.web_search_client = web_search_client or WebSearchClient()
    
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
        recommended_libraries = plan.get("recommended_libraries", [])
        algorithms = plan.get("algorithms", [])
        data_structures = plan.get("data_structures", [])
        
        logger.info(f"Researching information for {language} solution")
        
        # Generate research topics based on the plan
        research_topics = []
        
        # Add language-specific topics
        research_topics.append(f"best practices {language} programming")
        
        # Add libraries if available
        for lib in recommended_libraries[:3]:  # Limit to top 3 libraries
            if lib:
                research_topics.append(f"{lib} library {language} examples")
        
        # Add algorithms if available
        for algo in algorithms[:2]:  # Limit to top 2 algorithms
            if algo:
                research_topics.append(f"{algo} algorithm {language} implementation")
        
        # Add data structures if available
        for ds in data_structures[:2]:  # Limit to top 2 data structures
            if ds:
                research_topics.append(f"{ds} {language} implementation")
        
        # Conduct research on the topics
        logger.info(f"Researching topics: {research_topics}")
        
        # Try to gather external information first
        external_research_results = await self._gather_external_information(research_topics, language)
        
        # If external research failed or is incomplete, fall back to AI service
        if not external_research_results or (
            not external_research_results.get("libraries") and 
            not external_research_results.get("algorithms") and
            not external_research_results.get("best_practices")
        ):
            logger.info("External research incomplete, falling back to AI service")
            ai_research_results = await self._gather_ai_research(requirements, language, problem_analysis, research_topics)
            
            # Merge any existing external results with AI results
            merged_research = self._merge_research_results(external_research_results, ai_research_results)
            return merged_research
        
        return external_research_results
    
    async def _gather_external_information(self, research_topics: List[str], language: str) -> Dict[str, Any]:
        """Gather information from external sources using web search.
        
        Args:
            research_topics: List of topics to research
            language: Programming language
            
        Returns:
            Research results from external sources
        """
        try:
            # Initialize the web search client
            await self.web_search_client.initialize()
            
            # Structure to hold all research results
            research_results = {
                "libraries": [],
                "algorithms": [],
                "best_practices": [],
                "code_examples": []
            }
            
            # Process each research topic
            for topic in research_topics:
                logger.info(f"Researching external information for: {topic}")
                
                # Determine the type of topic
                topic_type = self._determine_topic_type(topic, language)
                
                if topic_type == "library":
                    # Extract library name from topic
                    library_name = topic.split()[0]
                    
                    # Get library documentation
                    doc_info = await self.web_search_client.fetch_documentation(library_name, language)
                    
                    # Get code examples
                    examples = await self.web_search_client.fetch_code_examples(f"{library_name} example", language, 2)
                    
                    # Format library information
                    if doc_info:
                        library_info = {
                            "name": library_name,
                            "description": doc_info.get("description", ""),
                            "usage_example": examples[0].get("code", "") if examples else "",
                            "best_practices": [doc_info.get("best_practice", "")]
                        }
                        research_results["libraries"].append(library_info)
                    
                elif topic_type == "algorithm":
                    # Extract algorithm name
                    algorithm_name = topic.split()[0]
                    
                    # Search for algorithm information
                    algorithm_results = await self.web_search_client.search_web(f"{algorithm_name} algorithm explanation {language}")
                    
                    # Get code examples
                    examples = await self.web_search_client.fetch_code_examples(f"{algorithm_name} implementation {language}", language, 1)
                    
                    # Format algorithm information
                    if algorithm_results:
                        algorithm_info = {
                            "name": algorithm_name,
                            "description": algorithm_results[0].get("snippet", "") if algorithm_results else "",
                            "implementation_example": examples[0].get("code", "") if examples else "",
                            "complexity": "O(n)"  # Default, ideally we'd get this from the search results
                        }
                        research_results["algorithms"].append(algorithm_info)
                
                elif topic_type == "best_practice":
                    # Search for best practices
                    best_practice_results = await self.web_search_client.search_web(topic)
                    
                    # Extract best practices
                    if best_practice_results:
                        for result in best_practice_results[:3]:  # Top 3 results
                            practice = result.get("snippet", "")
                            if practice and len(practice) > 20:  # Ensure it's substantial
                                research_results["best_practices"].append(practice)
                
                elif topic_type == "data_structure":
                    # Extract data structure name
                    ds_name = topic.split()[0]
                    
                    # Get code examples
                    examples = await self.web_search_client.fetch_code_examples(f"{ds_name} implementation {language}", language, 2)
                    
                    # Add examples to code_examples section
                    for example in examples:
                        if "code" in example:
                            example_info = {
                                "description": f"{ds_name} implementation in {language}",
                                "code": example.get("code", "")
                            }
                            research_results["code_examples"].append(example_info)
            
            logger.info("External research completed successfully")
            return research_results
            
        except Exception as e:
            logger.error(f"Error gathering external information: {str(e)}")
            return {}
        
        finally:
            # Always close the session when done
            try:
                await self.web_search_client.close()
            except:
                pass
    
    def _determine_topic_type(self, topic: str, language: str) -> str:
        """Determine the type of research topic.
        
        Args:
            topic: Research topic
            language: Programming language
            
        Returns:
            Topic type (library, algorithm, best_practice, or data_structure)
        """
        topic_lower = topic.lower()
        
        if "library" in topic_lower or "package" in topic_lower or "module" in topic_lower:
            return "library"
        elif "algorithm" in topic_lower:
            return "algorithm"
        elif "best practice" in topic_lower or "practices" in topic_lower:
            return "best_practice"
        elif any(ds in topic_lower for ds in ["array", "list", "map", "tree", "graph", "stack", "queue"]):
            return "data_structure"
        else:
            return "general"
    
    async def _gather_ai_research(
        self, requirements: str, language: str, problem_analysis: str, research_topics: List[str]
    ) -> Dict[str, Any]:
        """Use AI service to gather research if external sources are unavailable.
        
        Args:
            requirements: Problem requirements
            language: Programming language
            problem_analysis: Analysis of the problem
            research_topics: Topics to research
            
        Returns:
            Research results from AI
        """
        prompt = f"""
        I'm working on solving the following programming problem:
        
        PROBLEM:
        {requirements}
        
        LANGUAGE: {language}
        
        PROBLEM ANALYSIS:
        {problem_analysis}
        
        I need you to act as a research agent and gather information on the following topics:
        {json.dumps(research_topics, indent=2)}
        
        For each topic, provide:
        1. A brief summary of key information
        2. Best practices or efficient implementations
        3. Code examples when relevant
        4. Links to resources or documentation (if you were able to search the web)
        
        Please structure your response as a JSON object for easy parsing.
        """
        
        # Output schema for structured response
        output_schema = {
            "research_results": {
                "libraries": [{
                    "name": "string",
                    "description": "string",
                    "usage_example": "string",
                    "best_practices": ["string"]
                }],
                "algorithms": [{
                    "name": "string",
                    "description": "string",
                    "implementation_example": "string",
                    "complexity": "string"
                }],
                "best_practices": ["string"],
                "code_examples": [{
                    "description": "string",
                    "code": "string"
                }]
            }
        }
        
        response = await self.generate_structured_output(prompt, output_schema)
        
        if not response or "research_results" not in response:
            logger.warning("Failed to generate structured research, falling back to text generation")
            text_response = await self.generate_text(prompt)
            return {
                "research_findings": text_response,
                "libraries": [],
                "algorithms": [],
                "best_practices": [],
                "code_examples": []
            }
        
        # Return the research results
        return response.get("research_results", {})
    
    def _merge_research_results(self, external_results: Dict[str, Any], ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """Merge research results from external sources and AI service.
        
        Args:
            external_results: Results from external sources
            ai_results: Results from AI service
            
        Returns:
            Merged research results
        """
        merged = {
            "libraries": [],
            "algorithms": [],
            "best_practices": [],
            "code_examples": []
        }
        
        # Helper to merge and deduplicate
        def merge_section(section_name):
            section = []
            seen = set()
            
            # Add external results first
            for item in external_results.get(section_name, []):
                if isinstance(item, dict) and "name" in item:
                    key = item["name"]
                    if key not in seen:
                        section.append(item)
                        seen.add(key)
                elif isinstance(item, str):
                    if item not in seen:
                        section.append(item)
                        seen.add(item)
                else:
                    section.append(item)
            
            # Add AI results if not already present
            for item in ai_results.get(section_name, []):
                if isinstance(item, dict) and "name" in item:
                    key = item["name"]
                    if key not in seen:
                        section.append(item)
                        seen.add(key)
                elif isinstance(item, str):
                    if item not in seen:
                        section.append(item)
                        seen.add(item)
                else:
                    section.append(item)
            
            return section
        
        # Merge each section
        for section in merged.keys():
            merged[section] = merge_section(section)
        
        return merged
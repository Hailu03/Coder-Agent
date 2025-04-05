"""Web Search Client for external data retrieval.

This module provides a client for retrieving external information and resources.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("services.web_search")

class WebSearchClient:
    """Client for searching and retrieving information from external sources."""
    
    def __init__(self, api_key: str = None):
        """Initialize the Web Search client.
        
        Args:
            api_key: Optional API key for search services
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.session = None
        
    async def initialize(self):
        """Initialize the HTTP session for making requests."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
    async def close(self):
        """Close the HTTP session."""
        if self.session is not None:
            await self.session.close()
            self.session = None
    
    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web for information.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with snippets and links
        """
        await self.initialize()
        
        try:
            # Use SerpAPI demo key for demonstration purposes
            # In production, you would want to use a proper API key
            async with self.session.get(
                f"https://serpapi.com/search.json",
                params={
                    "q": query,
                    "api_key": self.api_key or "demo",
                    "num": max_results
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract organic results
                    results = data.get("organic_results", [])
                    
                    # Format results
                    formatted_results = []
                    for result in results[:max_results]:
                        formatted_results.append({
                            "title": result.get("title", ""),
                            "link": result.get("link", ""),
                            "snippet": result.get("snippet", "")
                        })
                    
                    return formatted_results
                else:
                    logger.warning(f"Search request failed with status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching web: {str(e)}")
            return []
    
    async def fetch_documentation(self, library: str, language: str) -> Dict[str, Any]:
        """Fetch documentation for a programming library.
        
        Args:
            library: The library name
            language: The programming language
            
        Returns:
            Documentation information
        """
        await self.initialize()
        
        try:
            # Search for library documentation
            search_results = await self.search_web(f"{library} {language} documentation", 3)
            
            if not search_results:
                return {"description": "", "best_practice": ""}
            
            # Get the first result as main documentation
            doc_info = {
                "description": search_results[0].get("snippet", ""),
                "url": search_results[0].get("link", ""),
                "best_practice": ""
            }
            
            # Try to find best practices
            best_practice_results = await self.search_web(f"{library} {language} best practices", 2)
            if best_practice_results:
                doc_info["best_practice"] = best_practice_results[0].get("snippet", "")
            
            return doc_info
                
        except Exception as e:
            logger.error(f"Error fetching documentation: {str(e)}")
            return {"description": "", "best_practice": ""}
    
    async def fetch_code_examples(self, topic: str, language: str, count: int = 3) -> List[Dict[str, Any]]:
        """Search for code examples.
        
        Args:
            topic: The topic to search for
            language: Programming language
            count: Number of examples to retrieve
            
        Returns:
            List of code examples (simulated)
        """
        await self.initialize()
        
        try:
            # Search for code examples
            search_results = await self.search_web(f"{topic} {language} code example github", count)
            
            examples = []
            for result in search_results:
                # Simulate code examples since we can't directly fetch code from GitHub
                examples.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "code": f"# Example code for {topic} in {language}\n# From: {result.get('link', '')}\n\n# This is a placeholder. In a real implementation, we would fetch actual code.\n"
                })
            
            return examples
                
        except Exception as e:
            logger.error(f"Error fetching code examples: {str(e)}")
            return []
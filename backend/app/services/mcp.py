from mcp.client.sse import sse_client
from mcp import ClientSession
from ..core.config import settings
import logging
import asyncio
import json
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("services.mcp")  

class MCPServer:
    """Client for interacting with the MCP Server."""
    
    def __init__(self, mcp_url: str = None):
        """Initialize the MCP Server client.
        
        Args:
            mcp_url: URL to the MCP server
        """
        self.mcp_url = mcp_url or settings.MCP_URL
        logger.info(f"Initialized MCP Server client with URL: {self.mcp_url}")
        self.connection_validated = False
    
    async def validate_connection(self) -> bool:
        """Validates that the MCP server is reachable.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Attempt to connect to MCP server
            async with sse_client(url=self.mcp_url, headers=None, timeout=5) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    if tools and hasattr(tools, 'tools') and any(t.name == "search" for t in tools.tools):
                        self.connection_validated = True
                        return True
                    else:
                        logger.warning("MCP server connected but search tool not found")
                        return False
        except (asyncio.TimeoutError, ConnectionRefusedError) as e:
            logger.error(f"MCP server connection timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating MCP server connection: {e}")
            return False
    
    async def search(self, query: str) -> Dict[str, Any]:
        """Search web using Serper API via MCP Server.
        
        Args:
            query: Search query string
            
        Returns:
            JSON response from Serper API or fallback response
        """
        # First validate connection if needed
        if not self.connection_validated:
            connection_ok = await self.validate_connection()
            if not connection_ok:
                return self._create_fallback_response(query)
                
        try:
            # Connect to MCP server via SSE transport with timeout
            async with sse_client(url=self.mcp_url, headers=None, timeout=10) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    # Call search tool
                    logger.info(f"Calling MCP search with query: '{query}'")
                    result = await asyncio.wait_for(
                        session.call_tool("search", {"query": query, "api_key": settings.SERPER_API_KEY}),
                        timeout=15
                    )
                    # Parse JSON result
                    if isinstance(result, str):
                        try:
                            return json.loads(result)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON response from MCP search: {result[:100]}...")
                            return self._create_fallback_response(query)
                    # Xử lý đối tượng CallToolResult không phải string
                    elif hasattr(result, 'json') and callable(getattr(result, 'json')):
                        # Nếu đối tượng có phương thức json(), gọi nó
                        return result.json()
                    elif hasattr(result, '__dict__'):
                        # Nếu đối tượng có __dict__, chuyển đổi thành dictionary
                        return result.__dict__
                    else:
                        # Cuối cùng, thử chuyển đổi object thành string rồi parsing
                        try:
                            return json.loads(json.dumps(result, default=lambda o: f"{o.__class__.__name__}"))
                        except:
                            logger.error(f"Cannot convert result to JSON: {type(result)}")
                            return self._create_fallback_response(query)
        except asyncio.TimeoutError:
            logger.error(f"Timeout while searching with MCP Server for query: '{query}'")
            return self._create_fallback_response(query)
        except Exception as e:
            logger.error(f"Error searching with MCP Server for query: '{query}': {e}")
            return self._create_fallback_response(query)
            
    def _create_fallback_response(self, query: str) -> Dict[str, Any]:
        """Create a fallback response when search fails.
        
        Args:
            query: The original search query
            
        Returns:
            A minimal response with the search query
        """
        logger.info(f"Creating fallback response for query: '{query}'")
        return {
            "searchParameters": {
                "q": query
            },
            "organic": [
                {
                    "title": f"Fallback result for: {query}",
                    "snippet": f"The search for '{query}' could not be completed. Using built-in knowledge instead."
                }
            ]
        }
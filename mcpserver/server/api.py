"""
MCP (Model Context Protocol) server implementation for the FPT Telecom chatbot.
This server exposes tools that can be called by OpenAI Agents to access data and functionality.
"""

from mcp.server.fastmcp import FastMCP
import os
import logging
from firecrawl import AsyncFirecrawlApp
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("mcpserver")

# Removed dotenv usage; API key will be passed by agent


class MCPTools:
    """MCP Tools implementation for the FPT Telecom chatbot."""

    def __init__(self):
        # Initialize FastMCP
        self.mcp = FastMCP("MCP API Server", port=9000)
        self.firecrawl_app = AsyncFirecrawlApp(
            api_key=os.getenv("FIRECRAWL_API_KEY"),
        )

        try:
            # Register tools
            self._register_tools()
            logger.info("MCP Tools initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MCP Tools: {str(e)}")
            raise    
        
    def _register_tools(self):
        @self.mcp.tool()
        async def search(query: str, limit: int = 3) -> dict:
            """
            Search for a query using the Firecrawl API.
            Args:
                query (str): The search query.
                limit (int): Number of results to return (default: 3).
            Returns:
                dict: The search results with title, description, and URL.
            """
            try:
                logger.info(f"Searching with Firecrawl: '{query}' (limit: {limit})")
                response = await self.firecrawl_app.search(query=query, limit=limit)
                # Format response already handled by Firecrawl SDK
                return response
            except Exception as e:
                logger.error(f"Error in search tool: {str(e)}")
                return {
                    "success": False,
                    "data": [],
                    "error": str(e)
                }

    def run_server(self, transport="sse", port=9000): # Giữ port ở đây để logging nếu muốn
        """
        Run the MCP server.
        Args:
            transport (str): Transport protocol to use (sse or websockets)
            port (int): Port the server is intended to run on (used for logging)
        """
        logger.info(f"Starting MCP server with {transport} transport on port {port}")
        # Chỉ truyền tham số transport vì run() không nhận port và path
        self.mcp.run(transport=transport)

def main():
    """Main function to run the MCP server."""
    try:
        mcp_tools = MCPTools()
        port = int(os.getenv("MCP_PORT", 9000))
        transport = os.getenv("MCP_TRANSPORT", "sse")
        mcp_tools.run_server(transport=transport, port=port)
    except Exception as e:
        logger.critical(f"Failed to start MCP server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
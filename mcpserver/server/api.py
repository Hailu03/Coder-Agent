"""
MCP (Model Context Protocol) server implementation for the FPT Telecom chatbot.
This server exposes tools that can be called by OpenAI Agents to access data and functionality.
"""

from mcp.server.fastmcp import FastMCP
import os
import http.client
import json
import logging

logger = logging.getLogger("mcpserver")

# Removed dotenv usage; API key will be passed by agent


class MCPTools:
    """MCP Tools implementation for the FPT Telecom chatbot."""

    def __init__(self):
        # Initialize FastMCP
        self.mcp = FastMCP("MCP API Server", port=9000)

        try:
            # Register tools
            self._register_tools()
            logger.info("MCP Tools initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MCP Tools: {str(e)}")
            raise

    def _register_tools(self):
        @self.mcp.tool()
        def search(query: str, api_key: str) -> str:
            """
            Search tool using Serper API.
            Args:
                query (str): The search query.
                api_key (str): The API key for Serper API.
            Returns:
                str: The search results in JSON format.
            """
            logger.info(f"Search tool called with query: {query}")
            if not api_key:
                raise ValueError("API key is required for the search tool.")
            conn = http.client.HTTPSConnection("google.serper.dev")

            payload = json.dumps({
                "q": query
            })
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }

            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")

            print(data)

            return data

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
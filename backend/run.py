"""Entry point script for running the FastAPI application.

This script is used to start the FastAPI server from the command line.
"""

import uvicorn
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run")

def main():
    """Run the FastAPI application using uvicorn."""
    logger.info("Starting Collaborative Coding Agents API server")
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main()
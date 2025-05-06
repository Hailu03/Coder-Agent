"""Entry point for the backend application.

This script starts the ASGI server with the FastAPI app.
"""

import os
import uvicorn

from app.main import app

if __name__ == "__main__":
    # Use environment variables for host and port if available
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting server at {host}:{port}")
    uvicorn.run(app, host=host, port=port)
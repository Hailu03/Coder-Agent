# Backend Service

This folder contains the FastAPI backend service for the Collaborative Coding Agents project.

## Overview

The backend service is responsible for:
- User authentication and management
- Orchestrating the collaborative agent system
- Processing code generation requests
- Managing application settings
- Communicating with AI services (Gemini/OpenAI)
- Communicating with the MCP server for extended functionality

## Directory Structure

- `app/`: Main application package
  - `agents/`: Agent implementations for different roles
    - `planner.py`: Planning and problem analysis agent
    - `researcher.py`: Information gathering agent
    - `developer.py`: Code generation agent
    - `tester.py`: Code testing and validation agent
  - `api/`: API route definitions
    - `v1/`: API version 1 endpoints
      - `auth.py`: Authentication endpoints
      - `settings.py`: Settings management endpoints
      - `solve.py`: Code generation endpoints
  - `auth/`: Authentication-related utilities
  - `core/`: Core functionality
    - `config.py`: Application configuration
    - `orchestrator.py`: Agent orchestration logic
  - `db/`: Database models and utilities
  - `models/`: Pydantic models for request/response handling
  - `services/`: External service integrations
    - `ai_service.py`: AI model integration
    - `mcp.py`: MCP server communication
  - `utils/`: Utility functions and helpers

## Setup and Configuration

1. Create a `.env` file in this directory with the following content:

```
# AI Provider: "gemini" or "openai"
AI_PROVIDER=gemini

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Other configurations
PROJECT_NAME="Coder-Agent"

# JWT Secret (for user authentication)
SECRET_KEY=your_secret_key_for_jwt_encryption
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

## Development

The backend server will be available at http://localhost:8000 by default, with the API documentation at http://localhost:8000/docs.

### Key Files

- `run.py`: Entry point for the application
- `app/main.py`: FastAPI application setup and configuration
- `app/core/orchestrator.py`: Manages the workflow between agents
- `app/api/v1/*.py`: API endpoint definitions

## Authentication System

The backend implements JWT-based authentication:
- Users must register and login to access protected features
- Authentication tokens are managed via bearer tokens
- Protected endpoints include settings management and problem-solving
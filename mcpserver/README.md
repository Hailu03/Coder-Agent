# MCP Server (Model Context Protocol)

This folder contains the Model Context Protocol server for the Collaborative Coding Agents project.

## Overview

The MCP (Model Context Protocol) server provides extended functionality for the AI agents, including:
- Web search capabilities via Firecrawl API
- Integration with external data sources
- Standardized communication protocol for agents

## Directory Structure

- `server/`: Server implementation
  - `api.py`: API endpoints and services
- `run.py`: Server entry point
- `requirements.txt`: Python dependencies
- `pyproject.toml`: Project configuration
- `uv.lock`: Dependency lock file

## Setup and Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python run.py
```

The MCP server will be available at http://localhost:9000 by default.

## Configuration

The MCP server now receives necessary configuration from the main backend service, so separate environment variables are no longer required. This simplifies deployment and ensures consistent configuration throughout the system.

## Key Features

### Web Search Integration
- Allows agents to search the web for code examples, documentation, and other relevant information
- Returns structured search results that can be easily parsed by the agents

### Standardized Communication Protocol
- Defines a standard way for agents to request and receive information
- Enables extensible architecture where new services can be added without modifying agent code

### Support for Research Agent
- Provides rich context for the Research Agent to gather information
- Helps find relevant libraries, code examples, algorithms, and best practices

## Development

The MCP server is designed to be lightweight and extensible. New capabilities can be added by implementing additional endpoints in the `server/api.py` file.
# Collaborative Coding Agents

Collaborative Coding Agents is an application that uses artificial intelligence (AI) to automatically generate programming solutions through the coordination of specialized agents. The system leverages AI models to analyze, research, and generate code based on user requirements.

![alt](image/app.png)

## System Architecture

The system consists of three main components:

### Backend (FastAPI)

- **Agents**: Specialized agents including:
  - `PlannerAgent`: Analyzes problems and creates solution plans
  - `ResearchAgent`: Researches relevant information from the web and external sources
  - `DeveloperAgent`: Generates source code based on plans and research
  - `TesterAgent`: Evaluates and tests code quality

- **Orchestrator**: Coordinates the workflow between agents
- **AI Service**: Communicates with AI model APIs (Gemini, OpenAI)
- **API**: Provides endpoints to interact with the system

### MCP Server (Model Context Protocol)

- Provides a protocol for agents to communicate with external services
- Integrates Serper API for web search capabilities
- Allows agents to access data and extended functionality

### Frontend (React + TypeScript)

- User interface built with React and TypeScript
- Connects to the backend via REST API
- Displays analysis results, solution plans, and source code

## Key Features

- Analysis of programming requirements
- Problem-solving planning
- Web-based research for relevant information
- Source code generation for multiple programming languages
- Configuration and selection of AI models
- Testing and code optimization
- User authentication system
- Settings management for API configurations

## Installation and Running with Docker

### Requirements

- Docker and Docker Compose
- API keys for AI services (Gemini or OpenAI)
- Serper API key for web search functionality (optional)

### Configuration

Create a `.env` file in the `backend` directory with the following content:

```
# AI Provider: "gemini" or "openai"
AI_PROVIDER=gemini

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Other configurations
PROJECT_NAME="Coder-Agent"

# JWT Secret (for user authentication)
SECRET_KEY=your_secret_key_for_jwt_encryption
```

### Starting with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/Hailu03/collaborative-coding-agents.git
cd collaborative-coding-agents
```

2. Run the application:
```bash
docker-compose up -d
```

3. Access the application at:
   - Frontend: http://localhost:80
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MCP Server: http://localhost:9000

### Stopping the Application

```bash
docker-compose down
```

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### MCP Server Development

```bash
cd mcpserver
pip install -r requirements.txt
python run.py
```

## API Endpoints

### Solve Endpoints
- `POST /api/v1/solve`: Submit a problem-solving request
- `GET /api/v1/solve/task/{task_id}`: Check the status of a task
- `POST /api/v1/solve/task/{task_id}/cancel`: Cancel a running task

### Settings Endpoints
- `POST /api/v1/settings`: Update system settings
- `GET /api/v1/settings`: Get current settings information

### Authentication Endpoints
- `POST /api/v1/auth/login`: User login
- `POST /api/v1/auth/register`: User registration
- `GET /api/v1/auth/me`: Get current user information
- `PUT /api/v1/auth/me`: Update user information

## User Authentication

The system now requires user authentication for accessing important features:
- User registration and login are required
- Settings can only be accessed by authenticated users
- The Solve page requires login before accessing

## Project Structure

- `backend/`: FastAPI backend server
- `frontend/`: React frontend application
- `mcpserver/`: Model Context Protocol server
- `image/`: Project images and screenshots

Each folder contains its own README file with detailed information about its contents and purpose.

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check API keys in the .env file
   - Ensure the backend is running and port 8000 is not blocked
   - Verify that you're logged in for accessing protected endpoints

2. **Container Not Starting**
   - Check logs: `docker-compose logs`
   - Ensure no services are occupying ports 80, 8000, or 9000

3. **CORS Errors**
   - Check the BACKEND_CORS_ORIGINS configuration in docker-compose.yml

4. **Memory or TaskGroup Errors**
   - Increase memory limits for containers in docker-compose.yml
   - Set the environment variable LOW_MEMORY_MODE=true

5. **Authentication Issues**
   - Clear browser local storage if login/logout issues persist
   - Check if JWT token is being properly stored and sent with requests

## Contributing

Contributions are welcome. Please create an issue or pull request with any improvements.

## License

[MIT License](LICENSE)
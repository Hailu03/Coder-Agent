# Collaborative Coding Agents

Collaborative Coding Agents is an application that uses AI to automatically generate programming solutions through the coordination of specialized agents. The system leverages AI models to analyze, research, and generate code based on user requirements.

## System Architecture

The system consists of two main components:

### Backend (FastAPI)

- **Agents**: Specialized agents including:
  - `PlannerAgent`: Analyzes problems and creates solution plans
  - `ResearchAgent`: Researches relevant information
  - `CodeGeneratorAgent`: Generates source code based on plans and research

- **Orchestrator**: Coordinates the workflow between agents
- **AI Service**: Communicates with AI model APIs (Gemini, OpenAI)
- **API**: Provides endpoints to interact with the system

### Frontend (React + TypeScript)

- User interface built with React and TypeScript
- Connects to the backend via REST API
- Displays analysis results, solution plans, and source code

## Key Features

- Analysis of programming requirements
- Problem-solving planning
- Research of relevant information
- Source code generation for multiple programming languages
- Configuration and selection of AI models

## Installation and Running with Docker

### Requirements

- Docker and Docker Compose
- API keys for AI services (Gemini or OpenAI)
- (Optional) Serper API key for web search functionality

### Configuration

1. Create a `.env` file in the `backend` directory with the following content:

```
# AI Provider: "gemini" or "openai"
AI_PROVIDER=gemini

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Other configurations
PROJECT_NAME="Collaborative Coding Agents"
```

### Starting with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/your-username/collaborative-coding-agents.git
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

## API Endpoints

- `POST /api/v1/solve`: Submit a problem-solving request
- `GET /api/v1/solve/task/{task_id}`: Check the status of a task
- `POST /api/v1/solve/task/{task_id}/cancel`: Cancel a running task
- `POST /api/v1/settings`: Update system settings
- `GET /api/v1/settings`: Get current settings information

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check API keys in the .env file
   - Ensure the backend is running and port 8000 is not blocked

2. **Container Not Starting**
   - Check logs: `docker-compose logs`
   - Ensure no services are occupying ports 80 or 8000

3. **CORS Errors**
   - Check the BACKEND_CORS_ORIGINS configuration in docker-compose.yml

## Contributing

Contributions are welcome. Please create an issue or pull request with any improvements.

## License

[MIT License](LICENSE)
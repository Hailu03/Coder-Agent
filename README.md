# Collaborative Coding Agents System

An advanced multi-agent AI system designed to solve programming challenges through intelligent coordination between specialized agents. The system uses a sophisticated 5-phase workflow where agents share information, iteratively improve solutions, and generate high-quality code with comprehensive testing and documentation.

<img src="image/app.png" alt="alt" width="700"/>

## 🚀 Key Features

### Multi-Agent Collaboration System
- **5 Specialized AI Agents**: PlannerAgent, ResearcherAgent, DeveloperAgent, TesterAgent, and DocumenterAgent
- **Intelligent Orchestration**: Coordinated workflow with phase-by-phase execution and progress tracking
- **Inter-Agent Collaboration**: Agents share information and collaborate to improve solutions for optimal results
- **Iterative Improvement**: Automatic code enhancement through multi-agent feedback loops

### Sophisticated Workflow Engine
- **5-Phase Problem Solving**: Planning → Research → Code Generation → Testing → Code Improvement
- **Real-time Progress Tracking**: Phase-by-phase status updates with detailed progress indicators
- **AI-Generated Test Cases**: Automated test case generation from requirement analysis
- **Code Improvement Loops**: Up to 3 automatic improvement iterations based on test results and agent feedback

### Integrated Development Environment
- **IDE-like Interface**: Modern, responsive interface with resizable panels and integrated terminal
- **Rich Text Editor**: TipTap editor with rich text formatting and comprehensive toolbar
- **Code Execution Environment**: Safe, isolated code execution with comprehensive error handling
- **Multi-language Support**: Supports Python, JavaScript, TypeScript, Java, C++, and other languages
- **Solution History**: Storage and management of previously solved problems

## 🤖 Specialized AI Agents

The system employs 5 specialized AI agents, each designed for specific aspects of the software development lifecycle:

### 1. PlannerAgent 📋
**Role**: Problem Analysis & Solution Planning
- **Requirements Analysis**: Analyzes and understands programming problem requirements
- **Algorithm Identification**: Identifies optimal algorithms, data structures, and design patterns
- **Implementation Strategy**: Creates high-level approach with detailed step-by-step execution
- **Edge Case Handling**: Considers special cases and potential challenges
- **Library Recommendations**: Suggests appropriate libraries and frameworks for target language

**Output**: Structured JSON with problem_analysis, approach, recommended_libraries, data_structures, algorithms, design_patterns, edge_cases, performance_considerations

### 2. ResearcherAgent 🔍
**Role**: Information Gathering & External Research
- **Library Research**: Detailed investigation of recommended libraries and frameworks
- **Best Practices**: Collects implementation patterns and best practices for target language
- **Algorithm Research**: Studies algorithms, data structures, and design patterns
- **Code Examples**: Provides code examples and usage patterns from external sources
- **MCP Integration**: Integrates with MCP server for advanced web search via FireCrawl API

**Output**: Detailed research findings with examples and implementation guidelines

### 3. DeveloperAgent 💻
**Role**: Code Generation & Implementation
- **Optimized Code Generation**: Creates clean, optimized, production-ready code
- **Solution Implementation**: Implements solutions based on planning and research results
- **File Structure**: Creates appropriate file structures for complex multi-file projects
- **Error Handling**: Implements error handling and edge case management
- **Agent Collaboration**: Works with other agents to refine and improve code quality

**Output**: Complete source code with explanation, libraries, best_practices, and file_structure

### 4. TesterAgent 🧪
**Role**: Test Generation & Code Validation
- **Automated Test Case Generation**: Automatically creates comprehensive test cases from requirements
- **Test Execution**: Executes tests in secure, isolated environments
- **Functionality Validation**: Validates code functionality against expected outputs
- **Results Reporting**: Provides detailed test results with pass/fail status
- **Multi-language Support**: Supports multiple programming languages with appropriate test frameworks

**Output**: Test results with passed status, test_output, execution_details, and error handling

### 5. DocumenterAgent 📚
**Role**: Documentation Generation
- **Comprehensive Documentation**: Creates detailed documentation for generated solutions
- **Code Structure**: Documents code structure, implementation details, and usage instructions
- **API Documentation**: Generates API documentation and code comments
- **Setup Guides**: Provides setup and installation guides for complex projects

**Output**: Structured Markdown documentation with problem_overview, solution_architecture, implementation_details, usage_guide

## 🔄 5-Phase Collaborative Workflow
The system implements a sophisticated 5-phase workflow where agents collaborate to create optimal solutions:

<img src="image/agent.png" alt="alt" width="500"/>

### Phase 1: Planning & Analysis (10-25%)
- **Primary Agent**: PlannerAgent
- **Activities**: 
  - Analyze problem requirements and constraints
  - Identify optimal algorithms and data structures
  - Create detailed step-by-step approach
  - Define performance considerations and edge cases
  - Provide appropriate library and framework recommendations

### Phase 2: Research & Information Gathering (25-45%)
- **Primary Agent**: ResearcherAgent
- **Activities**:
  - Research recommended libraries and frameworks
  - Collect best practices and implementation patterns
  - Find code examples and usage documentation
  - Analyze performance characteristics and trade-offs
  - Integrate with MCP server for web search through FireCrawl API

### Phase 3: Code Generation & Implementation (45-70%)
- **Primary Agent**: DeveloperAgent
- **Activities**:
  - Generate clean, optimized code based on planning and research
  - Create appropriate file structures for complex projects
  - Implement error handling and edge case management
  - Apply language-specific best practices and patterns

### Phase 4: Test Execution & Validation (70-80%)
- **Primary Agent**: TesterAgent
- **Activities**:
  - Generate comprehensive test cases from requirements
  - Execute tests in secure, isolated environments
  - Validate code functionality and performance
  - Report test results and identify potential issues

### Phase 5: Code Improvement & Collaboration (80-100%)
- **All Agents**: Collaborative improvement process
- **Activities**:
  - Agents share insights and feedback on generated solutions
  - Iterative code improvement based on test results and agent analysis
  - Up to 3 automatic improvement cycles for optimal code quality
  - Final validation and quality assurance

### System Architecture
📋Planning
The system follows a sophisticated microservices architecture with intelligent agent orchestration:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Frontend (React TypeScript)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Problem Solver │  │ Rich Text Editor│  │    Progress Tracker     │  │
│  │   Interface     │  │   (TipTap)      │  │   (5-Phase Workflow)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │     Backend (FastAPI)     │
                    │  ┌─────────────────────┐  │
                    │  │   RESTful API       │  │ ◄──── API endpoints
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │   Task Manager      │  │ ◄──── Task Management
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │ Agent Orchestrator  │  │ ◄──── Main Coordinator
                    │  └─────────────────────┘  │ 
                    └─────────────│─────────────┘              
                                  │
┌───────────────────────────────────────────────────────────────────────┐
│                               Base Agent                              │
│    ┌─────────────────┐ ┌────────────────────────┐ ┌────────────────┐  │
│    │  PlannerAgent   │ │    ResearcherAgent     │ │ DeveloperAgent │  │ 
│    └─────────────────┘ └────────────────────────┘ └────────────────┘  │
│    ┌────────────────┐ ┌─────────────────────────┐ ┌────────────────┐  │
│    │   TesterAgent  │ │    DocumenterAgent      │ │   ChatAgent    │  │
│    └────────────────┘ └─────────────────────────┘ └────────────────┘  │
└──────────────────────────────────│────────────────────────────────────┘
                                   │
                                   │
                     ┌─────────────▼─────────────┐
                     │      MCP Server           │
                     │ (Model Context Protocol)  │
                     │    + FireCrawl API        │
                     └───────────────────────────┘
```

### Frontend Layer (React + TypeScript)
- **IDE-like Interface**: Resizable panels, integrated terminal, and conversation sidebar
- **Real-time Progress Tracking**: Live updates of the 5-phase workflow process
- **Rich Text Editor**: TipTap editor with comprehensive formatting toolbar
- **Code Execution Environment**: Integrated terminal with syntax highlighting and error display
- **Responsive Design**: Adaptive layout supporting multiple screen sizes

<img src="image/solvepage.png" alt="alt" width="700"/>

<img src="image/resultpage.png" alt="alt" width="700"/>

### Backend Layer (FastAPI + SQLAlchemy)
- **Agent Orchestrator**: Central coordination system managing the 5-phase collaborative workflow
- **RESTful API**: Comprehensive endpoints for task management, conversation handling, and system configuration
- **SQLAlchemy ORM**: Database integration with powerful ORM framework
- **Task Management**: Asynchronous task handling with detailed status tracking
- **SSE (Server-Sent Events)**: Real-time communication with automatic reconnection

### Agent Runtime Layer (MCP Server)
- **Model Context Protocol**: Standardized communication interface for AI agents
- **FireCrawl Integration**: Advanced web search capabilities for ResearcherAgent
- **Secure Code Execution**: Safe, isolated environment for testing and validation
- **Tool Integration**: Extensible toolkit for web search, file operations, and external APIs

## 🛠️ Technology Stack

### Frontend
- **React 18** với TypeScript
- **Material-UI (MUI)** cho component library
- **TipTap Editor** cho rich text editing
- **Vite** cho build tool và hot reload
- **React Router** cho navigation
- **Axios** cho HTTP API calls

### Backend  
- **FastAPI** với WebSocket support
- **SQLAlchemy** cho database ORM
- **MySQL/PostgreSQL** làm primary database
- **Pydantic** cho data validation
- **Python 3.11+** runtime
- **Server-Sent Events (SSE)** cho real-time updates

### AI Services
- **OpenAI GPT Models** (GPT-4/GPT-3.5-turbo)
- **Google Gemini** (alternative AI provider)
- **Model Context Protocol (MCP)** cho agent communication

### Infrastructure
- **Docker & Docker Compose** cho containerization
- **FireCrawl API** cho web search capabilities
- **Git** cho version control

## 📦 Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd collaborative-coding-agents
```

2. **Set up environment variables**
```bash
# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit the .env files with your configuration
```

3. **Start the services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
# On Linux/Mac: source venv/bin/activate
# On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up MySQL database
alembic upgrade head

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### MCP Server Setup
```bash
cd mcpserver
python -m venv venv
# On Linux/Mac: source venv/bin/activate
# On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the MCP server
python server.py
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Google Gemini API Configuration  
GEMINI_API_KEY=your-gemini-api-key

# Database Configuration
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname

# Application Settings
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:9000

# FireCrawl API for web search
FIRECRAWL_API_KEY=your-firecrawl-api-key
```

#### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### Database Configuration
The system uses MySQL as the primary database with the following key tables:
- `conversations`: Store conversation metadata
- `messages`: Store individual messages with metadata
- `tasks`: Store task execution metadata and status
- `agents`: Store agent configurations

**Note**: While PostgreSQL is also supported, MySQL is the recommended database for optimal performance and compatibility.

### AI Services Configuration
The system supports multiple AI service providers:
- **OpenAI GPT**: GPT-4, GPT-3.5-turbo models
- **Google Gemini**: Alternative AI provider for diverse responses
- **MCP Server**: Model Context Protocol for agent communication

## 📡 API Reference

### REST Endpoints

#### Conversations
- `GET /api/v1/conversations` - List all conversations
- `POST /api/v1/conversations` - Create new conversation
- `GET /api/v1/conversations/{id}` - Get conversation with messages
- `PUT /api/v1/conversations/{id}` - Update conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation

#### Messages
- `POST /api/v1/conversations/{id}/messages` - Add message to conversation
- `GET /api/v1/messages/{id}` - Get specific message

#### Health & Status
- `GET /health` - System health check
- `GET /api/v1/status` - Service status

### WebSocket Events

#### Client → Server
```json
{
  "type": "user_message",
  "conversation_id": "uuid",
  "content": "message content",
  "metadata": {}
}
```

#### Server → Client
```json
{
  "type": "agent_response",
  "conversation_id": "uuid",
  "agent_id": "agent_name",
  "content": "response content",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00+07:00",
    "message_type": "text"
  }
}
```

## 🎨 UI Components

### Main Interface
- **Header**: Navigation and system status
- **Conversation Sidebar**: List of conversations with search/filter
- **Main Chat Area**: Message display with agent identification
- **Code Executor**: IDE-style code editor with integrated terminal

### Key UI Features
- **Resizable Panels**: Drag to resize code editor and terminal
- **Syntax Highlighting**: Full syntax highlighting for multiple languages
- **Auto-scrolling**: Smart scrolling behavior for chat and terminal
- **Responsive Design**: Works on desktop and tablet devices
- **Dark/Light Theme**: Theme support (configurable)

## 🔍 Troubleshooting

### Common Issues

#### WebSocket Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws
```

#### Database Connection Issues
```bash
# Check if MySQL container is running
docker ps | grep mysql

# Test MySQL database connection
mysql -h localhost -P 3306 -u user -p dbname

# Or using Docker exec
docker exec -it mysql-container mysql -u user -p
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check
```

### Logging
- Backend logs: Check Docker logs or console output
- Frontend logs: Check browser developer console
- Database logs: Check MySQL logs in Docker container

### Performance Issues
- Monitor WebSocket connection count
- Check database query performance
- Verify memory usage in containers

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Run end-to-end tests
npm run test:e2e
```

## 🚀 Deployment

### Production Deployment
1. **Set production environment variables**
2. **Build production images**
```bash
docker-compose -f docker-compose.prod.yml build
```

3. **Deploy with Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-specific Configurations
- **Development**: Hot reload, debug logging
- **Staging**: Production-like with debug access
- **Production**: Optimized builds, error logging only

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test thoroughly
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

### Code Standards
- **TypeScript**: Strict mode enabled
- **Python**: PEP 8 compliance with Black formatting
- **Testing**: Minimum 80% coverage for new features
- **Documentation**: Update README for significant changes

### Commit Message Format
```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation
- style: formatting
- refactor: code restructuring
- test: adding tests
- chore: maintenance
```

## 📋 Changelog

### v1.0.0 (Current)
- ✅ 5 Specialized AI Agents (PlannerAgent, ResearcherAgent, DeveloperAgent, TesterAgent, DocumenterAgent)
- ✅ 5-Phase collaborative workflow with automatic code improvement
- ✅ Agent Orchestrator for intelligent workflow coordination
- ✅ MCP Server integration with FireCrawl API for web search
- ✅ React/TypeScript frontend with TipTap rich text editor
- ✅ FastAPI backend with SQLAlchemy ORM
- ✅ Multi-language programming support (Python, JavaScript, Java, C++, etc.)
- ✅ Automated test execution with isolated environments
- ✅ Complex project file structure generation
- ✅ Iterative code improvement system (up to 3 iterations)
- ✅ Docker containerization for all services
- ✅ MySQL database with optimized performance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review API documentation at `/docs` endpoint

## 🔮 Future Roadmap

- [ ] Advanced agent coordination algorithms
- [ ] Plugin system for custom agents
- [ ] Enhanced code analysis and suggestions
- [ ] Team collaboration features
- [ ] Mobile application support
- [ ] Advanced debugging tools
- [ ] Integration with popular IDEs
- [ ] Cloud deployment options

---

**Built with ❤️ for the developer community**

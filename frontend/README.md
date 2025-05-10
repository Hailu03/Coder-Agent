# Frontend Application

This folder contains the React + TypeScript frontend application for the Collaborative Coding Agents project.

## Overview

The frontend provides a user-friendly interface for:
- User registration and authentication
- Problem description submission
- Programming language selection
- Visualization of solution generation process
- Displaying generated code with syntax highlighting
- Viewing code analysis and explanations
- Managing AI provider settings

## Directory Structure

- `src/`: Source code directory
  - `components/`: Reusable UI components
    - `Header.tsx`: Application header with navigation and user controls
    - `Footer.tsx`: Application footer
  - `pages/`: Page components
    - `HomePage.tsx`: Landing page
    - `LoginPage.tsx`: User authentication page
    - `SolvePage.tsx`: Problem submission and solution generation
    - `ResultPage.tsx`: Display solution and analysis
    - `NotFoundPage.tsx`: 404 error page
  - `services/`: API communication services
    - `apiService.ts`: Backend API client implementation
  - `utils/`: Utility functions
  - `App.tsx`: Main application component
  - `main.tsx`: Application entry point

## Setup and Development

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:5173 by default.

## Building for Production

```bash
npm run build
```

The build output will be in the `dist` directory.

## Key Features

### User Authentication
- Registration and login system
- Protected routes for authenticated users
- User profile management

### Problem Solving Interface
- Rich text editor for describing programming problems
- Support for multiple programming languages
- Real-time progress tracking of the solution generation process

### Solution Visualization
- Syntax-highlighted code display
- Downloadable solution code
- Detailed analysis with tabs for:
  - Code explanation
  - Libraries and dependencies used
  - Performance considerations
  - Best practices followed
  - Recommended file structure

### Settings Management
- AI provider configuration (Gemini/OpenAI)
- API key management
- Theme switching (dark/light mode)

## Authentication Requirements

The frontend implements authentication protection for:
- Settings page: Only logged-in users can access and modify settings
- Solve page: Authentication required before submitting coding problems

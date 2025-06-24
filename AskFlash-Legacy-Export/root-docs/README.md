# AskFlash

AskFlash is an intelligent AI assistant tool designed for internal company use, combining documentation search, AI assistance, and system monitoring capabilities.

## Features

- **Documentation Integration**
  - Seamless integration with documentation platforms (Notion, Azure DevOps Wiki, GitHub Wiki)
  - Smart search through company-specific documentation
  - External information integration to enhance documentation
  - Link and summary generation for relevant documentation

- **AI-Powered Assistance**
  - Integration with AI models (e.g., ChatGPT) for intelligent responses
  - Customizable ruleset and context management
  - Prompt interpretation layer for refined search and response generation
  - Company-specific response guidelines

- **System Monitoring**
  - Dynatrace integration for system stability queries
  - Log analysis and interpretation
  - Real-time system status monitoring

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL
- **AI Integration**: OpenAI API
- **Documentation Integration**: 
  - Notion API
  - Azure DevOps API
  - GitHub API
- **Monitoring**: Dynatrace API

## Project Structure

```
askflash/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements-base.txt    # Core Python dependencies
  └── requirements-features.txt   # Feature-specific dependencies (Teams bot)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
│   └── package.json       # Node dependencies
└── docker/                # Docker configuration
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Docker (optional)

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements-base.txt
pip install -r requirements-features.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the frontend:
   ```bash
   npm start
   ```

## Configuration

The following services need to be configured:

1. OpenAI API key for AI assistance
2. Notion API integration
3. Azure DevOps API integration
4. GitHub API integration
5. Dynatrace API integration
6. Database connection

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Docker Build Performance

The project includes multiple Docker build strategies optimized for different use cases:

### Build Options

1. **Poetry Build** (Recommended - Single Source of Truth):
   ```bash
   # Local Development (fast builds with hot reload)
   docker-compose up --build
   
   # Production (optimized and secure)
   docker-compose -f docker-compose.poetry.yml up --build
   ```
   - **Development target**: Fast builds, hot reload, debug logging
   - **Production target**: Optimized, secure, health checks
   - **Single source**: Only `pyproject.toml` to maintain - no dependency drift

2. **Alternative Builds** (Legacy/Fallback):
   ```bash
   # Split Requirements (development only)
   # Change dockerfile in docker-compose.yml to: Dockerfile.split-requirements
   docker-compose up --build
   
   # Standard Build (compatibility)
   # Change dockerfile in docker-compose.yml to: Dockerfile
   docker-compose up --build
   ```

### Build Performance Comparison
- **No-cache builds**: 60+ minutes → 8-12 minutes (6-8x improvement)
- **Integration changes**: 16 minutes → 2-3 minutes
- **Development vs Production**: Same dependency source, different optimizations
- **Layer caching**: Multi-stage builds with Poetry dependency groups

## Troubleshooting: Docker Build Cache Issues

### Problem
If you see errors like:

```
failed to solve: failed to prepare extraction snapshot ... parent snapshot ... does not exist: not found
```

This is a Docker cache corruption issue, not a missing Python requirement or project dependency.

### Why does this happen?
- Docker's build cache can get corrupted or out of sync, especially after running `docker system prune` or `docker builder prune`.
- It can also happen after interrupted builds, running out of disk space, or Docker daemon restarts.

### How to fix
1. **Clean Docker's build cache:**
   ```sh
   docker builder prune -f
   docker system prune -af
   ```
   (This will remove unused images, containers, and build cache. Be careful: it will also remove stopped containers and unused volumes.)

2. **Rebuild your images:**
   ```sh
   # For development (recommended)
   docker compose build --no-cache
   docker compose up -d
   
   # For production
   docker compose -f docker-compose.poetry.yml build --no-cache
   docker compose -f docker-compose.poetry.yml up -d
   ```

3. **If the error persists:**
   - Restart Docker Desktop (or the Docker daemon)
   - If using WSL2, restart the WSL2 backend
   - Ensure you have enough disk space allocated to Docker

### Notes
- This is not a Python or project dependency issue, so changing `requirements.txt` or `pyproject.toml` will not help.
- If you see this error frequently, consider updating Docker Desktop to the latest version.
- Use Poetry development target for faster iteration with consistent dependencies

--- 
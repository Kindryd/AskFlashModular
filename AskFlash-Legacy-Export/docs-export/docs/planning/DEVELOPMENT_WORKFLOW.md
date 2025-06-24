# Flash AI Assistant - Development Workflow

## Poetry-Based Development (Recommended)

Flash AI Assistant uses **Poetry for both development and production** to ensure dependency consistency and eliminate drift between environments.

## Your New Workflow ✅

### Development (Local Testing)
```bash
# Your familiar commands - now with Poetry development target
docker compose build
docker compose up -d

# Or combined
docker compose up -d --build
```

**What this does:**
- ✅ Uses `Dockerfile.poetry` with `development` target
- ✅ Fast builds (8-12 minutes vs 60+ minutes)
- ✅ Hot reload enabled with volume mounting
- ✅ Debug logging enabled
- ✅ Same dependencies as production (no drift!)

### Production Deployment
```bash
# Production builds
docker compose -f docker-compose.poetry.yml build
docker compose -f docker-compose.poetry.yml up -d

# Or combined
docker compose -f docker-compose.poetry.yml up -d --build
```

**What this does:**
- ✅ Uses `Dockerfile.poetry` with `production` target
- ✅ Multi-stage optimized builds
- ✅ Enhanced security
- ✅ Health checks and monitoring
- ✅ Exact same dependencies as development

## Why This Approach?

### ✅ **Single Source of Truth**
- Only `backend/pyproject.toml` defines dependencies
- No risk of `requirements.txt` vs `pyproject.toml` drift
- Same packages in development and production

### ✅ **Speed + Consistency**
- Development target: Fast builds, hot reload
- Production target: Optimized, secure
- Both use the same dependency resolver

### ✅ **Teams Integration Ready**
- All Microsoft Teams Bot Framework dependencies included
- Environment variables configured for both targets
- Webhook endpoints ready for production

## Environment Variables

Create a `.env` file in your project root:

```bash
# Core Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Microsoft Teams Bot Framework
TEAMS_APP_ID=your-microsoft-app-id-here
TEAMS_APP_PASSWORD=your-microsoft-app-password-here
TEAMS_TENANT_ID=your-azure-tenant-id-here

# External Integrations (optional)
NOTION_API_KEY=your-notion-api-key-here
AZURE_DEVOPS_PAT=your-azure-devops-token-here
GITHUB_TOKEN=your-github-token-here
```

## Development Features

### Hot Reload (Development Target)
- Code changes automatically restart the backend
- Volume mounting: `./backend:/app`
- Debug logging enabled
- Development dependencies included

### Production Optimizations (Production Target)
- Multi-stage builds reduce image size
- Production dependencies only
- Security scanning
- Health checks enabled
- Resource limits configured

## Migration from Split Requirements

If you were using the split requirements approach:

### ✅ **Dependencies Maintained**
All your existing dependencies are preserved in `pyproject.toml`:
- FastAPI, SQLAlchemy, OpenAI, etc. (production group)
- Microsoft Teams Bot Framework (teams group)
- Development tools (dev group)

### ✅ **Same Performance**
- Development builds: Still 8-12 minutes
- Integration changes: Still 2-3 minutes
- Layer caching: Multi-stage builds

### ✅ **Enhanced Benefits**
- No dependency drift
- Better security
- Production-ready
- Enhanced monitoring

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repo>
   cd askflash
   cp .env.example .env  # Edit with your keys
   ```

2. **Start development**:
   ```bash
   docker compose up -d --build
   ```

3. **Access services**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database Admin: http://localhost:8080

4. **Teams Integration**:
   - Configure Teams app in Azure Portal
   - Set webhook URL: `https://your-domain.com/api/v1/teams/messages`
   - Use `/flash company` or `/flash general` commands

## Troubleshooting

### Clean Rebuild
```bash
docker compose down -v
docker system prune -f
docker compose up -d --build --no-cache
```

### Check Logs
```bash
# Backend logs
docker compose logs backend -f

# All services
docker compose logs -f
```

### Teams Bot Issues
```bash
# Test Teams configuration
curl http://localhost:8000/api/v1/teams/health

# Check Teams config
curl http://localhost:8000/api/v1/teams/config
```

---

**Bottom Line**: Your familiar `docker compose build && docker compose up -d` commands now give you the best of both worlds - development speed AND production consistency! 🐄⚡ 
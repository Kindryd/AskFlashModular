# 🧱 AskFlash Modular - Containerized AI Assistant Platform

Modern, scalable enterprise RAG (Retrieval-Augmented Generation) system built with microservices architecture. This is a complete rewrite of the legacy AskFlash system using containerized services with shared database model.

## 🏗️ Architecture Overview

AskFlash Modular uses a **single shared PostgreSQL database** with logical table ownership per container, enabling clean separation of concerns while maintaining data consistency.

### 📦 Container Services

| Container | Purpose | Port | DB Tables Owned |
|-----------|---------|------|-----------------|
| `frontend.container` | React UI & user interface | 3000 | _(stateless)_ |
| `conversation.container` | Chat sessions & messaging | 8001 | `conversation_histories`, `frequent_queries` |
| `embedding.container` | Vector generation & search | 8002 | `wikis`, `wiki_page_indexes` |
| `ai-orchestrator.container` | AI routing & orchestration | 8003 | `rulesets`, `integrations` |
| `project-manager.container` | External integrations | 8004 | _(reads only)_ |
| `adaptive-engine.container` | User learning & behavior | 8005 | `user_habits`, `learning_insights` |
| `local-llm.container` | Local model hosting | 8006 | _(stateless)_ |
| `analytics.container` | Logging & metrics | 8007 | _(external storage)_ |
| `gateway.container` | API gateway & routing | 8000 | _(stateless)_ |

### 🗄️ Infrastructure Services

- **PostgreSQL** (5432) - Shared database with logical ownership
- **Redis** (6379) - Event messaging and caching
- **Qdrant** (6333) - Vector database for embeddings
- **Adminer** (8080) - Database management UI

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- OpenAI API key (or other AI provider)

### Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url> askflash-modular
cd askflash-modular
cp .env.template .env
# Edit .env with your configuration
```

2. **Start the infrastructure:**
```bash
docker-compose up postgres redis qdrant adminer -d
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Verify deployment:**
```bash
# Check all services are running
docker-compose ps

# Test the gateway
curl http://localhost:8000/health

# Access database UI
open http://localhost:8080
```

## 🔗 Communication Patterns

### Synchronous (HTTP APIs)
- Frontend ↔ Gateway ↔ Services
- Inter-service direct API calls for real-time operations

### Asynchronous (Redis Events)
- All containers emit analytics events
- Event-driven processing for background tasks
- Real-time notifications and updates

### Key Event Topics
- `conversation:*` - Chat lifecycle events
- `embedding:*` - Document indexing events  
- `ai:*` - AI processing events
- `adaptive:*` - Learning and insights events

## 📊 Development Workflow

### Building Individual Containers
```bash
# Build specific container
docker-compose build conversation

# Start specific service
docker-compose up conversation -d

# View logs
docker-compose logs conversation -f
```

### Database Management
```bash
# Access database directly
docker-compose exec postgres psql -U postgres -d askflashdb

# Run migrations (when implemented)
docker-compose exec conversation python -m alembic upgrade head

# Backup database
docker-compose exec postgres pg_dump -U postgres askflashdb > backup.sql
```

### Debugging and Monitoring
```bash
# View all service logs
docker-compose logs -f

# Check Redis events
docker-compose exec redis redis-cli monitor

# Access Qdrant UI
open http://localhost:6333/dashboard
```

## 🏷️ Service APIs

### Gateway (Port 8000)
Main entry point - routes to appropriate services
- `GET /health` - System health check
- `POST /api/conversations/*` - Chat functionality
- `POST /api/embeddings/*` - Search and indexing
- `POST /api/ai/*` - AI operations

### Individual Services (Ports 8001-8007)
Each service exposes its own API endpoints. See individual container READMEs:
- [Conversation Service](./containers/conversation.container/README.md)
- [Embedding Service](./containers/embedding.container/README.md)
- [AI Orchestrator](./containers/ai-orchestrator.container/README.md)
- [Project Manager](./containers/project-manager.container/README.md)
- [Adaptive Engine](./containers/adaptive-engine.container/README.md)
- [Local LLM](./containers/local-llm.container/README.md)
- [Analytics](./containers/analytics.container/README.md)
- [Gateway](./containers/gateway.container/README.md)

## 🛠️ Configuration

### Environment Variables
Essential configuration in `.env`:
```env
# AI Services
OPENAI_API_KEY=your_key_here

# External Integrations  
JIRA_URL=https://company.atlassian.net
TEAMS_WEBHOOK_URL=your_webhook

# Security
JWT_SECRET_KEY=secure_secret_key
CORS_ORIGINS=http://localhost:3000
```

### Service Configuration
Each container has its own configuration requirements detailed in their individual READMEs.

## 🧪 Testing

### Unit Tests
```bash
# Test specific container
docker-compose exec conversation pytest tests/

# Test all containers
./scripts/test-all.sh
```

### Integration Tests
```bash
# Full system integration test
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📈 Scaling and Production

### Horizontal Scaling
Individual containers can be scaled independently:
```bash
# Scale conversation handlers
docker-compose up --scale conversation=3

# Scale embedding processors  
docker-compose up --scale embedding=2
```

### Production Deployment
For production, consider:
- Kubernetes deployment with Helm charts
- External PostgreSQL and Redis clusters
- Load balancers for stateless services
- Monitoring with Prometheus/Grafana
- Centralized logging with ELK stack

## 🔧 Legacy Migration

This system replaces the legacy AskFlash monolith. Key preserved features:
- ✅ Real-time streaming chat
- ✅ Vector-powered semantic search  
- ✅ Microsoft Teams integration
- ✅ Azure DevOps wiki crawling
- ✅ Multi-provider AI support
- ❌ ALTO Protocol (removed - failed optimization)

Migration tools and guides available in `./migration/` directory.

## 📚 Documentation

- [Architecture Documentation](./docs/architecture/)
- [Container Documentation](./docs/containers/)
- [API Documentation](./docs/api/)
- [Deployment Guide](./docs/deployment/)

## 🤝 Contributing

1. Follow container-specific development guidelines
2. Ensure all tests pass: `./scripts/test-all.sh`
3. Update relevant documentation
4. Submit pull request with clear description

## 📄 License

[Your License Here]

---

**Built with modern microservices architecture for scalability, maintainability, and developer experience. 🚀** 
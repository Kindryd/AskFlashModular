# gateway.container

## 📌 Purpose
Reverse proxy and API gateway. Handles request routing, authentication, rate limiting, and load balancing across all backend services.

## 🔗 DB Tables Used
### Write:
- (none - stateless proxy)

### Read-only:
- (none - stateless proxy)

## 🔁 Communication
### API:
- `/*` - Routes all requests to appropriate backend services
- `/health` - Gateway health check
- `/metrics` - Gateway performance metrics

### Redis:
- **Emits**: `gateway:request_routed`, `gateway:rate_limit_exceeded`
- **Subscribes**: (none - stateless routing)

## ⚙️ Configuration
```env
REDIS_URL=redis://redis:6379
CONVERSATION_SERVICE_URL=http://conversation:8000
EMBEDDING_SERVICE_URL=http://embedding:8000
AI_ORCHESTRATOR_URL=http://ai-orchestrator:8000
PROJECT_MANAGER_URL=http://project-manager:8000
ADAPTIVE_ENGINE_URL=http://adaptive-engine:8000
ANALYTICS_URL=http://analytics:8000
RATE_LIMIT_PER_MINUTE=100
CORS_ORIGINS=http://localhost:3000,https://askflash.yourdomain.com
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/gateway .
docker run --env-file .env askflash/gateway
``` 
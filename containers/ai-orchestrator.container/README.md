# ai-orchestrator.container

## 📌 Purpose
AI access control, routing, and response orchestration. Manages AI provider selection, request routing, response quality control, and interfaces with both OpenAI and local LLM services.

## 🔗 DB Tables Used
### Write:
- `rulesets` - AI routing rules and configurations
- `integrations` - AI provider settings and API keys

### Read-only:
- `users` - User permissions and AI access levels
- `conversation_histories` - Context for AI responses

## 🔁 Communication
### API:
- `POST /api/ai/chat` - Process AI chat requests
- `GET /api/ai/providers` - List available AI providers
- `POST /api/ai/analyze` - Content analysis
- `GET /api/ai/status` - Health check for AI services

### Redis:
- **Emits**: `ai:response_ready`, `ai:processing`, `ai:error`
- **Subscribes**: `conversation:message_received`, `embedding:context_ready`

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=${OPENAI_API_KEY}
LOCAL_LLM_URL=http://local-llm:8000
DEFAULT_MODEL=gpt-4
FALLBACK_MODEL=gpt-3.5-turbo
MAX_TOKENS=4000
TEMPERATURE=0.7
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/ai-orchestrator .
docker run --env-file .env askflash/ai-orchestrator
``` 
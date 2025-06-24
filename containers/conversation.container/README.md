# conversation.container

## 📌 Purpose
Manages chat sessions, messaging history, and real-time conversation interfaces. Handles user interactions, conversation persistence, and coordinates with AI services for response generation.

## 🔗 DB Tables Used
### Write:
- `conversation_histories` - Chat sessions and message logs
- `frequent_queries` - User query patterns and analytics

### Read-only:
- `users` - User authentication and preferences
- `rulesets` - Configuration for conversation context

## 🔁 Communication
### API:
- `POST /api/conversations/` - Create new conversation
- `GET /api/conversations/{id}` - Retrieve conversation history
- `POST /api/conversations/{id}/messages` - Send message
- `GET /api/conversations/{id}/stream` - WebSocket streaming endpoint

### Redis:
- **Emits**: `conversation:created`, `message:sent`, `conversation:ended`
- **Subscribes**: `ai:response_ready`, `embedding:context_enhanced`

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
AI_ORCHESTRATOR_URL=http://ai-orchestrator:8000
EMBEDDING_SERVICE_URL=http://embedding:8000
WEBSOCKET_TIMEOUT=300
MAX_CONVERSATION_HISTORY=50
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/conversation .
docker run --env-file .env askflash/conversation
``` 
# local-llm.container

## 📌 Purpose
Hosts local LLM models (e.g., Mistral, Llama) providing OpenAI-compatible API endpoints. Serves as fallback and privacy-focused alternative to external AI services.

## 🔗 DB Tables Used
### Write:
- (none - stateless model serving)

### Read-only:
- (none - stateless model serving)

## 🔁 Communication
### API:
- `POST /api/v1/chat/completions` - OpenAI-compatible chat endpoint
- `POST /api/v1/completions` - Text completion endpoint
- `GET /api/v1/models` - List available models
- `GET /api/health` - Service health check

### Redis:
- **Emits**: `llm:response_generated`, `llm:model_loaded`
- **Subscribes**: `ai:local_request`

## ⚙️ Configuration
```env
REDIS_URL=redis://redis:6379
MODEL_NAME=mistral-7b-instruct
MODEL_PATH=/models/mistral-7b
GPU_ENABLED=true
MAX_CONTEXT_LENGTH=8192
TEMPERATURE=0.7
MAX_TOKENS=2048
BATCH_SIZE=4
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/local-llm .
docker run --env-file .env --gpus all askflash/local-llm
``` 
# adaptive-engine.container

## 📌 Purpose
User learning, behavior tracking, and adaptive response optimization. Analyzes user patterns, preferences, and conversation effectiveness to improve AI responses over time.

## 🔗 DB Tables Used
### Write:
- `user_habits` - User behavior patterns and preferences
- `learning_insights` - Generated insights and recommendations

### Read-only:
- `users` - User profiles and settings
- `conversation_histories` - Conversation analysis data
- `frequent_queries` - Query pattern analysis

## 🔁 Communication
### API:
- `POST /api/adaptive/analyze` - Analyze user behavior
- `GET /api/adaptive/insights/{user_id}` - Get user insights
- `POST /api/adaptive/feedback` - Record user feedback
- `GET /api/adaptive/recommendations` - Get personalization recommendations

### Redis:
- **Emits**: `adaptive:insight_generated`, `adaptive:pattern_detected`
- **Subscribes**: `conversation:ended`, `ai:response_rated`, `user:feedback_given`

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
ANALYSIS_BATCH_SIZE=100
LEARNING_THRESHOLD=0.8
PATTERN_DETECTION_WINDOW=7d
INSIGHT_RETENTION_DAYS=90
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/adaptive-engine .
docker run --env-file .env askflash/adaptive-engine
``` 
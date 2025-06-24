# embedding.container

## 📌 Purpose
Handles vector generation, context enhancement, and semantic search capabilities. Manages document indexing, embedding generation, and interfaces with Qdrant vector database.

## 🔗 DB Tables Used
### Write:
- `wikis` - Document metadata and indexing status
- `wiki_page_indexes` - Page-level indexing and embedding references

### Read-only:
- `rulesets` - Data source configurations
- `integrations` - External system connection details

## 🔁 Communication
### API:
- `POST /api/embeddings/generate` - Generate embeddings for content
- `POST /api/embeddings/search` - Semantic search
- `GET /api/embeddings/status` - Indexing status
- `POST /api/embeddings/index` - Index new documents

### Redis:
- **Emits**: `embedding:generated`, `document:indexed`, `search:completed`
- **Subscribes**: `conversation:message_received`, `document:uploaded`

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
OPENAI_API_KEY=${OPENAI_API_KEY}
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_DIMENSIONS=1536
BATCH_SIZE=100
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/embedding .
docker run --env-file .env askflash/embedding
``` 
# Intent Agent - AskFlash MCP Architecture

The Intent Agent is a specialized container in the AskFlash MCP (Master Control Program) system that processes intent analysis tasks. It analyzes user queries to understand intent, assess complexity, and determine optimal processing strategies.

## 🧠 Capabilities

- **Intent Classification**: Categorizes queries into 8 intent types (informational, procedural, navigational, transactional, comparative, diagnostic, creative, analytical)
- **Complexity Assessment**: Evaluates query complexity (very_low, low, medium, high, very_high) 
- **Sub-Question Generation**: Breaks down complex queries into focused sub-questions
- **Strategy Determination**: Selects optimal processing approach (quick_answer, standard_query, complex_research, web_enhanced)
- **Web Search Detection**: Identifies queries requiring real-time information

## 🏗️ Architecture

### Core Components

- **Intent Analyzer**: Core analysis engine using GPT-3.5-turbo
- **RabbitMQ Consumer**: Processes tasks from `intent.task` queue
- **Redis Integration**: Caches results and publishes progress events
- **FastAPI Server**: Provides REST API for monitoring and testing

### Communication Flow

1. Consumes tasks from `intent.task` RabbitMQ queue
2. Performs comprehensive intent analysis using OpenAI
3. Publishes results to Redis channels:
   - `ai:intent:complete` - Completion notifications
   - `ai:progress:{task_id}` - Progress updates
4. Stores full analysis in `intent_result:{task_id}` Redis key

## 🚀 Getting Started

### Prerequisites

- Docker
- OpenAI API key
- Redis server
- RabbitMQ server

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Redis Configuration  
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=askflash123

# RabbitMQ Configuration
RABBITMQ_URL=amqp://askflash:askflash123@localhost:5672/
```

### Running the Container

```bash
# Build the container
docker build -t intent-agent .

# Run the container
docker run -d \
  --name intent-agent \
  -p 8010:8010 \
  -e OPENAI_API_KEY=your_key \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  -e RABBITMQ_URL=amqp://askflash:askflash123@host.docker.internal:5672/ \
  intent-agent
```

## 📡 API Endpoints

### Health & Status

- `GET /` - Service information
- `GET /health` - Health check (Redis, RabbitMQ, OpenAI status)
- `GET /capabilities` - Agent capabilities and configuration

### Monitoring

- `GET /api/v1/stats` - Processing statistics
- `GET /api/v1/queue/status` - RabbitMQ queue status

### Testing

- `POST /api/v1/analyze` - Manual intent analysis
  ```json
  {
    "query": "What are the latest trends in AI?",
    "user_id": "test_user"
  }
  ```

## 🔄 Message Format

### Input (from `intent.task` queue)

```json
{
  "task_id": "abc123",
  "query": "Who are the SRE team members?", 
  "user_id": "user-001"
}
```

### Output (to `ai:intent:complete` channel)

```json
{
  "task_id": "abc123",
  "stage": "intent_analysis",
  "status": "completed",
  "analysis_summary": {
    "primary_intent": "informational",
    "complexity_level": "medium",
    "strategy": "standard_query",
    "web_search_required": false,
    "estimated_processing_time_ms": 10000
  },
  "next_stage": "embedding_lookup",
  "timestamp": "2024-12-27T10:15:30Z"
}
```

## 📊 Performance Characteristics

- **Processing Time**: 1.5-4 seconds per query
- **Throughput**: ~15-20 tasks per minute
- **Memory Usage**: ~150-200MB
- **Concurrency**: Up to 10 concurrent tasks

## 🔧 Configuration

### Intent Analysis Settings

```python
# Query limits
min_query_length: int = 3
max_query_length: int = 2000

# Complexity assessment
complexity_threshold_words: int = 10

# Web search detection keywords
web_search_keywords = [
    "current", "today", "latest", "recent", "news", 
    "weather", "stock", "price", "real-time", "live"
]
```

### RabbitMQ Settings

```python
rabbitmq_queue: str = "intent.task"
rabbitmq_prefetch_count: int = 10
max_concurrent_tasks: int = 10
```

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Check API key and rate limits
2. **Redis Connection**: Verify Redis URL and password
3. **RabbitMQ Issues**: Ensure queue exists and credentials are correct
4. **Memory Issues**: Monitor memory usage with high concurrency

### Logs

```bash
# View container logs
docker logs intent-agent

# Follow logs
docker logs -f intent-agent
```

### Health Checks

```bash
# Check health endpoint
curl http://localhost:8010/health

# Check queue status
curl http://localhost:8010/api/v1/queue/status
```

## 🔗 Integration

The Intent Agent integrates with:

- **MCP Container**: Receives tasks via RabbitMQ
- **Embedding Agent**: Next stage for document retrieval
- **Web Search Agent**: Alternative next stage for current information
- **Redis**: State management and progress tracking
- **PostgreSQL**: Task history and analytics (via MCP)

## 📈 Monitoring

Key metrics to monitor:

- Processing success rate
- Average processing time
- Queue depth
- Memory and CPU usage
- OpenAI API response times
- Redis connection health

## 🔄 Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

### Testing

```bash
# Test intent analysis
curl -X POST http://localhost:8010/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I deploy a new service?", "user_id": "test"}'
``` 
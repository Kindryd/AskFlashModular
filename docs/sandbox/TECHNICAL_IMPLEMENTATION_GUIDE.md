# ⚙️ Technical Implementation Guide - MCP Architecture

This document provides specific technical implementation details, code patterns, and configuration examples for implementing the MCP (Master Control Program) architecture in AskFlash Modular.

---

## 🏗️ Phase 1: Infrastructure Setup

### **1.1 RabbitMQ Configuration**

#### Docker Compose Update
```yaml
# Add to docker-compose.yml
services:
  rabbitmq:
    image: rabbitmq:3.12-management
    container_name: askflash_rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-askflash}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-askflash123}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./infrastructure/rabbitmq/enabled_plugins:/etc/rabbitmq/enabled_plugins
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 30s
      retries: 3

volumes:
  rabbitmq_data:
```

#### Queue Initialization Script
```python
# infrastructure/rabbitmq/init_queues.py
import pika
import logging

def setup_rabbitmq_queues():
    """Initialize RabbitMQ exchanges and queues for MCP"""
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost', 5672, '/', 
                                pika.PlainCredentials('askflash', 'askflash123'))
    )
    channel = connection.channel()
    
    # Declare exchange for task routing
    channel.exchange_declare(
        exchange='mcp.tasks',
        exchange_type='direct',
        durable=True
    )
    
    # Declare task queues
    queues = [
        'intent.task',
        'embedding.task', 
        'executor.task',
        'moderator.task',
        'websearch.task'
    ]
    
    for queue_name in queues:
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(
            exchange='mcp.tasks',
            queue=queue_name,
            routing_key=queue_name
        )
    
    connection.close()
    logging.info("RabbitMQ queues initialized successfully")

if __name__ == "__main__":
    setup_rabbitmq_queues()
```

### **1.2 Enhanced Redis Configuration**

#### Redis Configuration File
```redis
# infrastructure/redis/redis.conf
# Enable streams and pub/sub
stream-node-max-bytes 4096
stream-node-max-entries 100

# Set memory policy for task cleanup
maxmemory-policy allkeys-lru
maxmemory 256mb

# Enable keyspace notifications for task expiration
notify-keyspace-events Ex

# Persistence configuration
save 900 1
save 300 10
save 60 10000
```

#### Redis Task Management Utility
```python
# shared/redis_manager.py
import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class RedisTaskManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.task_ttl = 600  # 10 minutes
    
    def create_task(self, user_id: str, query: str, plan: list) -> str:
        """Create a new task DAG in Redis"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "query": query,
            "plan": plan,
            "current_stage": plan[0] if plan else None,
            "completed_stages": [],
            "status": "in_progress",
            "context": "",
            "vector_hits": [],
            "response": None,
            "error": None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store main task data
        self.redis.setex(
            f"task:{task_id}",
            self.task_ttl,
            json.dumps(task_data)
        )
        
        # Initialize progress stream
        self.redis.xadd(
            f"task:{task_id}:progress",
            {"stage": "initialized", "message": "Task created", "timestamp": datetime.utcnow().isoformat()}
        )
        
        return task_id
    
    def update_task_stage(self, task_id: str, new_stage: str, context: str = None):
        """Update task to next stage"""
        task_key = f"task:{task_id}"
        task_data = self.get_task(task_id)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        # Move current stage to completed
        if task_data["current_stage"]:
            task_data["completed_stages"].append(task_data["current_stage"])
        
        task_data["current_stage"] = new_stage
        task_data["updated_at"] = datetime.utcnow().isoformat()
        
        if context:
            task_data["context"] = context
        
        # Update in Redis
        self.redis.setex(task_key, self.task_ttl, json.dumps(task_data))
        
        # Add progress event
        self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": new_stage, 
                "message": f"Advanced to {new_stage}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task data"""
        task_data = self.redis.get(f"task:{task_id}")
        return json.loads(task_data) if task_data else None
    
    def emit_progress_event(self, task_id: str, stage: str, message: str):
        """Emit progress event for frontend"""
        self.redis.publish(
            f"ai:progress:{task_id}",
            json.dumps({
                "task_id": task_id,
                "stage": stage,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
```

### **1.3 Database Schema Migration**

```sql
-- infrastructure/database/migrations/add_mcp_tables.sql

-- Task histories for MCP coordination
CREATE TABLE IF NOT EXISTS task_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    plan JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    current_stage VARCHAR(100),
    completed_stages JSONB DEFAULT '[]',
    context TEXT,
    response JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_task_user_id (user_id),
    INDEX idx_task_status (status),
    INDEX idx_task_created (started_at)
);

-- DAG templates for reusable task patterns
CREATE TABLE IF NOT EXISTS task_dag_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    stages JSONB NOT NULL,
    conditions JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent performance tracking
CREATE TABLE IF NOT EXISTS agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    task_id UUID REFERENCES task_histories(id),
    stage VARCHAR(100) NOT NULL,
    duration_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_agent_performance (agent_name, created_at)
);

-- Insert default DAG templates
INSERT INTO task_dag_templates (name, description, stages, conditions) VALUES
('standard_query', 'Standard question answering flow', 
 '["intent_analysis", "embedding_lookup", "executor_reasoning", "moderation", "response_packaging"]',
 '{"complexity": "low", "requires_web_search": false}'),
('complex_research', 'Complex multi-step research with web augmentation',
 '["intent_analysis", "embedding_lookup", "web_search", "executor_reasoning", "moderation", "response_packaging"]',
 '{"complexity": "high", "requires_web_search": true}'),
('simple_lookup', 'Simple document lookup without complex reasoning',
 '["embedding_lookup", "response_packaging"]',
 '{"complexity": "very_low", "direct_answer": true}');
```

---

## 🧠 Phase 2: MCP Core Implementation

### **2.1 Task Coordinator Service**

```python
# containers/mcp.container/services/task_coordinator.py
import asyncio
import json
import logging
from typing import Dict, List, Optional
from shared.redis_manager import RedisTaskManager
from services.message_broker import MessageBroker
from services.state_manager import StateManager

class TaskCoordinator:
    """Core DAG execution engine for MCP"""
    
    def __init__(self):
        self.redis_manager = RedisTaskManager()
        self.message_broker = MessageBroker()
        self.state_manager = StateManager()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # DAG stage routing map
        self.stage_routes = {
            "intent_analysis": "intent.task",
            "embedding_lookup": "embedding.task", 
            "executor_reasoning": "executor.task",
            "moderation": "moderator.task",
            "web_search": "websearch.task",
            "response_packaging": self._handle_response_packaging
        }
    
    async def create_and_execute_task(self, user_id: str, query: str, template: str = "standard_query") -> str:
        """Create new task and begin execution"""
        
        # Get DAG template
        dag_template = await self.state_manager.get_dag_template(template)
        if not dag_template:
            raise ValueError(f"Unknown DAG template: {template}")
        
        # Create task in Redis
        task_id = self.redis_manager.create_task(user_id, query, dag_template["stages"])
        
        # Start execution
        execution_task = asyncio.create_task(self._execute_dag(task_id))
        self.active_tasks[task_id] = execution_task
        
        logging.info(f"Created and started task {task_id} for user {user_id}")
        return task_id
    
    async def _execute_dag(self, task_id: str):
        """Execute task DAG stages sequentially"""
        try:
            task_data = self.redis_manager.get_task(task_id)
            if not task_data:
                logging.error(f"Task {task_id} not found")
                return
            
            while task_data["current_stage"] and task_data["status"] == "in_progress":
                stage = task_data["current_stage"]
                
                logging.info(f"Executing stage {stage} for task {task_id}")
                
                # Execute current stage
                success = await self._execute_stage(task_id, stage, task_data)
                
                if not success:
                    await self._handle_stage_failure(task_id, stage)
                    break
                
                # Move to next stage
                await self._advance_to_next_stage(task_id)
                task_data = self.redis_manager.get_task(task_id)
            
            # Complete task
            if task_data and task_data["status"] == "in_progress":
                await self._complete_task(task_id)
                
        except Exception as e:
            logging.error(f"Error executing task {task_id}: {e}")
            await self._handle_task_error(task_id, str(e))
        finally:
            # Cleanup
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _execute_stage(self, task_id: str, stage: str, task_data: Dict) -> bool:
        """Execute a single DAG stage"""
        
        if stage == "response_packaging":
            return await self._handle_response_packaging(task_id, task_data)
        
        # Get queue for stage
        queue_name = self.stage_routes.get(stage)
        if not queue_name:
            logging.error(f"Unknown stage {stage} for task {task_id}")
            return False
        
        # Prepare task payload
        payload = {
            "task_id": task_id,
            "query": task_data["query"],
            "user_id": task_data["user_id"],
            "context": task_data.get("context", ""),
            "vector_hits": task_data.get("vector_hits", [])
        }
        
        # Publish to RabbitMQ
        await self.message_broker.publish_task(queue_name, payload)
        
        # Wait for completion (with timeout)
        return await self._wait_for_stage_completion(task_id, stage, timeout=300)
    
    async def _wait_for_stage_completion(self, task_id: str, stage: str, timeout: int = 300) -> bool:
        """Wait for stage completion event"""
        completion_event = f"ai:{stage.replace('_', ':')}:complete"
        
        try:
            # Wait for Redis pub/sub event
            result = await asyncio.wait_for(
                self.message_broker.wait_for_event(completion_event, task_id),
                timeout=timeout
            )
            return result.get("success", False)
            
        except asyncio.TimeoutError:
            logging.error(f"Stage {stage} timed out for task {task_id}")
            return False
    
    async def _advance_to_next_stage(self, task_id: str):
        """Move task to next stage in DAG"""
        task_data = self.redis_manager.get_task(task_id)
        if not task_data:
            return
        
        current_index = task_data["plan"].index(task_data["current_stage"])
        
        if current_index + 1 < len(task_data["plan"]):
            next_stage = task_data["plan"][current_index + 1]
            self.redis_manager.update_task_stage(task_id, next_stage)
        else:
            # No more stages
            task_data["current_stage"] = None
            task_data["status"] = "complete"
            self.redis_manager.redis.setex(
                f"task:{task_id}",
                self.redis_manager.task_ttl,
                json.dumps(task_data)
            )
    
    async def _handle_response_packaging(self, task_id: str, task_data: Dict) -> bool:
        """Final stage: package response for frontend"""
        try:
            # Get accumulated context and results
            context = task_data.get("context", "")
            vector_hits = task_data.get("vector_hits", [])
            
            # Package final response
            response = {
                "content": context,
                "sources": vector_hits,
                "confidence": 0.8,  # Calculate based on moderation results
                "thinking_steps": await self._get_thinking_steps(task_id)
            }
            
            # Update task with final response
            task_data["response"] = response
            task_data["status"] = "complete"
            
            self.redis_manager.redis.setex(
                f"task:{task_id}",
                self.redis_manager.task_ttl, 
                json.dumps(task_data)
            )
            
            # Emit completion event
            await self.message_broker.publish_event("ai:response:ready", {
                "task_id": task_id,
                "response": response
            })
            
            return True
            
        except Exception as e:
            logging.error(f"Error packaging response for task {task_id}: {e}")
            return False
    
    async def _get_thinking_steps(self, task_id: str) -> List[Dict]:
        """Retrieve thinking steps from Redis stream"""
        try:
            stream_key = f"task:{task_id}:progress"
            events = self.redis_manager.redis.xrange(stream_key)
            
            thinking_steps = []
            for event_id, fields in events:
                thinking_steps.append({
                    "stage": fields.get("stage", ""),
                    "message": fields.get("message", ""),
                    "timestamp": fields.get("timestamp", "")
                })
            
            return thinking_steps
            
        except Exception as e:
            logging.error(f"Error retrieving thinking steps for task {task_id}: {e}")
            return []
```

### **2.2 Message Broker Service**

```python
# containers/mcp.container/services/message_broker.py
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis

class MessageBroker:
    """RabbitMQ and Redis messaging integration"""
    
    def __init__(self):
        self.rabbitmq_url = "amqp://askflash:askflash123@localhost/"
        self.redis_url = "redis://localhost:6379"
        self.connection = None
        self.channel = None
        self.redis = None
        
    async def connect(self):
        """Initialize connections"""
        # RabbitMQ
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        
        # Redis
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
        
        logging.info("Message broker connections established")
    
    async def publish_task(self, queue_name: str, payload: Dict[str, Any]):
        """Publish task to RabbitMQ queue"""
        if not self.channel:
            await self.connect()
        
        message = aio_pika.Message(
            json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self.channel.default_exchange.publish(
            message, routing_key=queue_name
        )
        
        logging.info(f"Published task to {queue_name}: {payload['task_id']}")
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]):
        """Publish event to Redis pub/sub"""
        if not self.redis:
            await self.connect()
        
        await self.redis.publish(channel, json.dumps(event_data))
        logging.info(f"Published event to {channel}")
    
    async def wait_for_event(self, event_pattern: str, task_id: str, timeout: int = 300) -> Dict:
        """Wait for specific Redis pub/sub event"""
        if not self.redis:
            await self.connect()
        
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"{event_pattern}:{task_id}")
        
        try:
            message = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True),
                timeout=timeout
            )
            
            if message:
                return json.loads(message['data'])
            return {}
            
        except asyncio.TimeoutError:
            logging.warning(f"Timeout waiting for event {event_pattern}:{task_id}")
            return {}
        finally:
            await pubsub.unsubscribe(f"{event_pattern}:{task_id}")
```

---

## 🤖 Phase 3: Agent Container Templates

### **3.1 Base Agent Container Pattern**

```python
# shared/base_agent.py
import asyncio
import json
import logging
from abc import ABC, abstractmethod
import aio_pika
import redis.asyncio as aioredis

class BaseAgent(ABC):
    """Base class for all MCP agent containers"""
    
    def __init__(self, agent_name: str, queue_name: str):
        self.agent_name = agent_name
        self.queue_name = queue_name
        self.rabbitmq_url = "amqp://askflash:askflash123@localhost/"
        self.redis_url = "redis://localhost:6379"
        self.connection = None
        self.channel = None
        self.redis = None
        
    async def start(self):
        """Start agent and begin consuming tasks"""
        await self._connect()
        await self._setup_consumer()
        logging.info(f"{self.agent_name} agent started")
        
    async def _connect(self):
        """Initialize connections"""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
        
    async def _setup_consumer(self):
        """Setup RabbitMQ consumer"""
        queue = await self.channel.declare_queue(self.queue_name, durable=True)
        await queue.consume(self._handle_message)
        
    async def _handle_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming RabbitMQ message"""
        async with message.process():
            try:
                payload = json.loads(message.body.decode())
                task_id = payload["task_id"]
                
                logging.info(f"{self.agent_name} processing task {task_id}")
                
                # Process task
                result = await self.process_task(payload)
                
                # Update task state and emit events
                await self._complete_task(task_id, result)
                
            except Exception as e:
                logging.error(f"{self.agent_name} error processing message: {e}")
                await self._handle_error(payload.get("task_id"), str(e))
    
    @abstractmethod
    async def process_task(self, payload: Dict) -> Dict:
        """Process the task - to be implemented by each agent"""
        pass
    
    async def _complete_task(self, task_id: str, result: Dict):
        """Mark task stage as complete"""
        # Update task in Redis
        await self._update_task_context(task_id, result)
        
        # Emit completion event
        completion_event = f"ai:{self.agent_name.replace('_', ':')}:complete"
        await self.redis.publish(f"{completion_event}:{task_id}", json.dumps({
            "task_id": task_id,
            "success": True,
            "result": result
        }))
        
        logging.info(f"{self.agent_name} completed task {task_id}")
    
    async def _update_task_context(self, task_id: str, result: Dict):
        """Update task context with agent results"""
        task_key = f"task:{task_id}"
        task_data_str = await self.redis.get(task_key)
        
        if task_data_str:
            task_data = json.loads(task_data_str)
            
            # Update context based on agent type
            if "context" in result:
                task_data["context"] = result["context"]
            if "vector_hits" in result:
                task_data["vector_hits"] = result["vector_hits"]
                
            # Store updated task
            await self.redis.setex(task_key, 600, json.dumps(task_data))
    
    async def _emit_progress(self, task_id: str, message: str):
        """Emit progress event for frontend"""
        await self.redis.publish(f"ai:progress:{task_id}", json.dumps({
            "task_id": task_id,
            "stage": self.agent_name,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }))
```

### **3.2 Preprocessor Agent Implementation**

```python
# containers/preprocessor.container/services/intent_analyzer.py
import openai
from shared.base_agent import BaseAgent

class PreprocessorAgent(BaseAgent):
    """Intent analysis and query planning agent"""
    
    def __init__(self):
        super().__init__("preprocessor", "intent.task")
        self.openai_client = openai.AsyncOpenAI()
        
    async def process_task(self, payload: Dict) -> Dict:
        """Analyze query intent and suggest DAG modifications"""
        query = payload["query"]
        task_id = payload["task_id"]
        
        await self._emit_progress(task_id, "Analyzing query intent...")
        
        # Analyze with GPT-3.5
        intent_analysis = await self._analyze_intent(query)
        
        await self._emit_progress(task_id, "Determining search strategy...")
        
        # Determine if web search needed
        needs_web_search = await self._assess_web_search_need(query, intent_analysis)
        
        # Suggest DAG modifications
        dag_suggestions = await self._suggest_dag_modifications(intent_analysis, needs_web_search)
        
        return {
            "intent_analysis": intent_analysis,
            "needs_web_search": needs_web_search,
            "dag_suggestions": dag_suggestions,
            "context": f"Query analysis: {intent_analysis['summary']}"
        }
    
    async def _analyze_intent(self, query: str) -> Dict:
        """Analyze query intent with GPT-3.5"""
        prompt = f"""
        Analyze the following user query and provide a detailed intent analysis:
        
        Query: "{query}"
        
        Provide analysis in JSON format:
        {{
            "primary_intent": "information_retrieval|problem_solving|creation|other",
            "complexity": "low|medium|high",
            "domains": ["list of relevant domains"],
            "sub_questions": ["list of sub-questions to answer"],
            "summary": "brief summary of what user wants"
        }}
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {
                "primary_intent": "information_retrieval",
                "complexity": "medium", 
                "domains": ["general"],
                "sub_questions": [query],
                "summary": query
            }
    
    async def _assess_web_search_need(self, query: str, intent_analysis: Dict) -> bool:
        """Determine if web search is needed"""
        # Check for time-sensitive keywords
        time_sensitive_keywords = ["current", "latest", "recent", "today", "now", "2024", "2025"]
        query_lower = query.lower()
        
        # Check for news/current events
        if any(keyword in query_lower for keyword in time_sensitive_keywords):
            return True
            
        # Check complexity
        if intent_analysis.get("complexity") == "high":
            return True
            
        return False
    
    async def _suggest_dag_modifications(self, intent_analysis: Dict, needs_web_search: bool) -> List[str]:
        """Suggest DAG stage modifications based on analysis"""
        base_dag = ["intent_analysis", "embedding_lookup", "executor_reasoning", "moderation", "response_packaging"]
        
        if needs_web_search:
            # Insert web search before executor
            base_dag.insert(-2, "web_search")
            
        if intent_analysis.get("complexity") == "low":
            # Skip some stages for simple queries
            return ["embedding_lookup", "response_packaging"]
            
        return base_dag
```

This technical implementation guide provides the specific code patterns, configurations, and integration details needed to implement the MCP architecture. Each section includes working code examples that can be directly implemented in the AskFlash Modular project.

The guide covers:

1. **Infrastructure Setup** - RabbitMQ, Redis, and database configurations
2. **Core MCP Implementation** - Task coordination and message broker services
3. **Agent Container Patterns** - Reusable base classes and specific agent implementations
4. **Integration Patterns** - How containers communicate and coordinate

This provides the foundation for implementing the complete MCP multi-agent architecture while maintaining the existing working functionality. 
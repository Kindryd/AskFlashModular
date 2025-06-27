import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

import aio_pika
from aio_pika import connect_robust, Message, ExchangeType
import redis.asyncio as redis

from core.config import settings
from services.web_searcher import WebSearcher

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """RabbitMQ consumer for web search tasks"""
    
    def __init__(self, web_searcher: WebSearcher):
        self.web_searcher = web_searcher
        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.redis_client: Optional[redis.Redis] = None
        self.consuming = False
        
    async def initialize(self):
        """Initialize RabbitMQ and Redis connections"""
        try:
            # Connect to RabbitMQ
            self.connection = await connect_robust(
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
                f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}{settings.RABBITMQ_VHOST}"
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=settings.MAX_CONCURRENT_SEARCHES)
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.QUEUE_NAME,
                durable=settings.QUEUE_DURABLE
            )
            
            # Connect to Redis for progress tracking
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            # Initialize web searcher
            await self.web_searcher.initialize()
            
            logger.info("✅ RabbitMQ and Redis connections established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise
    
    async def publish_progress(self, task_id: str, stage: str, message: str, progress: int = None):
        """Publish progress update to Redis"""
        try:
            if self.redis_client:
                progress_data = {
                    "task_id": task_id,
                    "agent": "websearch",
                    "stage": stage,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if progress is not None:
                    progress_data["progress"] = progress
                
                # Publish to progress stream
                await self.redis_client.xadd(
                    f"ai:progress:{task_id}",
                    progress_data,
                    maxlen=100  # Keep last 100 progress entries
                )
                
                logger.debug(f"📊 Progress published for task {task_id}: {message}")
                
        except Exception as e:
            logger.warning(f"Failed to publish progress: {e}")
    
    async def publish_result(self, task_id: str, result: Dict[str, Any]):
        """Publish search result back to MCP"""
        try:
            result_data = {
                "task_id": task_id,
                "agent": "websearch",
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            # Store result in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"websearch_result:{task_id}",
                    3600,  # 1 hour TTL
                    json.dumps(result_data)
                )
                
                # Publish completion event
                await self.redis_client.publish(
                    "ai:websearch:complete",
                    json.dumps({"task_id": task_id, "status": "completed"})
                )
            
            # Send to response queue
            if self.channel:
                response_queue = await self.channel.declare_queue(
                    settings.RESPONSE_QUEUE,
                    durable=True
                )
                
                message = Message(
                    json.dumps(result_data).encode(),
                    content_type="application/json",
                    headers={"task_id": task_id, "agent": "websearch"}
                )
                
                await self.channel.default_exchange.publish(
                    message,
                    routing_key=settings.RESPONSE_QUEUE
                )
            
            logger.info(f"✅ Result published for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish result: {e}")
    
    async def process_search_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a web search task"""
        task_id = task_data.get("task_id", "unknown")
        query = task_data.get("query", "")
        search_type = task_data.get("search_type", "web")
        max_results = task_data.get("max_results")
        
        try:
            await self.publish_progress(
                task_id, 
                "websearch_start", 
                f"Starting web search for: {query[:50]}...",
                0
            )
            
            if search_type == "instant":
                # Get instant answers
                await self.publish_progress(
                    task_id,
                    "websearch_instant",
                    "Searching for instant answers...",
                    25
                )
                
                result = await self.web_searcher.search_instant_answers(query)
                
            else:
                # Perform web search
                await self.publish_progress(
                    task_id,
                    "websearch_web",
                    "Performing web search...",
                    25
                )
                
                result = await self.web_searcher.search_web(query, max_results)
            
            await self.publish_progress(
                task_id,
                "websearch_processing",
                "Processing and ranking results...",
                75
            )
            
            # Add task metadata to result
            result.update({
                "task_id": task_id,
                "agent": "websearch",
                "processing_time": "calculated_by_searcher"
            })
            
            await self.publish_progress(
                task_id,
                "websearch_complete",
                f"Search completed with {result.get('total_results', 0)} results",
                100
            )
            
            return result
            
        except Exception as e:
            error_result = {
                "task_id": task_id,
                "agent": "websearch", 
                "query": query,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.publish_progress(
                task_id,
                "websearch_error",
                f"Search failed: {str(e)}",
                -1
            )
            
            logger.error(f"❌ Search task failed for {task_id}: {e}")
            return error_result
    
    async def handle_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming RabbitMQ message"""
        async with message.process():
            try:
                # Parse message
                task_data = json.loads(message.body.decode())
                task_id = task_data.get("task_id", "unknown")
                
                logger.info(f"🔍 Processing search task: {task_id}")
                
                # Process the search task
                result = await self.process_search_task(task_data)
                
                # Publish result
                await self.publish_result(task_id, result)
                
                logger.info(f"✅ Completed search task: {task_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in message: {e}")
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
    
    async def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        if not self.connection:
            await self.initialize()
        
        try:
            self.consuming = True
            logger.info(f"🎯 Starting to consume from queue: {settings.QUEUE_NAME}")
            
            # Start consuming
            await self.queue.consume(self.handle_message)
            
            # Keep consuming until stopped
            while self.consuming:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error in message consumption: {e}")
            raise
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.consuming = False
        logger.info("🛑 Stopping message consumption")
    
    async def close(self):
        """Close connections"""
        try:
            self.consuming = False
            
            if self.channel:
                await self.channel.close()
            
            if self.connection:
                await self.connection.close()
            
            if self.redis_client:
                await self.redis_client.aclose()
            
            logger.info("✅ Connections closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing connections: {e}")
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        try:
            if not self.queue:
                return {"status": "disconnected"}
            
            queue_info = await self.queue.channel.queue_declare(
                settings.QUEUE_NAME, 
                passive=True
            )
            
            return {
                "queue_name": settings.QUEUE_NAME,
                "message_count": queue_info.queue.message_count,
                "consumer_count": queue_info.queue.consumer_count,
                "status": "connected" if self.consuming else "disconnected"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting queue status: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 
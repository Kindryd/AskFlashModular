import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

import aio_pika
from aio_pika import connect_robust, Message, ExchangeType
import redis.asyncio as redis

from core.config import settings
from services.content_moderator import ContentModerator

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """RabbitMQ consumer for content moderation tasks"""
    
    def __init__(self, content_moderator: ContentModerator):
        self.content_moderator = content_moderator
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
            await self.channel.set_qos(prefetch_count=settings.MAX_CONCURRENT_CHECKS)
            
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
                    "agent": "moderator",
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
        """Publish moderation result back to MCP"""
        try:
            result_data = {
                "task_id": task_id,
                "agent": "moderator",
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            # Store result in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"moderator_result:{task_id}",
                    3600,  # 1 hour TTL
                    json.dumps(result_data)
                )
                
                # Publish completion event
                await self.redis_client.publish(
                    "ai:moderator:complete",
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
                    headers={"task_id": task_id, "agent": "moderator"}
                )
                
                await self.channel.default_exchange.publish(
                    message,
                    routing_key=settings.RESPONSE_QUEUE
                )
            
            logger.info(f"✅ Result published for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish result: {e}")
    
    async def process_moderation_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a content moderation task"""
        task_id = task_data.get("task_id", "unknown")
        content = task_data.get("content", "")
        content_type = task_data.get("content_type", "text")
        moderation_type = task_data.get("moderation_type", "content")
        context = task_data.get("context", {})
        
        try:
            await self.publish_progress(
                task_id, 
                "moderation_start", 
                f"Starting moderation of {content_type} content",
                0
            )
            
            if moderation_type == "ai_response":
                # Special handling for AI response validation
                query = context.get("query", "")
                sources = context.get("sources", [])
                
                await self.publish_progress(
                    task_id,
                    "ai_response_validation",
                    "Validating AI response content and sources...",
                    25
                )
                
                result = await self.content_moderator.validate_ai_response(
                    content, query, sources
                )
                
            else:
                # Standard content moderation
                await self.publish_progress(
                    task_id,
                    "content_moderation",
                    "Performing comprehensive content moderation...",
                    25
                )
                
                result = await self.content_moderator.moderate_content(
                    content, content_type, context
                )
            
            await self.publish_progress(
                task_id,
                "moderation_analysis",
                "Analyzing moderation results...",
                75
            )
            
            # Add task metadata to result
            result.update({
                "task_id": task_id,
                "agent": "moderator",
                "moderation_type": moderation_type,
                "content_type": content_type
            })
            
            # Determine final status
            if result.get("approved", False):
                status_message = f"Content approved (confidence: {result.get('confidence', 0):.2f})"
            else:
                status_message = f"Content blocked: {result.get('reason', 'Unknown reason')}"
            
            await self.publish_progress(
                task_id,
                "moderation_complete",
                status_message,
                100
            )
            
            return result
            
        except Exception as e:
            error_result = {
                "task_id": task_id,
                "agent": "moderator",
                "content_type": content_type,
                "approved": False,
                "error": str(e),
                "reason": f"Moderation failed: {str(e)}",
                "confidence": 0.0,
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.publish_progress(
                task_id,
                "moderation_error",
                f"Moderation failed: {str(e)}",
                -1
            )
            
            logger.error(f"❌ Moderation task failed for {task_id}: {e}")
            return error_result
    
    async def handle_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming RabbitMQ message"""
        async with message.process():
            try:
                # Parse message
                task_data = json.loads(message.body.decode())
                task_id = task_data.get("task_id", "unknown")
                
                logger.info(f"🛡️ Processing moderation task: {task_id}")
                
                # Process the moderation task
                result = await self.process_moderation_task(task_data)
                
                # Publish result
                await self.publish_result(task_id, result)
                
                logger.info(f"✅ Completed moderation task: {task_id}")
                
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
"""
Message Broker for AskFlash MCP Architecture

This service handles all messaging between MCP components through RabbitMQ and Redis.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
import aio_pika
import redis.asyncio as aioredis
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

class MessageBroker:
    """
    Unified message broker for RabbitMQ and Redis
    
    Responsibilities:
    - RabbitMQ task queue management
    - Redis pub/sub for real-time events
    - Message routing and delivery
    - Connection management and retries
    """
    
    def __init__(self):
        self.rabbitmq_connection: Optional[aio_pika.RobustConnection] = None
        self.rabbitmq_channel: Optional[aio_pika.Channel] = None
        self.redis: Optional[aioredis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.rabbitmq_url = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@localhost:5672/"
        self.redis_url = f"redis://localhost:6379"
        
        # Queue configuration
        self.queue_config = {
            "intent.task": {"routing_key": "intent.task", "durable": True},
            "embedding.task": {"routing_key": "embedding.task", "durable": True},
            "executor.task": {"routing_key": "executor.task", "durable": True},
            "moderator.task": {"routing_key": "moderator.task", "durable": True},
            "websearch.task": {"routing_key": "websearch.task", "durable": True},
            "mcp.responses": {"routing_key": "mcp.responses", "durable": True}
        }
    
    async def connect(self):
        """Initialize connections to RabbitMQ and Redis"""
        try:
            # Connect to RabbitMQ
            await self._connect_rabbitmq()
            
            # Connect to Redis
            await self._connect_redis()
            
            logger.info("✅ Message Broker connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect Message Broker: {e}")
            raise
    
    async def _connect_rabbitmq(self):
        """Connect to RabbitMQ with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.rabbitmq_connection = await aio_pika.connect_robust(
                    self.rabbitmq_url,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                
                self.rabbitmq_channel = await self.rabbitmq_connection.channel()
                
                # Set QoS for load balancing
                await self.rabbitmq_channel.set_qos(prefetch_count=1)
                
                logger.info(f"✅ Connected to RabbitMQ on attempt {attempt + 1}")
                return
                
            except Exception as e:
                logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise
    
    async def _connect_redis(self):
        """Connect to Redis"""
        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                password="askflash123"
            )
            
            # Test connection
            await self.redis.ping()
            
            logger.info("✅ Connected to Redis")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def publish_task(self, queue_name: str, payload: Dict[str, Any]) -> bool:
        """
        Publish task to RabbitMQ queue
        
        Args:
            queue_name: Target queue name
            payload: Task payload
            
        Returns:
            True if published successfully
        """
        try:
            if not self.rabbitmq_channel:
                raise Exception("RabbitMQ not connected")
            
            queue_config = self.queue_config.get(queue_name)
            if not queue_config:
                raise Exception(f"Unknown queue: {queue_name}")
            
            # Declare queue (idempotent)
            queue = await self.rabbitmq_channel.declare_queue(
                queue_name,
                durable=queue_config["durable"]
            )
            
            # Prepare message
            message_body = json.dumps(payload)
            message = aio_pika.Message(
                message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                timestamp=datetime.utcnow()
            )
            
            # Publish to exchange
            await self.rabbitmq_channel.default_exchange.publish(
                message,
                routing_key=queue_name
            )
            
            logger.debug(f"📤 Published to {queue_name}: {payload.get('task_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish to {queue_name}: {e}")
            return False
    
    async def publish_event(self, channel: str, payload: Dict[str, Any]) -> bool:
        """
        Publish event to Redis pub/sub
        
        Args:
            channel: Redis channel name
            payload: Event payload
            
        Returns:
            True if published successfully
        """
        try:
            if not self.redis:
                raise Exception("Redis not connected")
            
            message = json.dumps(payload)
            await self.redis.publish(channel, message)
            
            logger.debug(f"📡 Published event to {channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event to {channel}: {e}")
            return False
    
    async def consume_queue(
        self, 
        queue_name: str, 
        callback: Callable,
        auto_ack: bool = False
    ):
        """
        Start consuming from RabbitMQ queue
        
        Args:
            queue_name: Queue to consume from
            callback: Message handler function
            auto_ack: Whether to auto-acknowledge messages
        """
        try:
            if not self.rabbitmq_channel:
                raise Exception("RabbitMQ not connected")
            
            queue_config = self.queue_config.get(queue_name)
            if not queue_config:
                raise Exception(f"Unknown queue: {queue_name}")
            
            # Declare queue
            queue = await self.rabbitmq_channel.declare_queue(
                queue_name,
                durable=queue_config["durable"]
            )
            
            # Set up consumer
            async def message_handler(message: aio_pika.IncomingMessage):
                try:
                    # Decode message
                    payload = json.loads(message.body.decode())
                    
                    # Process message
                    success = await callback(payload)
                    
                    # Acknowledge based on result
                    if auto_ack or success:
                        await message.ack()
                    else:
                        await message.nack(requeue=True)
                        
                except Exception as e:
                    logger.error(f"❌ Error processing message from {queue_name}: {e}")
                    await message.nack(requeue=False)  # Dead letter
            
            # Start consuming
            await queue.consume(message_handler)
            
            logger.info(f"🔄 Started consuming from queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to consume from {queue_name}: {e}")
            raise
    
    async def subscribe_event(
        self, 
        channel_pattern: str, 
        callback: Callable
    ):
        """
        Subscribe to Redis pub/sub events
        
        Args:
            channel_pattern: Redis channel pattern to subscribe to
            callback: Event handler function
        """
        try:
            if not self.redis:
                raise Exception("Redis not connected")
            
            # Add to subscribers
            if channel_pattern not in self.subscribers:
                self.subscribers[channel_pattern] = []
            self.subscribers[channel_pattern].append(callback)
            
            # Create pub/sub
            pubsub = self.redis.pubsub()
            await pubsub.psubscribe(channel_pattern)
            
            logger.info(f"📡 Subscribed to Redis pattern: {channel_pattern}")
            
            # Start listening
            async def listen():
                try:
                    async for message in pubsub.listen():
                        if message["type"] == "pmessage":
                            try:
                                payload = json.loads(message["data"])
                                await callback(message["channel"], payload)
                            except Exception as e:
                                logger.error(f"❌ Error handling pub/sub message: {e}")
                except Exception as e:
                    logger.error(f"❌ Error in pub/sub listener: {e}")
            
            # Start listener task
            asyncio.create_task(listen())
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to {channel_pattern}: {e}")
            raise
    
    async def wait_for_event(
        self, 
        channel: str, 
        task_id: str, 
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for specific event on Redis channel
        
        Args:
            channel: Redis channel to monitor
            task_id: Task ID to match
            timeout: Timeout in seconds
            
        Returns:
            Event payload when received
        """
        try:
            if not self.redis:
                raise Exception("Redis not connected")
            
            # Create pub/sub
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            
            # Wait for matching message
            async def wait_for_message():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            payload = json.loads(message["data"])
                            if payload.get("task_id") == task_id:
                                return payload
                        except (json.JSONDecodeError, KeyError):
                            continue
                return None
            
            # Wait with timeout
            result = await asyncio.wait_for(wait_for_message(), timeout=timeout)
            await pubsub.unsubscribe(channel)
            
            return result or {}
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout waiting for event on {channel} for task {task_id}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error waiting for event: {e}")
            return {}
    
    async def get_queue_status(self, queue_name: str) -> Dict[str, Any]:
        """
        Get queue status information
        
        Args:
            queue_name: Queue to check
            
        Returns:
            Queue status information
        """
        try:
            if not self.rabbitmq_channel:
                raise Exception("RabbitMQ not connected")
            
            # Declare queue to get info
            queue = await self.rabbitmq_channel.declare_queue(
                queue_name,
                durable=self.queue_config.get(queue_name, {}).get("durable", True),
                passive=True  # Don't create, just get info
            )
            
            return {
                "name": queue_name,
                "message_count": queue.declaration_result.message_count,
                "consumer_count": queue.declaration_result.consumer_count,
                "durable": self.queue_config.get(queue_name, {}).get("durable", True)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting queue status for {queue_name}: {e}")
            return {"name": queue_name, "error": str(e)}
    
    async def purge_queue(self, queue_name: str) -> bool:
        """
        Purge all messages from queue
        
        Args:
            queue_name: Queue to purge
            
        Returns:
            True if purged successfully
        """
        try:
            if not self.rabbitmq_channel:
                raise Exception("RabbitMQ not connected")
            
            queue = await self.rabbitmq_channel.declare_queue(
                queue_name,
                durable=self.queue_config.get(queue_name, {}).get("durable", True)
            )
            
            await queue.purge()
            
            logger.info(f"🧹 Purged queue: {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error purging queue {queue_name}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on message broker
        
        Returns:
            Health status information
        """
        status = {
            "rabbitmq": {"connected": False, "channel_open": False},
            "redis": {"connected": False},
            "overall": "unhealthy"
        }
        
        try:
            # Check RabbitMQ
            if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
                status["rabbitmq"]["connected"] = True
                if self.rabbitmq_channel and not self.rabbitmq_channel.is_closed:
                    status["rabbitmq"]["channel_open"] = True
            
            # Check Redis
            if self.redis:
                await self.redis.ping()
                status["redis"]["connected"] = True
            
            # Overall status
            if (status["rabbitmq"]["connected"] and 
                status["rabbitmq"]["channel_open"] and 
                status["redis"]["connected"]):
                status["overall"] = "healthy"
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            status["error"] = str(e)
        
        return status
    
    async def close(self):
        """Close all connections"""
        try:
            if self.rabbitmq_connection:
                await self.rabbitmq_connection.close()
                logger.info("🔌 Closed RabbitMQ connection")
            
            if self.redis:
                await self.redis.close()
                logger.info("🔌 Closed Redis connection")
                
        except Exception as e:
            logger.error(f"❌ Error closing connections: {e}")

# Message formatting utilities
def format_task_message(
    task_id: str,
    stage: str,
    query: str,
    user_id: str,
    context: str = "",
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Format standardized task message"""
    return {
        "task_id": task_id,
        "stage": stage,
        "query": query,
        "user_id": user_id,
        "context": context,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0"
    }

def format_event_message(
    event_type: str,
    task_id: str,
    data: Dict[str, Any],
    source: str = "mcp"
) -> Dict[str, Any]:
    """Format standardized event message"""
    return {
        "event_type": event_type,
        "task_id": task_id,
        "source": source,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0"
    } 
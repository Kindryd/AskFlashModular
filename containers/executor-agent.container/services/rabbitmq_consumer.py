"""
RabbitMQ Consumer for Executor Agent

This service consumes reasoning tasks from RabbitMQ and coordinates
their processing through the AI Executor.
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any

import aio_pika
import redis.asyncio as redis
from aio_pika import Message, IncomingMessage

from core.config import settings
from services.ai_executor import AIExecutor

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """
    RabbitMQ consumer for AI reasoning tasks
    
    Responsibilities:
    - Connect to RabbitMQ and consume from executor.task queue
    - Process AI reasoning requests
    - Publish results to appropriate channels
    - Handle errors and retries
    """
    
    def __init__(self, rabbitmq_url: str, ai_executor: AIExecutor, redis_client: redis.Redis):
        self.rabbitmq_url = rabbitmq_url
        self.ai_executor = ai_executor
        self.redis = redis_client
        
        # Connection state
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.is_consuming = False
        self.start_time = time.time()
        
        # Processing stats
        self.processed_count = 0
        self.error_count = 0
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    @property
    def uptime_seconds(self) -> int:
        """Calculate uptime in seconds"""
        return int(time.time() - self.start_time)
    
    async def connect(self):
        """Establish RabbitMQ connection"""
        try:
            logger.info(f"🔗 Connecting to RabbitMQ: {self.rabbitmq_url}")
            
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=60,
                reconnect_interval=settings.rabbitmq_reconnect_delay
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)
            
            # Declare queue (should already exist from infrastructure setup)
            self.queue = await self.channel.declare_queue(
                settings.rabbitmq_queue,
                durable=True
            )
            
            logger.info(f"✅ Connected to RabbitMQ queue: {settings.rabbitmq_queue}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise
    
    async def start_consuming(self):
        """Start consuming messages from the queue"""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        try:
            logger.info(f"🎯 Starting to consume from {settings.rabbitmq_queue}")
            
            # Start consuming with callback
            await self.queue.consume(self._process_message, no_ack=False)
            self.is_consuming = True
            
            logger.info("📥 Executor Agent is now consuming messages...")
            
            # Keep the consumer running
            while self.is_consuming:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error in message consumption: {e}")
            self.is_consuming = False
            raise
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        try:
            self.is_consuming = False
            
            # Wait for active tasks to complete (with timeout)
            if self.active_tasks:
                logger.info(f"⏳ Waiting for {len(self.active_tasks)} active tasks to complete...")
                await asyncio.wait_for(
                    asyncio.gather(*self.active_tasks.values(), return_exceptions=True),
                    timeout=60
                )
            
            # Close RabbitMQ connection
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
                
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                
            logger.info("🛑 RabbitMQ consumer stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping consumer: {e}")
    
    async def _process_message(self, message: IncomingMessage):
        """Process individual message from queue"""
        async with message.process():
            try:
                # Parse message
                message_data = json.loads(message.body.decode())
                task_id = message_data.get("task_id")
                
                if not task_id:
                    logger.error("❌ Received message without task_id")
                    return
                
                logger.info(f"📥 Processing executor task: {task_id}")
                
                # Create task for processing
                task = asyncio.create_task(self._handle_executor_task(message_data))
                self.active_tasks[task_id] = task
                
                # Wait for completion
                await task
                
                # Cleanup
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                
                self.processed_count += 1
                logger.info(f"✅ Completed executor task: {task_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in message: {e}")
                self.error_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                self.error_count += 1
                
                # Try to extract task_id for error reporting
                try:
                    message_data = json.loads(message.body.decode())
                    task_id = message_data.get("task_id")
                    if task_id:
                        await self._report_task_error(task_id, str(e))
                except:
                    pass
    
    async def _handle_executor_task(self, message_data: Dict[str, Any]):
        """Handle individual AI reasoning task"""
        task_id = message_data["task_id"]
        
        start_time = time.time()
        
        try:
            logger.info(f"🤖 Starting AI reasoning for task {task_id}")
            
            # Validate required fields
            query = message_data.get("query", "")
            if not query:
                raise ValueError("Query is required for AI reasoning")
            
            # Update task status in Redis
            await self._update_task_status(task_id, "processing", "AI reasoning in progress")
            
            # Gather additional context from Redis
            reasoning_request = await self._prepare_reasoning_request(task_id, message_data)
            
            # Perform AI reasoning
            execution_result = await self.ai_executor.execute_reasoning(
                task_id=task_id,
                reasoning_request=reasoning_request
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            execution_result["metadata"]["processing_time_ms"] = processing_time_ms
            
            # Publish results
            await self._publish_execution_result(task_id, execution_result)
            
            # Update task status to completed
            await self._update_task_status(
                task_id, 
                "completed", 
                f"AI reasoning completed in {processing_time_ms}ms"
            )
            
            logger.info(f"✅ AI reasoning completed for task {task_id} in {processing_time_ms}ms")
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ AI reasoning failed for task {task_id}: {e}")
            
            await self._report_task_error(task_id, str(e))
            raise
    
    async def _prepare_reasoning_request(self, task_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive reasoning request with context from Redis"""
        
        reasoning_request = {
            "query": message_data.get("query", ""),
            "context": message_data.get("context", ""),
            "documents": message_data.get("documents", []),
            "strategy": {},
            "intent_analysis": {}
        }
        
        try:
            # Get intent analysis if available
            intent_key = f"intent_result:{task_id}"
            intent_data = await self.redis.get(intent_key)
            if intent_data:
                intent_result = json.loads(intent_data)
                reasoning_request["intent_analysis"] = intent_result.get("intent_classification", {})
                reasoning_request["strategy"] = intent_result.get("processing_strategy", {})
                reasoning_request["strategy"]["complexity_level"] = intent_result.get("complexity_assessment", {}).get("complexity_level", "medium")
            
            # Get embedding results if available
            embedding_key = f"embedding_result:{task_id}"
            embedding_data = await self.redis.get(embedding_key)
            if embedding_data:
                embedding_result = json.loads(embedding_data)
                documents = embedding_result.get("documents", [])
                if documents:
                    reasoning_request["documents"] = documents
            
            # Get web search results if available
            web_search_key = f"websearch_result:{task_id}"
            web_search_data = await self.redis.get(web_search_key)
            if web_search_data:
                web_search_result = json.loads(web_search_data)
                web_documents = web_search_result.get("documents", [])
                # Merge with existing documents
                reasoning_request["documents"].extend(web_documents)
            
            # Get task context
            task_key = f"task:{task_id}:context"
            task_context = await self.redis.get(task_key)
            if task_context:
                context_data = json.loads(task_context)
                if context_data and not reasoning_request["context"]:
                    reasoning_request["context"] = str(context_data)
            
            logger.info(f"Prepared reasoning request with {len(reasoning_request['documents'])} documents")
            
        except Exception as e:
            logger.warning(f"Failed to gather additional context for {task_id}: {e}")
        
        return reasoning_request
    
    async def _publish_execution_result(self, task_id: str, execution_result: Dict[str, Any]):
        """Publish AI execution result"""
        try:
            # Store full execution result in Redis
            result_key = f"executor_result:{task_id}"
            await self.redis.setex(
                result_key,
                600,  # 10 minute TTL
                json.dumps(execution_result)
            )
            
            # Publish completion event
            completion_data = {
                "task_id": task_id,
                "stage": "executor_reasoning",
                "status": "completed",
                "result_summary": {
                    "confidence_score": execution_result["response"]["confidence_score"],
                    "word_count": execution_result["response"]["word_count"],
                    "citations": len(execution_result["response"]["citations"]),
                    "model_used": execution_result["reasoning_metadata"]["model_used"],
                    "documents_processed": execution_result["reasoning_metadata"]["documents_processed"]
                },
                "next_stage": "moderation",
                "timestamp": execution_result["metadata"]["execution_timestamp"]
            }
            
            # Publish to MCP completion channel
            completion_channel = f"ai:execution:complete"
            await self.redis.publish(completion_channel, json.dumps(completion_data))
            
            # Also publish to task-specific progress channel
            progress_channel = f"ai:progress:{task_id}"
            await self.redis.publish(progress_channel, json.dumps({
                "task_id": task_id,
                "agent": "ai_executor",
                "stage": "completed",
                "message": f"AI reasoning completed with {execution_result['response']['confidence_score']:.2f} confidence",
                "progress_data": completion_data["result_summary"]
            }))
            
            logger.info(f"📤 Published execution result for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish execution result for task {task_id}: {e}")
            raise
    
    async def _update_task_status(self, task_id: str, status: str, message: str):
        """Update task status in Redis"""
        try:
            # Get current task data
            task_key = f"task:{task_id}"
            task_data_str = await self.redis.get(task_key)
            
            if task_data_str:
                task_data = json.loads(task_data_str)
                
                # Update status if we're handling executor reasoning stage
                if task_data.get("current_stage") == "executor_reasoning":
                    if status == "completed":
                        # Move to completed stages
                        task_data["completed_stages"].append("executor_reasoning")
                        task_data["current_stage"] = "moderation"  # Next stage
                    
                    task_data["updated_at"] = message
                    
                    # Save updated task data
                    await self.redis.setex(task_key, 600, json.dumps(task_data))
            
        except Exception as e:
            logger.warning(f"Failed to update task status for {task_id}: {e}")
    
    async def _report_task_error(self, task_id: str, error_message: str):
        """Report task error"""
        try:
            error_data = {
                "task_id": task_id,
                "agent": "ai_executor",
                "stage": "executor_reasoning",
                "error": error_message,
                "timestamp": time.time()
            }
            
            # Publish error event
            error_channel = f"ai:error:{task_id}"
            await self.redis.publish(error_channel, json.dumps(error_data))
            
            # Update task status
            await self._update_task_status(task_id, "failed", f"AI reasoning failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to report error for task {task_id}: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        return {
            "is_consuming": self.is_consuming,
            "uptime_seconds": self.uptime_seconds,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "active_tasks": len(self.active_tasks),
            "queue_name": settings.rabbitmq_queue,
            "connection_status": "connected" if (self.connection and not self.connection.is_closed) else "disconnected"
        } 
"""
RabbitMQ Consumer for Intent Agent

This service consumes intent analysis tasks from RabbitMQ and coordinates
their processing through the Intent Analyzer.
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
from services.intent_analyzer import IntentAnalyzer

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """
    RabbitMQ consumer for intent analysis tasks
    
    Responsibilities:
    - Connect to RabbitMQ and consume from intent.task queue
    - Process intent analysis requests
    - Publish results to appropriate channels
    - Handle errors and retries
    """
    
    def __init__(self, rabbitmq_url: str, intent_analyzer: IntentAnalyzer, redis_client: redis.Redis):
        self.rabbitmq_url = rabbitmq_url
        self.intent_analyzer = intent_analyzer
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
            
            logger.info("📥 Intent Agent is now consuming messages...")
            
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
                    timeout=30
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
                
                logger.info(f"📥 Processing intent task: {task_id}")
                
                # Create task for processing
                task = asyncio.create_task(self._handle_intent_task(message_data))
                self.active_tasks[task_id] = task
                
                # Wait for completion
                await task
                
                # Cleanup
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                
                self.processed_count += 1
                logger.info(f"✅ Completed intent task: {task_id}")
                
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
    
    async def _handle_intent_task(self, message_data: Dict[str, Any]):
        """Handle individual intent analysis task"""
        task_id = message_data["task_id"]
        query = message_data.get("query", "")
        user_id = message_data.get("user_id", "unknown")
        
        start_time = time.time()
        
        try:
            logger.info(f"🧠 Starting intent analysis for task {task_id}")
            
            # Validate required fields
            if not query:
                raise ValueError("Query is required for intent analysis")
            
            # Update task status in Redis
            await self._update_task_status(task_id, "processing", "Intent analysis in progress")
            
            # Perform intent analysis
            analysis_result = await self.intent_analyzer.analyze_intent(
                task_id=task_id,
                query=query,
                user_id=user_id
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            analysis_result["metadata"]["processing_time_ms"] = processing_time_ms
            
            # Publish results
            await self._publish_analysis_result(task_id, analysis_result)
            
            # Update task status to completed
            await self._update_task_status(
                task_id, 
                "completed", 
                f"Intent analysis completed in {processing_time_ms}ms"
            )
            
            logger.info(f"✅ Intent analysis completed for task {task_id} in {processing_time_ms}ms")
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Intent analysis failed for task {task_id}: {e}")
            
            await self._report_task_error(task_id, str(e))
            raise
    
    async def _publish_analysis_result(self, task_id: str, analysis_result: Dict[str, Any]):
        """Publish intent analysis result"""
        try:
            # Store full analysis in Redis
            analysis_key = f"intent_result:{task_id}"
            await self.redis.setex(
                analysis_key,
                600,  # 10 minute TTL
                json.dumps(analysis_result)
            )
            
            # Publish completion event
            completion_data = {
                "task_id": task_id,
                "stage": "intent_analysis",
                "status": "completed",
                "analysis_summary": {
                    "primary_intent": analysis_result["intent_classification"]["primary_intent"],
                    "complexity_level": analysis_result["complexity_assessment"]["complexity_level"],
                    "strategy": analysis_result["processing_strategy"]["approach"],
                    "web_search_required": analysis_result["processing_strategy"]["web_search_required"],
                    "estimated_processing_time_ms": analysis_result["complexity_assessment"]["estimated_processing_time_ms"]
                },
                "next_stage": self._determine_next_stage(analysis_result),
                "timestamp": analysis_result["metadata"]["analysis_timestamp"]
            }
            
            # Publish to MCP completion channel
            completion_channel = f"ai:intent:complete"
            await self.redis.publish(completion_channel, json.dumps(completion_data))
            
            # Also publish to task-specific progress channel
            progress_channel = f"ai:progress:{task_id}"
            await self.redis.publish(progress_channel, json.dumps({
                "task_id": task_id,
                "agent": "intent_analyzer",
                "stage": "completed",
                "message": f"Intent analysis completed - {analysis_result['intent_classification']['primary_intent']} intent detected",
                "progress_data": completion_data["analysis_summary"]
            }))
            
            logger.info(f"📤 Published intent analysis result for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish analysis result for task {task_id}: {e}")
            raise
    
    def _determine_next_stage(self, analysis_result: Dict[str, Any]) -> str:
        """Determine the next processing stage based on analysis"""
        strategy = analysis_result["processing_strategy"]
        
        if strategy["web_search_required"]:
            return "web_search"
        else:
            return "embedding_lookup"
    
    async def _update_task_status(self, task_id: str, status: str, message: str):
        """Update task status in Redis"""
        try:
            # Get current task data
            task_key = f"task:{task_id}"
            task_data_str = await self.redis.get(task_key)
            
            if task_data_str:
                task_data = json.loads(task_data_str)
                
                # Update status if we're handling intent analysis stage
                if task_data.get("current_stage") == "intent_analysis":
                    if status == "completed":
                        # Move to completed stages
                        task_data["completed_stages"].append("intent_analysis")
                        
                        # Determine next stage from analysis
                        analysis_key = f"intent_result:{task_id}"
                        analysis_str = await self.redis.get(analysis_key)
                        if analysis_str:
                            analysis = json.loads(analysis_str)
                            next_stage = self._determine_next_stage(analysis)
                            task_data["current_stage"] = next_stage
                        else:
                            task_data["current_stage"] = "embedding_lookup"  # default
                    
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
                "agent": "intent_analyzer",
                "stage": "intent_analysis",
                "error": error_message,
                "timestamp": time.time()
            }
            
            # Publish error event
            error_channel = f"ai:error:{task_id}"
            await self.redis.publish(error_channel, json.dumps(error_data))
            
            # Update task status
            await self._update_task_status(task_id, "failed", f"Intent analysis failed: {error_message}")
            
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
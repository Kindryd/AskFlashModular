"""
Executor Agent for AskFlash MCP Architecture

This agent processes main reasoning tasks from the MCP system.
It performs comprehensive AI reasoning using GPT-4 or GPT-3.5-turbo
based on context, documents, and intent analysis.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import aio_pika
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI

from core.config import settings
from services.ai_executor import AIExecutor
from services.rabbitmq_consumer import RabbitMQConsumer
from api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global components
ai_executor = None
consumer = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global ai_executor, consumer, redis_client
    
    try:
        # Initialize Redis connection
        redis_client = redis.from_url(
            settings.redis_url, 
            password=settings.redis_password,
            decode_responses=True
        )
        
        # Initialize AI Executor
        ai_executor = AIExecutor(
            openai_api_key=settings.openai_api_key,
            redis_client=redis_client
        )
        
        # Initialize RabbitMQ Consumer
        consumer = RabbitMQConsumer(
            rabbitmq_url=settings.rabbitmq_url,
            ai_executor=ai_executor,
            redis_client=redis_client
        )
        
        # Start consuming messages
        consumer_task = asyncio.create_task(consumer.start_consuming())
        
        logger.info("🤖 Executor Agent started successfully")
        logger.info(f"🔗 Connected to Redis: {settings.redis_url}")
        logger.info(f"🐰 Connected to RabbitMQ: {settings.rabbitmq_url}")
        logger.info("📥 Listening for executor.task messages...")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Executor Agent: {e}")
        raise
    finally:
        # Cleanup
        if consumer:
            await consumer.stop_consuming()
        if redis_client:
            await redis_client.close()
        logger.info("🔄 Executor Agent shut down completed")

# Create FastAPI app
app = FastAPI(
    title="AskFlash Executor Agent",
    description="AI reasoning agent for the AskFlash MCP system",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AskFlash Executor Agent",
        "version": "1.0.0",
        "status": "running",
        "description": "AI reasoning agent for the AskFlash MCP system"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_status = "connected"
        try:
            await redis_client.ping()
        except Exception:
            redis_status = "disconnected"
        
        # Check RabbitMQ consumer status
        consumer_status = "running" if consumer and consumer.is_consuming else "stopped"
        
        # Check OpenAI API access
        openai_status = "available"
        try:
            if ai_executor:
                await ai_executor.client.models.list()
        except Exception:
            openai_status = "unavailable"
        
        health_data = {
            "service": "executor-agent",
            "status": "healthy" if all([
                redis_status == "connected",
                consumer_status == "running", 
                openai_status == "available"
            ]) else "unhealthy",
            "components": {
                "redis": redis_status,
                "rabbitmq_consumer": consumer_status,
                "openai": openai_status
            },
            "uptime_seconds": getattr(consumer, 'uptime_seconds', 0) if consumer else 0
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities"""
    return {
        "agent_type": "ai_executor",
        "capabilities": [
            "comprehensive_reasoning",
            "document_synthesis", 
            "multi_step_analysis",
            "contextual_response_generation",
            "source_attribution",
            "structured_output"
        ],
        "models": {
            "primary": "gpt-4",
            "fallback": "gpt-3.5-turbo-16k",
            "simple_tasks": "gpt-3.5-turbo"
        },
        "queue": "executor.task",
        "max_concurrent_tasks": 5,
        "average_processing_time_ms": 8000,
        "token_limits": {
            "gpt-4": 8192,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
    }

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🛑 Received signal {signum}, shutting down Executor Agent...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Run the application
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8011,
        log_level="info",
        access_log=True
    ) 
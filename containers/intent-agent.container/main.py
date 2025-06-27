"""
Intent Agent for AskFlash MCP Architecture

This agent processes intent analysis tasks from the MCP system.
It analyzes user queries to understand intent, extract key information,
and determine the best approach for processing.
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
from services.intent_analyzer import IntentAnalyzer
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
intent_analyzer = None
consumer = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global intent_analyzer, consumer, redis_client
    
    try:
        # Initialize Redis connection
        redis_client = redis.from_url(
            settings.redis_url, 
            password=settings.redis_password,
            decode_responses=True
        )
        
        # Initialize Intent Analyzer
        intent_analyzer = IntentAnalyzer(
            openai_api_key=settings.openai_api_key,
            redis_client=redis_client
        )
        
        # Initialize RabbitMQ Consumer
        consumer = RabbitMQConsumer(
            rabbitmq_url=settings.rabbitmq_url,
            intent_analyzer=intent_analyzer,
            redis_client=redis_client
        )
        
        # Start consuming messages
        consumer_task = asyncio.create_task(consumer.start_consuming())
        
        logger.info("🧠 Intent Agent started successfully")
        logger.info(f"🔗 Connected to Redis: {settings.redis_url}")
        logger.info(f"🐰 Connected to RabbitMQ: {settings.rabbitmq_url}")
        logger.info("📥 Listening for intent.task messages...")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Intent Agent: {e}")
        raise
    finally:
        # Cleanup
        if consumer:
            await consumer.stop_consuming()
        if redis_client:
            await redis_client.close()
        logger.info("🔄 Intent Agent shut down completed")

# Create FastAPI app
app = FastAPI(
    title="AskFlash Intent Agent",
    description="Intent analysis agent for the AskFlash MCP system",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AskFlash Intent Agent",
        "version": "1.0.0",
        "status": "running",
        "description": "Intent analysis agent for the AskFlash MCP system"
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
            if intent_analyzer:
                await intent_analyzer.client.models.list()
        except Exception:
            openai_status = "unavailable"
        
        health_data = {
            "service": "intent-agent",
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
        "agent_type": "intent_analyzer",
        "capabilities": [
            "query_analysis",
            "intent_classification", 
            "sub_question_generation",
            "complexity_assessment",
            "search_strategy_determination"
        ],
        "models": {
            "primary": "gpt-3.5-turbo",
            "fallback": "gpt-3.5-turbo-16k"
        },
        "queue": "intent.task",
        "max_concurrent_tasks": 10,
        "average_processing_time_ms": 2500
    }

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🛑 Received signal {signum}, shutting down Intent Agent...")
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
        port=8010,
        log_level="info",
        access_log=True
    ) 
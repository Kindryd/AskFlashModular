"""
Adaptive Learning Engine for AskFlash MCP Architecture

This container implements intelligent adaptation and learning capabilities:
- User persona building and preference learning
- Company knowledge evolution through interaction analysis  
- Pattern recognition and optimization suggestions
- Cross-user behavior analysis and insights
"""

import asyncio
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as aioredis
import asyncpg
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

from core.config import settings
from services.persona_builder import PersonaBuilder
from services.knowledge_evolution import KnowledgeEvolution
from services.pattern_analyzer import PatternAnalyzer
from services.adaptive_optimizer import AdaptiveOptimizer
from api.routes import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
persona_builder = None
knowledge_evolution = None
pattern_analyzer = None
adaptive_optimizer = None
redis_client = None
db_pool = None
qdrant_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global persona_builder, knowledge_evolution, pattern_analyzer, adaptive_optimizer
    global redis_client, db_pool, qdrant_client
    
    try:
        # Initialize database connection
        logger.info("🔗 Connecting to PostgreSQL...")
        db_pool = await asyncpg.create_pool(
            settings.POSTGRES_URL,
            min_size=2,
            max_size=10,
            command_timeout=30
        )
        
        # Initialize Redis connection
        logger.info("🔗 Connecting to Redis...")
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            password="askflash123"
        )
        await redis_client.ping()
        
        # Initialize Qdrant connection
        logger.info("🔗 Connecting to Qdrant...")
        qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Initialize adaptive learning collections in Qdrant
        await initialize_qdrant_collections()
        
        # Initialize core services
        logger.info("🧠 Initializing adaptive learning services...")
        persona_builder = PersonaBuilder(db_pool, redis_client, qdrant_client)
        knowledge_evolution = KnowledgeEvolution(db_pool, redis_client, qdrant_client)
        pattern_analyzer = PatternAnalyzer(db_pool, redis_client, qdrant_client)
        adaptive_optimizer = AdaptiveOptimizer(db_pool, redis_client, qdrant_client)
        
        # Start all services
        await persona_builder.initialize()
        await knowledge_evolution.initialize()
        await pattern_analyzer.initialize()
        await adaptive_optimizer.initialize()
        
        # Start background learning tasks
        asyncio.create_task(start_background_learning())
        
        logger.info("✅ Adaptive Learning Engine initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Adaptive Learning Engine: {e}")
        raise
    finally:
        # Cleanup
        if db_pool:
            await db_pool.close()
        if redis_client:
            await redis_client.close()
        if qdrant_client:
            await qdrant_client.close()
        logger.info("🧹 Adaptive Learning Engine cleanup completed")

async def initialize_qdrant_collections():
    """Initialize Qdrant collections for adaptive learning"""
    collections = [
        {
            "name": "user_personas",
            "description": "User interaction patterns and preferences",
            "vector_size": 384,  # sentence-transformers/all-MiniLM-L6-v2
        },
        {
            "name": "knowledge_insights", 
            "description": "Evolved company knowledge and insights",
            "vector_size": 384,
        },
        {
            "name": "conversation_patterns",
            "description": "Conversation flow and success patterns", 
            "vector_size": 384,
        },
        {
            "name": "context_relevance",
            "description": "Context relevance scoring patterns",
            "vector_size": 384,
        }
    ]
    
    for collection in collections:
        try:
            await qdrant_client.create_collection(
                collection_name=collection["name"],
                vectors_config=VectorParams(
                    size=collection["vector_size"],
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created Qdrant collection: {collection['name']}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"📂 Qdrant collection already exists: {collection['name']}")
            else:
                logger.error(f"❌ Failed to create collection {collection['name']}: {e}")

async def start_background_learning():
    """Start background learning and analysis tasks"""
    try:
        # Start periodic learning tasks
        asyncio.create_task(persona_builder.start_continuous_learning())
        asyncio.create_task(knowledge_evolution.start_knowledge_evolution())
        asyncio.create_task(pattern_analyzer.start_pattern_detection())
        asyncio.create_task(adaptive_optimizer.start_optimization_loop())
        
        logger.info("🔄 Background learning tasks started")
        
    except Exception as e:
        logger.error(f"❌ Failed to start background learning: {e}")

# FastAPI application
app = FastAPI(
    title="AskFlash Adaptive Learning Engine",
    description="Intelligent adaptation and learning system for personalized AI interactions",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Pydantic models for API
class LearningFeedback(BaseModel):
    user_id: str
    conversation_id: str
    query: str
    response: str
    rating: int  # 1-5 scale
    feedback_text: Optional[str] = None
    response_time_ms: int
    was_helpful: bool

class PersonaQuery(BaseModel):
    user_id: str
    include_preferences: bool = True
    include_patterns: bool = True
    include_expertise: bool = True

class KnowledgeInsight(BaseModel):
    topic: str
    insight_type: str  # "gap", "pattern", "optimization", "evolution"
    content: str
    confidence_score: float
    supporting_evidence: List[str]

class AdaptationRequest(BaseModel):
    user_id: str
    query: str
    context: str
    conversation_history: List[Dict[str, Any]]

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis connection
        await redis_client.ping()
        
        # Check Qdrant connection
        collections = await qdrant_client.get_collections()
        
        return {
            "status": "healthy",
            "services": {
                "database": "connected",
                "redis": "connected", 
                "qdrant": "connected",
                "collections": len(collections.collections)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

# Main API endpoints
@app.post("/api/v1/feedback")
async def record_feedback(feedback: LearningFeedback, background_tasks: BackgroundTasks):
    """Record user feedback for learning"""
    try:
        # Process feedback asynchronously
        background_tasks.add_task(
            persona_builder.process_feedback,
            feedback.dict()
        )
        background_tasks.add_task(
            knowledge_evolution.analyze_interaction,
            feedback.dict()
        )
        
        return {
            "status": "feedback_recorded",
            "message": "Feedback will be processed for learning",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to record feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/persona/{user_id}")
async def get_user_persona(user_id: str):
    """Get comprehensive user persona and preferences"""
    try:
        persona = await persona_builder.get_user_persona(user_id)
        
        if not persona:
            return {
                "user_id": user_id,
                "status": "new_user",
                "persona": {},
                "recommendations": ["Start building user preferences through interactions"]
            }
        
        return {
            "user_id": user_id,
            "status": "active",
            "persona": persona,
            "last_updated": persona.get("last_updated"),
            "confidence_score": persona.get("confidence_score", 0.0)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get user persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/insights/knowledge")
async def get_knowledge_insights():
    """Get evolved knowledge insights and patterns"""
    try:
        insights = await knowledge_evolution.get_latest_insights()
        
        return {
            "insights": insights,
            "total_count": len(insights),
            "categories": {
                "knowledge_gaps": len([i for i in insights if i["type"] == "gap"]),
                "successful_patterns": len([i for i in insights if i["type"] == "pattern"]),
                "optimization_opportunities": len([i for i in insights if i["type"] == "optimization"]),
                "emerging_topics": len([i for i in insights if i["type"] == "evolution"])
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get knowledge insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/adapt")
async def get_adaptation_recommendations(request: AdaptationRequest):
    """Get personalized adaptation recommendations for a user query"""
    try:
        recommendations = await adaptive_optimizer.get_adaptation_recommendations(
            user_id=request.user_id,
            query=request.query,
            context=request.context,
            conversation_history=request.conversation_history
        )
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations,
            "adaptation_confidence": recommendations.get("confidence", 0.0),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get adaptation recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/patterns")
async def get_behavior_patterns():
    """Get detected behavior patterns across all users"""
    try:
        patterns = await pattern_analyzer.get_detected_patterns()
        
        return {
            "patterns": patterns,
            "pattern_types": {
                "user_behavior": len([p for p in patterns if p["category"] == "user_behavior"]),
                "conversation_flow": len([p for p in patterns if p["category"] == "conversation_flow"]),
                "content_preference": len([p for p in patterns if p["category"] == "content_preference"]),
                "temporal": len([p for p in patterns if p["category"] == "temporal"])
            },
            "analysis_period": "last_7_days",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get behavior patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8015,
        reload=True,
        log_level="info"
    ) 
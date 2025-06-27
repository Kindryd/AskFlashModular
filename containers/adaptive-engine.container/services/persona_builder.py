"""
User Persona Builder - Learn user preferences and interaction patterns
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class PersonaBuilder:
    """
    Builds and maintains user personas through interaction analysis
    
    Features:
    - Interaction style profiling (technical vs simplified, direct vs detailed)
    - Domain expertise mapping (knowledge areas and gaps)
    - Communication preference learning
    - Temporal behavior pattern recognition
    """
    
    def __init__(self, db_pool, redis_client, qdrant_client):
        self.db_pool = db_pool
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.is_running = False
        
    async def initialize(self):
        """Initialize persona builder"""
        try:
            # Create database tables if they don't exist
            await self._create_persona_tables()
            
            # Set up Redis subscriptions for real-time learning
            await self._setup_redis_subscriptions()
            
            logger.info("✅ PersonaBuilder initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PersonaBuilder: {e}")
            raise
    
    async def _create_persona_tables(self):
        """Create persona-related database tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_personas (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) UNIQUE NOT NULL,
                    interaction_style JSONB DEFAULT '{}',
                    domain_expertise JSONB DEFAULT '{}',
                    communication_preferences JSONB DEFAULT '{}',
                    temporal_patterns JSONB DEFAULT '{}',
                    confidence_score FLOAT DEFAULT 0.0,
                    total_interactions INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS user_interaction_logs (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    query_complexity VARCHAR(50),
                    response_style VARCHAR(50),
                    user_satisfaction INTEGER, -- 1-5 scale
                    response_time_ms INTEGER,
                    topics JSONB DEFAULT '[]',
                    interaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_personas_user_id ON user_personas(user_id);
                CREATE INDEX IF NOT EXISTS idx_interaction_logs_user_id ON user_interaction_logs(user_id);
                CREATE INDEX IF NOT EXISTS idx_interaction_logs_time ON user_interaction_logs(interaction_at);
            """)
    
    async def _setup_redis_subscriptions(self):
        """Set up Redis subscriptions for real-time learning"""
        try:
            # Subscribe to conversation events
            pubsub = self.redis.pubsub()
            await pubsub.subscribe("conversation:ended", "ai:response_rated", "user:feedback_given")
            
            # Start background task to process events
            asyncio.create_task(self._process_redis_events(pubsub))
            
        except Exception as e:
            logger.error(f"Failed to setup Redis subscriptions: {e}")
    
    async def _process_redis_events(self, pubsub):
        """Process Redis events for real-time persona updates"""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._handle_interaction_event(data)
                    except Exception as e:
                        logger.warning(f"Failed to process Redis event: {e}")
        except Exception as e:
            logger.error(f"Redis event processing error: {e}")
    
    async def _handle_interaction_event(self, event_data: Dict[str, Any]):
        """Handle real-time interaction events"""
        try:
            user_id = event_data.get("user_id")
            if not user_id:
                return
            
            # Process different event types
            if "query" in event_data and "response" in event_data:
                await self._analyze_interaction(
                    user_id=user_id,
                    query=event_data["query"],
                    response=event_data["response"],
                    metadata=event_data
                )
                
        except Exception as e:
            logger.error(f"Failed to handle interaction event: {e}")
    
    async def process_feedback(self, feedback_data: Dict[str, Any]):
        """Process user feedback for persona learning"""
        try:
            user_id = feedback_data["user_id"]
            
            # Log interaction with feedback
            await self._log_interaction(
                user_id=user_id,
                query=feedback_data["query"],
                response=feedback_data["response"],
                satisfaction=feedback_data["rating"],
                response_time_ms=feedback_data["response_time_ms"],
                was_helpful=feedback_data["was_helpful"]
            )
            
            # Update persona immediately for high-confidence feedback
            if feedback_data["rating"] in [1, 5]:  # Strong positive or negative
                await self._update_persona_from_feedback(user_id, feedback_data)
            
            logger.info(f"Processed feedback for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
    
    async def _analyze_interaction(self, user_id: str, query: str, response: str, metadata: Dict[str, Any]):
        """Analyze interaction to extract persona insights"""
        try:
            # Analyze query complexity and style preference
            query_analysis = await self._analyze_query_style(query)
            
            # Analyze response effectiveness
            response_analysis = await self._analyze_response_effectiveness(response, metadata)
            
            # Extract domain topics
            topics = await self._extract_topics(query, response)
            
            # Update persona with new insights
            await self._update_persona_insights(
                user_id=user_id,
                query_analysis=query_analysis,
                response_analysis=response_analysis,
                topics=topics,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze interaction: {e}")
    
    async def _analyze_query_style(self, query: str) -> Dict[str, Any]:
        """Analyze user's query style and preferences"""
        query_length = len(query.split())
        
        # Simple heuristics for query style analysis
        style_indicators = {
            "technical_keywords": len([w for w in query.lower().split() 
                                     if w in ["api", "technical", "architecture", "implementation", "code"]]),
            "question_type": "direct" if query.strip().endswith("?") else "conversational",
            "complexity_level": "high" if query_length > 20 else "medium" if query_length > 10 else "low",
            "urgency_indicators": len([w for w in query.lower().split() 
                                     if w in ["urgent", "asap", "immediately", "quick", "fast"]]),
            "formality_level": "formal" if any(w in query.lower() for w in ["please", "could you", "would you"]) else "casual"
        }
        
        return style_indicators
    
    async def _analyze_response_effectiveness(self, response: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how effective the response was"""
        response_length = len(response.split())
        
        effectiveness_metrics = {
            "response_length": response_length,
            "detail_level": "detailed" if response_length > 100 else "moderate" if response_length > 50 else "brief",
            "code_examples": response.count("```") // 2,  # Number of code blocks
            "list_items": response.count("\n-") + response.count("\n*"),
            "confidence_score": metadata.get("confidence_score", 0.8),
            "response_time_ms": metadata.get("response_time_ms", 0)
        }
        
        return effectiveness_metrics
    
    async def _extract_topics(self, query: str, response: str) -> List[str]:
        """Extract topics from query and response"""
        # Simple keyword extraction - could be enhanced with NLP
        combined_text = f"{query} {response}".lower()
        
        # Common technical topics
        topic_keywords = {
            "authentication": ["auth", "login", "password", "token", "jwt"],
            "database": ["database", "sql", "postgres", "query", "table"],
            "api": ["api", "endpoint", "rest", "http", "request"],
            "security": ["security", "permission", "access", "secure"],
            "integration": ["integration", "connect", "webhook", "sync"],
            "performance": ["performance", "speed", "optimize", "cache"],
            "deployment": ["deploy", "docker", "container", "production"],
            "frontend": ["frontend", "ui", "react", "javascript", "css"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    async def _update_persona_insights(self, user_id: str, query_analysis: Dict, 
                                     response_analysis: Dict, topics: List[str], metadata: Dict):
        """Update user persona with new insights"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get existing persona
                existing = await conn.fetchrow(
                    "SELECT * FROM user_personas WHERE user_id = $1", user_id
                )
                
                if existing:
                    # Update existing persona
                    await self._merge_persona_data(conn, user_id, existing, 
                                                 query_analysis, response_analysis, topics)
                else:
                    # Create new persona
                    await self._create_new_persona(conn, user_id, query_analysis, 
                                                 response_analysis, topics)
                    
        except Exception as e:
            logger.error(f"Failed to update persona insights: {e}")
    
    async def _merge_persona_data(self, conn, user_id: str, existing, 
                                query_analysis: Dict, response_analysis: Dict, topics: List[str]):
        """Merge new data with existing persona"""
        # Weighted update of interaction style (more recent interactions have higher weight)
        current_style = existing["interaction_style"] or {}
        new_weight = 0.3  # 30% weight for new interaction
        
        merged_style = {
            "avg_query_length": self._weighted_average(
                current_style.get("avg_query_length", 0), 
                len(query_analysis.get("complexity_level", "").split()), 
                new_weight
            ),
            "technical_preference": self._weighted_average(
                current_style.get("technical_preference", 0.5),
                min(query_analysis.get("technical_keywords", 0) / 3, 1.0),
                new_weight
            ),
            "formality_level": query_analysis.get("formality_level", "casual"),
            "preferred_detail_level": response_analysis.get("detail_level", "moderate")
        }
        
        # Update domain expertise
        current_expertise = existing["domain_expertise"] or {}
        for topic in topics:
            current_expertise[topic] = current_expertise.get(topic, 0) + 1
        
        # Update temporal patterns
        current_temporal = existing["temporal_patterns"] or {}
        current_hour = datetime.now().hour
        hour_key = str(current_hour)
        current_temporal[hour_key] = current_temporal.get(hour_key, 0) + 1
        
        # Calculate confidence score
        total_interactions = existing["total_interactions"] + 1
        confidence_score = min(total_interactions / 20, 1.0)  # Max confidence after 20 interactions
        
        # Update database
        await conn.execute("""
            UPDATE user_personas SET
                interaction_style = $2,
                domain_expertise = $3,
                temporal_patterns = $4,
                confidence_score = $5,
                total_interactions = $6,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id, json.dumps(merged_style), json.dumps(current_expertise), 
             json.dumps(current_temporal), confidence_score, total_interactions)
    
    def _weighted_average(self, current_val: float, new_val: float, new_weight: float) -> float:
        """Calculate weighted average for persona updates"""
        return current_val * (1 - new_weight) + new_val * new_weight
    
    async def get_user_persona(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive user persona"""
        try:
            async with self.db_pool.acquire() as conn:
                persona = await conn.fetchrow(
                    "SELECT * FROM user_personas WHERE user_id = $1", user_id
                )
                
                if not persona:
                    return None
                
                # Get recent interaction patterns
                recent_interactions = await conn.fetch("""
                    SELECT * FROM user_interaction_logs 
                    WHERE user_id = $1 
                    ORDER BY interaction_at DESC 
                    LIMIT 10
                """, user_id)
                
                return {
                    "user_id": user_id,
                    "interaction_style": persona["interaction_style"],
                    "domain_expertise": persona["domain_expertise"],
                    "communication_preferences": persona["communication_preferences"],
                    "temporal_patterns": persona["temporal_patterns"],
                    "confidence_score": persona["confidence_score"],
                    "total_interactions": persona["total_interactions"],
                    "recent_interactions": [dict(r) for r in recent_interactions],
                    "last_updated": persona["updated_at"].isoformat(),
                    "persona_insights": await self._generate_persona_insights(persona)
                }
                
        except Exception as e:
            logger.error(f"Failed to get user persona: {e}")
            return None
    
    async def _generate_persona_insights(self, persona) -> Dict[str, str]:
        """Generate human-readable insights from persona data"""
        style = persona["interaction_style"] or {}
        expertise = persona["domain_expertise"] or {}
        
        insights = {
            "communication_style": f"Prefers {style.get('preferred_detail_level', 'moderate')} responses",
            "technical_level": "Technical" if style.get("technical_preference", 0) > 0.7 else "Non-technical",
            "top_domains": list(sorted(expertise.items(), key=lambda x: x[1], reverse=True)[:3]),
            "interaction_frequency": f"{persona['total_interactions']} total interactions",
            "confidence_level": f"{persona['confidence_score']:.1%} persona confidence"
        }
        
        return insights
    
    async def start_continuous_learning(self):
        """Start continuous learning background task"""
        self.is_running = True
        
        while self.is_running:
            try:
                await self._periodic_persona_update()
                await asyncio.sleep(30 * 60)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in continuous learning: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _periodic_persona_update(self):
        """Periodic update of all user personas"""
        try:
            # Get users who need persona updates
            async with self.db_pool.acquire() as conn:
                users_to_update = await conn.fetch("""
                    SELECT user_id FROM user_personas 
                    WHERE updated_at < NOW() - INTERVAL '24 hours'
                    OR confidence_score < 0.8
                    LIMIT 50
                """)
                
                for user_row in users_to_update:
                    user_id = user_row["user_id"]
                    await self._analyze_user_patterns(user_id)
                    
            logger.info(f"Updated personas for {len(users_to_update)} users")
            
        except Exception as e:
            logger.error(f"Failed periodic persona update: {e}")
    
    async def _analyze_user_patterns(self, user_id: str):
        """Deep analysis of user patterns for persona refinement"""
        # Implementation for advanced pattern analysis
        # This would include temporal analysis, preference drift detection, etc.
        pass 
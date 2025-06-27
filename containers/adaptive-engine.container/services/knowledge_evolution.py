"""
Knowledge Evolution - Learn and evolve company knowledge through interactions
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class KnowledgeEvolution:
    """
    Evolves company knowledge through interaction analysis
    
    Features:
    - FAQ pattern recognition from common questions
    - Knowledge gap detection when docs don't answer well
    - Concept relationship discovery
    - Success pattern learning from effective responses
    - Emerging topic detection
    """
    
    def __init__(self, db_pool, redis_client, qdrant_client):
        self.db_pool = db_pool
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.is_running = False
        
    async def initialize(self):
        """Initialize knowledge evolution system"""
        try:
            await self._create_knowledge_tables()
            await self._setup_knowledge_collections()
            
            logger.info("✅ KnowledgeEvolution initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize KnowledgeEvolution: {e}")
            raise
    
    async def _create_knowledge_tables(self):
        """Create knowledge evolution tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_type VARCHAR(50) NOT NULL, -- 'faq', 'gap', 'concept', 'success'
                    topic VARCHAR(255) NOT NULL,
                    pattern_data JSONB NOT NULL,
                    confidence_score FLOAT DEFAULT 0.0,
                    occurrence_count INTEGER DEFAULT 1,
                    first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS knowledge_insights (
                    id SERIAL PRIMARY KEY,
                    insight_type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    supporting_evidence JSONB DEFAULT '[]',
                    confidence_score FLOAT DEFAULT 0.0,
                    impact_score FLOAT DEFAULT 0.0,
                    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'implemented'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS question_clusters (
                    id SERIAL PRIMARY KEY,
                    cluster_topic VARCHAR(255) NOT NULL,
                    similar_questions JSONB NOT NULL,
                    successful_responses JSONB NOT NULL,
                    avg_satisfaction FLOAT DEFAULT 0.0,
                    question_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_knowledge_patterns_type ON knowledge_patterns(pattern_type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_patterns_topic ON knowledge_patterns(topic);
                CREATE INDEX IF NOT EXISTS idx_knowledge_insights_type ON knowledge_insights(insight_type);
            """)
    
    async def _setup_knowledge_collections(self):
        """Set up Qdrant collections for knowledge evolution"""
        try:
            # Knowledge insights collection is already created in main.py
            logger.info("Knowledge collections ready")
        except Exception as e:
            logger.error(f"Failed to setup knowledge collections: {e}")
    
    async def analyze_interaction(self, feedback_data: Dict[str, Any]):
        """Analyze interaction for knowledge evolution opportunities"""
        try:
            query = feedback_data["query"]
            response = feedback_data["response"] 
            rating = feedback_data["rating"]
            was_helpful = feedback_data["was_helpful"]
            
            # Detect FAQ patterns
            if rating >= 4 and was_helpful:
                await self._detect_faq_pattern(query, response, rating)
            
            # Detect knowledge gaps
            if rating <= 2 or not was_helpful:
                await self._detect_knowledge_gap(query, response, rating)
            
            # Extract and relate concepts
            await self._analyze_concept_relationships(query, response)
            
            # Learn from successful responses
            if rating >= 4:
                await self._learn_success_patterns(query, response, feedback_data)
                
            logger.debug(f"Analyzed interaction for knowledge evolution")
            
        except Exception as e:
            logger.error(f"Failed to analyze interaction: {e}")
    
    async def _detect_faq_pattern(self, query: str, response: str, rating: int):
        """Detect and cluster frequently asked questions"""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode(query)
            
            # Search for similar questions in existing clusters
            similar_cluster = await self._find_similar_question_cluster(query_embedding)
            
            if similar_cluster:
                # Add to existing cluster
                await self._add_to_question_cluster(similar_cluster["id"], query, response, rating)
            else:
                # Create new cluster if this is a repeated question
                await self._check_and_create_question_cluster(query, response, rating)
                
        except Exception as e:
            logger.error(f"Failed to detect FAQ pattern: {e}")
    
    async def _find_similar_question_cluster(self, query_embedding: np.ndarray) -> Optional[Dict]:
        """Find similar question cluster using vector similarity"""
        try:
            # Search in Qdrant for similar questions
            search_results = await self.qdrant.search(
                collection_name="knowledge_insights",
                query_vector=query_embedding.tolist(),
                limit=3,
                score_threshold=0.8
            )
            
            for result in search_results:
                if result.payload.get("type") == "faq_cluster":
                    return result.payload
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find similar question cluster: {e}")
            return None
    
    async def _detect_knowledge_gap(self, query: str, response: str, rating: int):
        """Detect areas where knowledge base is insufficient"""
        try:
            # Extract topic from query
            topic = await self._extract_primary_topic(query)
            
            # Check if this is a recurring gap
            async with self.db_pool.acquire() as conn:
                existing_gap = await conn.fetchrow("""
                    SELECT * FROM knowledge_patterns 
                    WHERE pattern_type = 'gap' AND topic = $1
                """, topic)
                
                if existing_gap:
                    # Update existing gap pattern
                    new_count = existing_gap["occurrence_count"] + 1
                    confidence = min(new_count / 10, 1.0)  # Higher confidence with more occurrences
                    
                    await conn.execute("""
                        UPDATE knowledge_patterns SET
                            occurrence_count = $2,
                            confidence_score = $3,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """, existing_gap["id"], new_count, confidence)
                    
                    # Create insight if gap is significant
                    if new_count >= 3 and confidence >= 0.7:
                        await self._create_knowledge_gap_insight(topic, new_count)
                        
                else:
                    # Create new gap pattern
                    gap_data = {
                        "sample_query": query,
                        "attempted_response": response,
                        "rating": rating,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await conn.execute("""
                        INSERT INTO knowledge_patterns 
                        (pattern_type, topic, pattern_data, confidence_score, occurrence_count)
                        VALUES ($1, $2, $3, $4, $5)
                    """, "gap", topic, json.dumps(gap_data), 0.3, 1)
                    
        except Exception as e:
            logger.error(f"Failed to detect knowledge gap: {e}")
    
    async def _analyze_concept_relationships(self, query: str, response: str):
        """Analyze and learn concept relationships"""
        try:
            # Extract concepts from both query and response
            query_concepts = await self._extract_concepts(query)
            response_concepts = await self._extract_concepts(response)
            
            # Store concept relationships
            for q_concept in query_concepts:
                for r_concept in response_concepts:
                    if q_concept != r_concept:
                        await self._record_concept_relationship(q_concept, r_concept)
                        
        except Exception as e:
            logger.error(f"Failed to analyze concept relationships: {e}")
    
    async def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple concept extraction - could be enhanced with NLP
        concepts = []
        
        # Technical concepts
        tech_concepts = {
            "authentication", "authorization", "database", "api", "integration",
            "security", "performance", "deployment", "frontend", "backend",
            "docker", "kubernetes", "postgres", "redis", "queue", "webhook"
        }
        
        text_lower = text.lower()
        for concept in tech_concepts:
            if concept in text_lower:
                concepts.append(concept)
        
        return concepts
    
    async def _learn_success_patterns(self, query: str, response: str, feedback_data: Dict):
        """Learn from successful responses"""
        try:
            # Analyze what made this response successful
            success_factors = {
                "response_length": len(response.split()),
                "has_examples": "example" in response.lower() or "```" in response,
                "has_steps": any(indicator in response.lower() 
                               for indicator in ["step", "first", "then", "next", "finally"]),
                "has_links": "http" in response or "link" in response.lower(),
                "response_time_ms": feedback_data.get("response_time_ms", 0),
                "confidence_score": feedback_data.get("confidence_score", 0.8)
            }
            
            topic = await self._extract_primary_topic(query)
            
            # Store success pattern
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO knowledge_patterns 
                    (pattern_type, topic, pattern_data, confidence_score, occurrence_count)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (pattern_type, topic) DO UPDATE SET
                        pattern_data = knowledge_patterns.pattern_data || $3,
                        occurrence_count = knowledge_patterns.occurrence_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, "success", topic, json.dumps(success_factors), 0.8, 1)
                
        except Exception as e:
            logger.error(f"Failed to learn success patterns: {e}")
    
    async def _extract_primary_topic(self, text: str) -> str:
        """Extract primary topic from text"""
        # Simple topic extraction
        topic_keywords = {
            "authentication": ["auth", "login", "password", "token", "jwt", "oauth"],
            "database": ["database", "sql", "postgres", "query", "table", "schema"],
            "api": ["api", "endpoint", "rest", "http", "request", "response"],
            "security": ["security", "permission", "access", "secure", "encryption"],
            "integration": ["integration", "connect", "webhook", "sync", "external"],
            "performance": ["performance", "speed", "optimize", "cache", "slow"],
            "deployment": ["deploy", "docker", "container", "production", "environment"],
            "frontend": ["frontend", "ui", "react", "javascript", "css", "html"]
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        # Return topic with highest score, or "general" if none found
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        return "general"
    
    async def _create_knowledge_gap_insight(self, topic: str, occurrence_count: int):
        """Create insight about knowledge gap"""
        try:
            insight_title = f"Knowledge Gap Detected: {topic.title()}"
            insight_content = f"""
            Analysis shows {occurrence_count} user queries about {topic} received poor ratings.
            This suggests our current documentation or knowledge base may be insufficient 
            for {topic}-related questions. 
            
            Recommendations:
            1. Review and enhance {topic} documentation
            2. Add more examples and use cases for {topic}
            3. Consider creating FAQ section for {topic}
            4. Monitor user satisfaction for {topic} queries
            """
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO knowledge_insights 
                    (insight_type, title, content, confidence_score, impact_score)
                    VALUES ($1, $2, $3, $4, $5)
                """, "gap", insight_title, insight_content.strip(), 0.8, 0.7)
                
            logger.info(f"Created knowledge gap insight for topic: {topic}")
            
        except Exception as e:
            logger.error(f"Failed to create knowledge gap insight: {e}")
    
    async def get_latest_insights(self) -> List[Dict[str, Any]]:
        """Get latest knowledge insights"""
        try:
            async with self.db_pool.acquire() as conn:
                insights = await conn.fetch("""
                    SELECT 
                        insight_type as type,
                        title,
                        content,
                        confidence_score,
                        impact_score,
                        status,
                        created_at,
                        updated_at
                    FROM knowledge_insights 
                    ORDER BY created_at DESC 
                    LIMIT 50
                """)
                
                return [dict(insight) for insight in insights]
                
        except Exception as e:
            logger.error(f"Failed to get latest insights: {e}")
            return []
    
    async def start_knowledge_evolution(self):
        """Start continuous knowledge evolution"""
        self.is_running = True
        
        while self.is_running:
            try:
                await self._periodic_knowledge_analysis()
                await asyncio.sleep(60 * 60)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in knowledge evolution: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _periodic_knowledge_analysis(self):
        """Periodic analysis of knowledge patterns"""
        try:
            # Analyze emerging topics
            await self._detect_emerging_topics()
            
            # Update pattern confidence scores
            await self._update_pattern_confidence()
            
            # Generate new insights
            await self._generate_periodic_insights()
            
            logger.info("Completed periodic knowledge analysis")
            
        except Exception as e:
            logger.error(f"Failed periodic knowledge analysis: {e}")
    
    async def _detect_emerging_topics(self):
        """Detect new emerging topics from recent interactions"""
        try:
            # Get recent queries from the last week
            async with self.db_pool.acquire() as conn:
                recent_queries = await conn.fetch("""
                    SELECT query, COUNT(*) as frequency
                    FROM user_interaction_logs 
                    WHERE interaction_at > NOW() - INTERVAL '7 days'
                    GROUP BY query
                    HAVING COUNT(*) >= 2
                    ORDER BY frequency DESC
                    LIMIT 100
                """)
                
                # Analyze for new topics
                for query_row in recent_queries:
                    query = query_row["query"]
                    topic = await self._extract_primary_topic(query)
                    
                    # Check if this is a new topic trend
                    existing = await conn.fetchrow("""
                        SELECT * FROM knowledge_patterns 
                        WHERE pattern_type = 'emerging' AND topic = $1
                    """, topic)
                    
                    if not existing and query_row["frequency"] >= 3:
                        # Create emerging topic pattern
                        pattern_data = {
                            "sample_queries": [query],
                            "frequency": query_row["frequency"],
                            "detected_at": datetime.utcnow().isoformat()
                        }
                        
                        await conn.execute("""
                            INSERT INTO knowledge_patterns 
                            (pattern_type, topic, pattern_data, confidence_score, occurrence_count)
                            VALUES ($1, $2, $3, $4, $5)
                        """, "emerging", topic, json.dumps(pattern_data), 0.6, query_row["frequency"])
                        
        except Exception as e:
            logger.error(f"Failed to detect emerging topics: {e}")
    
    async def _update_pattern_confidence(self):
        """Update confidence scores for knowledge patterns"""
        # Implementation for confidence score updates based on recent data
        pass
    
    async def _generate_periodic_insights(self):
        """Generate new insights from accumulated patterns"""
        # Implementation for generating insights from patterns
        pass 
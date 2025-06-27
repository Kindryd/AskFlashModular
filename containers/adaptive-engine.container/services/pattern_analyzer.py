"""
Pattern Analyzer - Detect behavioral patterns across users and conversations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """
    Analyzes patterns across user interactions and conversations
    
    Features:
    - Cross-user behavior pattern detection
    - Conversation flow optimization patterns
    - Temporal usage pattern analysis
    - Content preference pattern recognition
    - Escalation pattern detection
    """
    
    def __init__(self, db_pool, redis_client, qdrant_client):
        self.db_pool = db_pool
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.is_running = False
        
    async def initialize(self):
        """Initialize pattern analyzer"""
        try:
            await self._create_pattern_tables()
            
            logger.info("✅ PatternAnalyzer initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PatternAnalyzer: {e}")
            raise
    
    async def _create_pattern_tables(self):
        """Create pattern analysis tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS behavioral_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_category VARCHAR(50) NOT NULL, -- 'user_behavior', 'conversation_flow', 'content_preference', 'temporal'
                    pattern_name VARCHAR(255) NOT NULL,
                    pattern_description TEXT NOT NULL,
                    pattern_data JSONB NOT NULL,
                    confidence_score FLOAT DEFAULT 0.0,
                    affected_users INTEGER DEFAULT 0,
                    occurrences INTEGER DEFAULT 0,
                    first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS conversation_flows (
                    id SERIAL PRIMARY KEY,
                    flow_type VARCHAR(100) NOT NULL,
                    conversation_path JSONB NOT NULL, -- Array of interaction types
                    success_rate FLOAT DEFAULT 0.0,
                    avg_satisfaction FLOAT DEFAULT 0.0,
                    total_occurrences INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS usage_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_type VARCHAR(50) NOT NULL, -- 'hourly', 'daily', 'weekly', 'seasonal'
                    time_segment VARCHAR(50) NOT NULL,
                    usage_data JSONB NOT NULL,
                    user_count INTEGER DEFAULT 0,
                    query_count INTEGER DEFAULT 0,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_behavioral_patterns_category ON behavioral_patterns(pattern_category);
                CREATE INDEX IF NOT EXISTS idx_conversation_flows_type ON conversation_flows(flow_type);
                CREATE INDEX IF NOT EXISTS idx_usage_patterns_type ON usage_patterns(pattern_type);
            """)
    
    async def start_pattern_detection(self):
        """Start continuous pattern detection"""
        self.is_running = True
        
        while self.is_running:
            try:
                await self._analyze_all_patterns()
                await asyncio.sleep(45 * 60)  # 45 minutes
                
            except Exception as e:
                logger.error(f"Error in pattern detection: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _analyze_all_patterns(self):
        """Comprehensive pattern analysis"""
        try:
            # Analyze different pattern types
            await self._analyze_user_behavior_patterns()
            await self._analyze_conversation_flow_patterns()
            await self._analyze_temporal_patterns()
            await self._analyze_content_preference_patterns()
            
            logger.info("Completed comprehensive pattern analysis")
            
        except Exception as e:
            logger.error(f"Failed comprehensive pattern analysis: {e}")
    
    async def _analyze_user_behavior_patterns(self):
        """Analyze cross-user behavior patterns"""
        try:
            async with self.db_pool.acquire() as conn:
                # Pattern 1: Query complexity preferences across users
                complexity_patterns = await conn.fetch("""
                    SELECT 
                        query_complexity,
                        COUNT(DISTINCT user_id) as user_count,
                        COUNT(*) as query_count,
                        AVG(user_satisfaction) as avg_satisfaction
                    FROM user_interaction_logs 
                    WHERE interaction_at > NOW() - INTERVAL '7 days'
                    AND query_complexity IS NOT NULL
                    GROUP BY query_complexity
                """)
                
                for pattern in complexity_patterns:
                    if pattern["user_count"] >= 3:  # Minimum 3 users for pattern
                        await self._record_behavioral_pattern(
                            category="user_behavior",
                            name=f"query_complexity_{pattern['query_complexity']}",
                            description=f"Users preferring {pattern['query_complexity']} complexity queries",
                            data={
                                "complexity_level": pattern["query_complexity"],
                                "user_count": pattern["user_count"],
                                "query_count": pattern["query_count"],
                                "avg_satisfaction": float(pattern["avg_satisfaction"]) if pattern["avg_satisfaction"] else 0.0
                            },
                            confidence=min(pattern["user_count"] / 10, 1.0),
                            affected_users=pattern["user_count"]
                        )
                
                # Pattern 2: Response time sensitivity
                await self._analyze_response_time_patterns(conn)
                
                # Pattern 3: Topic expertise distribution
                await self._analyze_expertise_patterns(conn)
                
        except Exception as e:
            logger.error(f"Failed to analyze user behavior patterns: {e}")
    
    async def _analyze_response_time_patterns(self, conn):
        """Analyze response time sensitivity patterns"""
        try:
            time_satisfaction = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN response_time_ms < 3000 THEN 'fast'
                        WHEN response_time_ms < 8000 THEN 'medium'
                        ELSE 'slow'
                    END as response_speed,
                    COUNT(DISTINCT user_id) as user_count,
                    AVG(user_satisfaction) as avg_satisfaction
                FROM user_interaction_logs 
                WHERE interaction_at > NOW() - INTERVAL '7 days'
                AND response_time_ms IS NOT NULL
                AND user_satisfaction IS NOT NULL
                GROUP BY 1
            """)
            
            for pattern in time_satisfaction:
                await self._record_behavioral_pattern(
                    category="user_behavior",
                    name=f"response_time_sensitivity_{pattern['response_speed']}",
                    description=f"User satisfaction with {pattern['response_speed']} response times",
                    data={
                        "response_speed": pattern["response_speed"],
                        "user_count": pattern["user_count"],
                        "avg_satisfaction": float(pattern["avg_satisfaction"])
                    },
                    confidence=0.8,
                    affected_users=pattern["user_count"]
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze response time patterns: {e}")
    
    async def _analyze_expertise_patterns(self, conn):
        """Analyze user expertise distribution patterns"""
        try:
            # Get domain expertise from user personas
            expertise_distribution = await conn.fetch("""
                SELECT 
                    jsonb_object_keys(domain_expertise) as domain,
                    COUNT(*) as user_count,
                    AVG((domain_expertise->jsonb_object_keys(domain_expertise))::int) as avg_interactions
                FROM user_personas 
                WHERE domain_expertise IS NOT NULL
                GROUP BY 1
                HAVING COUNT(*) >= 2
            """)
            
            for pattern in expertise_distribution:
                await self._record_behavioral_pattern(
                    category="user_behavior", 
                    name=f"domain_expertise_{pattern['domain']}",
                    description=f"Users with expertise in {pattern['domain']}",
                    data={
                        "domain": pattern["domain"],
                        "user_count": pattern["user_count"],
                        "avg_interactions": float(pattern["avg_interactions"])
                    },
                    confidence=min(pattern["user_count"] / 5, 1.0),
                    affected_users=pattern["user_count"]
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze expertise patterns: {e}")
    
    async def _analyze_conversation_flow_patterns(self):
        """Analyze conversation flow and success patterns"""
        try:
            async with self.db_pool.acquire() as conn:
                # Analyze conversation sequences that lead to high satisfaction
                successful_flows = await conn.fetch("""
                    SELECT 
                        topics,
                        COUNT(*) as occurrence_count,
                        AVG(user_satisfaction) as avg_satisfaction
                    FROM user_interaction_logs 
                    WHERE interaction_at > NOW() - INTERVAL '7 days'
                    AND user_satisfaction >= 4
                    AND topics IS NOT NULL
                    GROUP BY topics
                    HAVING COUNT(*) >= 3
                    ORDER BY avg_satisfaction DESC
                """)
                
                for flow in successful_flows:
                    await self._record_conversation_flow(
                        flow_type="successful_topic_sequence",
                        conversation_path=flow["topics"],
                        success_rate=1.0,  # These are all successful flows
                        avg_satisfaction=float(flow["avg_satisfaction"]),
                        occurrences=flow["occurrence_count"]
                    )
                
                # Analyze escalation patterns
                await self._analyze_escalation_patterns(conn)
                
        except Exception as e:
            logger.error(f"Failed to analyze conversation flow patterns: {e}")
    
    async def _analyze_escalation_patterns(self, conn):
        """Analyze when users need escalation or additional help"""
        try:
            # Find patterns in low-satisfaction interactions
            escalation_patterns = await conn.fetch("""
                SELECT 
                    topics,
                    query_complexity,
                    COUNT(*) as occurrence_count,
                    AVG(user_satisfaction) as avg_satisfaction,
                    AVG(response_time_ms) as avg_response_time
                FROM user_interaction_logs 
                WHERE interaction_at > NOW() - INTERVAL '7 days'
                AND user_satisfaction <= 2
                GROUP BY topics, query_complexity
                HAVING COUNT(*) >= 2
            """)
            
            for pattern in escalation_patterns:
                await self._record_behavioral_pattern(
                    category="conversation_flow",
                    name="escalation_risk_pattern",
                    description=f"Pattern leading to user dissatisfaction requiring escalation",
                    data={
                        "topics": pattern["topics"],
                        "query_complexity": pattern["query_complexity"],
                        "occurrence_count": pattern["occurrence_count"],
                        "avg_satisfaction": float(pattern["avg_satisfaction"]),
                        "avg_response_time": float(pattern["avg_response_time"]) if pattern["avg_response_time"] else 0
                    },
                    confidence=min(pattern["occurrence_count"] / 5, 1.0),
                    affected_users=pattern["occurrence_count"]
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze escalation patterns: {e}")
    
    async def _analyze_temporal_patterns(self):
        """Analyze temporal usage patterns"""
        try:
            async with self.db_pool.acquire() as conn:
                # Hourly usage patterns
                hourly_patterns = await conn.fetch("""
                    SELECT 
                        EXTRACT(hour FROM interaction_at) as hour,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(*) as total_queries,
                        AVG(user_satisfaction) as avg_satisfaction
                    FROM user_interaction_logs 
                    WHERE interaction_at > NOW() - INTERVAL '7 days'
                    GROUP BY 1
                    ORDER BY 1
                """)
                
                for pattern in hourly_patterns:
                    await self._record_usage_pattern(
                        pattern_type="hourly",
                        time_segment=f"hour_{int(pattern['hour'])}",
                        usage_data={
                            "hour": int(pattern["hour"]),
                            "unique_users": pattern["unique_users"],
                            "total_queries": pattern["total_queries"],
                            "avg_satisfaction": float(pattern["avg_satisfaction"]) if pattern["avg_satisfaction"] else 0.0
                        },
                        user_count=pattern["unique_users"],
                        query_count=pattern["total_queries"]
                    )
                
                # Daily patterns
                await self._analyze_daily_patterns(conn)
                
        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {e}")
    
    async def _analyze_daily_patterns(self, conn):
        """Analyze daily usage patterns"""
        try:
            daily_patterns = await conn.fetch("""
                SELECT 
                    EXTRACT(dow FROM interaction_at) as day_of_week,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_queries,
                    AVG(user_satisfaction) as avg_satisfaction
                FROM user_interaction_logs 
                WHERE interaction_at > NOW() - INTERVAL '4 weeks'
                GROUP BY 1
                ORDER BY 1
            """)
            
            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            
            for pattern in daily_patterns:
                day_name = day_names[int(pattern["day_of_week"])]
                await self._record_usage_pattern(
                    pattern_type="daily",
                    time_segment=day_name.lower(),
                    usage_data={
                        "day_of_week": int(pattern["day_of_week"]),
                        "day_name": day_name,
                        "unique_users": pattern["unique_users"],
                        "total_queries": pattern["total_queries"],
                        "avg_satisfaction": float(pattern["avg_satisfaction"]) if pattern["avg_satisfaction"] else 0.0
                    },
                    user_count=pattern["unique_users"],
                    query_count=pattern["total_queries"]
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze daily patterns: {e}")
    
    async def _analyze_content_preference_patterns(self):
        """Analyze content and response style preferences"""
        try:
            async with self.db_pool.acquire() as conn:
                # Analyze preference for different response styles
                style_preferences = await conn.fetch("""
                    SELECT 
                        response_style,
                        COUNT(DISTINCT user_id) as user_count,
                        AVG(user_satisfaction) as avg_satisfaction,
                        COUNT(*) as occurrence_count
                    FROM user_interaction_logs 
                    WHERE interaction_at > NOW() - INTERVAL '7 days'
                    AND response_style IS NOT NULL
                    AND user_satisfaction IS NOT NULL
                    GROUP BY response_style
                    HAVING COUNT(DISTINCT user_id) >= 2
                """)
                
                for pattern in style_preferences:
                    await self._record_behavioral_pattern(
                        category="content_preference",
                        name=f"response_style_{pattern['response_style']}",
                        description=f"Users preferring {pattern['response_style']} response style",
                        data={
                            "response_style": pattern["response_style"],
                            "user_count": pattern["user_count"],
                            "avg_satisfaction": float(pattern["avg_satisfaction"]),
                            "occurrence_count": pattern["occurrence_count"]
                        },
                        confidence=min(pattern["user_count"] / 5, 1.0),
                        affected_users=pattern["user_count"]
                    )
                    
        except Exception as e:
            logger.error(f"Failed to analyze content preference patterns: {e}")
    
    async def _record_behavioral_pattern(self, category: str, name: str, description: str, 
                                       data: Dict, confidence: float, affected_users: int):
        """Record behavioral pattern"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO behavioral_patterns 
                    (pattern_category, pattern_name, pattern_description, pattern_data, 
                     confidence_score, affected_users, occurrences)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (pattern_category, pattern_name) DO UPDATE SET
                        pattern_data = $4,
                        confidence_score = $5,
                        affected_users = $6,
                        occurrences = behavioral_patterns.occurrences + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, category, name, description, json.dumps(data), 
                    confidence, affected_users, 1)
                    
        except Exception as e:
            logger.error(f"Failed to record behavioral pattern: {e}")
    
    async def _record_conversation_flow(self, flow_type: str, conversation_path: Any,
                                      success_rate: float, avg_satisfaction: float, occurrences: int):
        """Record conversation flow pattern"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_flows 
                    (flow_type, conversation_path, success_rate, avg_satisfaction, total_occurrences)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (flow_type, conversation_path) DO UPDATE SET
                        success_rate = $3,
                        avg_satisfaction = $4,
                        total_occurrences = conversation_flows.total_occurrences + $5
                """, flow_type, json.dumps(conversation_path), success_rate, avg_satisfaction, occurrences)
                
        except Exception as e:
            logger.error(f"Failed to record conversation flow: {e}")
    
    async def _record_usage_pattern(self, pattern_type: str, time_segment: str,
                                  usage_data: Dict, user_count: int, query_count: int):
        """Record usage pattern"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO usage_patterns 
                    (pattern_type, time_segment, usage_data, user_count, query_count)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (pattern_type, time_segment) DO UPDATE SET
                        usage_data = $3,
                        user_count = $4,
                        query_count = $5,
                        recorded_at = CURRENT_TIMESTAMP
                """, pattern_type, time_segment, json.dumps(usage_data), user_count, query_count)
                
        except Exception as e:
            logger.error(f"Failed to record usage pattern: {e}")
    
    async def get_detected_patterns(self) -> List[Dict[str, Any]]:
        """Get all detected patterns"""
        try:
            async with self.db_pool.acquire() as conn:
                patterns = await conn.fetch("""
                    SELECT 
                        pattern_category as category,
                        pattern_name as name,
                        pattern_description as description,
                        pattern_data as data,
                        confidence_score,
                        affected_users,
                        occurrences,
                        last_updated
                    FROM behavioral_patterns 
                    WHERE confidence_score > 0.5
                    ORDER BY confidence_score DESC, last_updated DESC
                """)
                
                return [dict(pattern) for pattern in patterns]
                
        except Exception as e:
            logger.error(f"Failed to get detected patterns: {e}")
            return [] 
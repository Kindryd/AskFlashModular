"""
Adaptive Optimizer - Provide personalized recommendations based on learned patterns
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class AdaptiveOptimizer:
    """
    Provides adaptive optimization recommendations
    
    Features:
    - Personalized response adaptation based on user persona
    - Context relevance optimization
    - Conversation flow recommendations
    - Response style optimization
    - Real-time adaptation suggestions
    """
    
    def __init__(self, db_pool, redis_client, qdrant_client):
        self.db_pool = db_pool
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.is_running = False
        
    async def initialize(self):
        """Initialize adaptive optimizer"""
        try:
            await self._create_optimization_tables()
            
            logger.info("✅ AdaptiveOptimizer initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AdaptiveOptimizer: {e}")
            raise
    
    async def _create_optimization_tables(self):
        """Create optimization tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS optimization_recommendations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255),
                    recommendation_type VARCHAR(50) NOT NULL, -- 'response_style', 'context_relevance', 'flow_optimization'
                    recommendation_data JSONB NOT NULL,
                    confidence_score FLOAT DEFAULT 0.0,
                    applied BOOLEAN DEFAULT FALSE,
                    success_rate FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS adaptation_metrics (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255),
                    metric_type VARCHAR(50) NOT NULL, -- 'satisfaction_improvement', 'response_time', 'engagement'
                    before_value FLOAT DEFAULT 0.0,
                    after_value FLOAT DEFAULT 0.0,
                    improvement_percentage FLOAT DEFAULT 0.0,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_user ON optimization_recommendations(user_id);
                CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_type ON optimization_recommendations(recommendation_type);
            """)
    
    async def get_adaptation_recommendations(self, user_id: str, query: str, 
                                           context: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Get personalized adaptation recommendations"""
        try:
            # Get user persona for personalization
            persona = await self._get_user_persona(user_id)
            
            # Analyze query and context
            query_analysis = await self._analyze_query_context(query, context)
            
            # Generate recommendations based on persona and patterns
            recommendations = {
                "response_style": await self._recommend_response_style(persona, query_analysis),
                "context_optimization": await self._recommend_context_optimization(query, context, persona),
                "conversation_flow": await self._recommend_conversation_flow(conversation_history, persona),
                "personalization": await self._recommend_personalization(user_id, persona, query_analysis),
                "confidence": 0.0
            }
            
            # Calculate overall confidence
            recommendations["confidence"] = await self._calculate_recommendation_confidence(recommendations)
            
            # Store recommendations for tracking
            await self._store_recommendations(user_id, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get adaptation recommendations: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    async def _get_user_persona(self, user_id: str) -> Optional[Dict]:
        """Get user persona from database"""
        try:
            async with self.db_pool.acquire() as conn:
                persona = await conn.fetchrow("""
                    SELECT * FROM user_personas WHERE user_id = $1
                """, user_id)
                
                return dict(persona) if persona else None
                
        except Exception as e:
            logger.error(f"Failed to get user persona: {e}")
            return None
    
    async def _analyze_query_context(self, query: str, context: str) -> Dict[str, Any]:
        """Analyze query and context for optimization"""
        query_length = len(query.split())
        context_length = len(context.split()) if context else 0
        
        return {
            "query_length": query_length,
            "context_length": context_length,
            "complexity": "high" if query_length > 20 else "medium" if query_length > 10 else "low",
            "has_technical_terms": any(term in query.lower() for term in 
                                     ["api", "database", "code", "technical", "implementation"]),
            "is_question": query.strip().endswith("?"),
            "urgency_indicators": any(word in query.lower() for word in 
                                    ["urgent", "asap", "immediately", "quick"])
        }
    
    async def _recommend_response_style(self, persona: Optional[Dict], query_analysis: Dict) -> Dict[str, Any]:
        """Recommend optimal response style"""
        if not persona:
            # Default recommendations for new users
            return {
                "detail_level": "moderate",
                "technical_depth": "medium",
                "include_examples": True,
                "structured_format": True,
                "confidence": 0.5
            }
        
        interaction_style = persona.get("interaction_style", {})
        
        # Determine optimal style based on persona
        technical_preference = interaction_style.get("technical_preference", 0.5)
        preferred_detail = interaction_style.get("preferred_detail_level", "moderate")
        
        recommendations = {
            "detail_level": preferred_detail,
            "technical_depth": "high" if technical_preference > 0.7 else "low" if technical_preference < 0.3 else "medium",
            "include_examples": query_analysis.get("has_technical_terms", False) or technical_preference > 0.5,
            "structured_format": preferred_detail in ["detailed", "moderate"],
            "tone": interaction_style.get("formality_level", "professional"),
            "confidence": min(persona.get("confidence_score", 0.5) + 0.2, 1.0)
        }
        
        return recommendations
    
    async def _recommend_context_optimization(self, query: str, context: str, persona: Optional[Dict]) -> Dict[str, Any]:
        """Recommend context optimization strategies"""
        try:
            # Analyze context relevance
            query_embedding = self.embedding_model.encode(query)
            
            if context:
                context_chunks = context.split('\n\n')  # Split by paragraphs
                relevance_scores = []
                
                for chunk in context_chunks:
                    if chunk.strip():
                        chunk_embedding = self.embedding_model.encode(chunk)
                        similarity = np.dot(query_embedding, chunk_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                        )
                        relevance_scores.append(similarity)
                
                avg_relevance = np.mean(relevance_scores) if relevance_scores else 0.0
            else:
                avg_relevance = 0.0
            
            recommendations = {
                "context_relevance_score": float(avg_relevance),
                "needs_more_context": avg_relevance < 0.6,
                "context_optimization": "high" if avg_relevance < 0.5 else "medium" if avg_relevance < 0.8 else "low",
                "suggested_context_types": await self._suggest_context_types(query, persona),
                "confidence": 0.8
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend context optimization: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    async def _suggest_context_types(self, query: str, persona: Optional[Dict]) -> List[str]:
        """Suggest types of context that would be helpful"""
        suggestions = []
        
        query_lower = query.lower()
        
        # Based on query content
        if any(word in query_lower for word in ["how", "tutorial", "guide", "steps"]):
            suggestions.extend(["step_by_step_guide", "examples", "best_practices"])
        
        if any(word in query_lower for word in ["error", "issue", "problem", "troubleshoot"]):
            suggestions.extend(["troubleshooting_guide", "common_issues", "error_solutions"])
        
        if any(word in query_lower for word in ["api", "integration", "connect"]):
            suggestions.extend(["api_documentation", "integration_examples", "authentication_guide"])
        
        # Based on user persona
        if persona:
            domain_expertise = persona.get("domain_expertise", {})
            if "authentication" in domain_expertise:
                suggestions.append("security_considerations")
            if "database" in domain_expertise:
                suggestions.append("data_modeling_examples")
        
        return list(set(suggestions))  # Remove duplicates
    
    async def _recommend_conversation_flow(self, conversation_history: List[Dict], persona: Optional[Dict]) -> Dict[str, Any]:
        """Recommend optimal conversation flow"""
        if not conversation_history:
            return {
                "flow_stage": "initial",
                "recommended_approach": "direct_answer",
                "follow_up_suggestions": ["clarification", "examples", "related_topics"],
                "confidence": 0.7
            }
        
        # Analyze conversation pattern
        conversation_length = len(conversation_history)
        
        # Look for patterns in successful conversations
        recommendations = {
            "flow_stage": self._determine_conversation_stage(conversation_history),
            "recommended_approach": await self._suggest_approach_strategy(conversation_history, persona),
            "escalation_risk": await self._assess_escalation_risk(conversation_history),
            "follow_up_suggestions": await self._suggest_follow_ups(conversation_history),
            "confidence": min(conversation_length / 5, 1.0)  # Higher confidence with more history
        }
        
        return recommendations
    
    def _determine_conversation_stage(self, history: List[Dict]) -> str:
        """Determine current stage of conversation"""
        if len(history) <= 1:
            return "initial"
        elif len(history) <= 3:
            return "clarification"
        elif len(history) <= 5:
            return "deep_dive"
        else:
            return "extended"
    
    async def _suggest_approach_strategy(self, history: List[Dict], persona: Optional[Dict]) -> str:
        """Suggest approach strategy based on history and persona"""
        # Simple heuristic - could be enhanced with ML
        if persona and persona.get("confidence_score", 0) > 0.8:
            interaction_style = persona.get("interaction_style", {})
            if interaction_style.get("technical_preference", 0) > 0.7:
                return "technical_detailed"
            else:
                return "explanatory"
        
        # Default strategy based on conversation length
        return "direct_answer" if len(history) <= 2 else "comprehensive"
    
    async def _assess_escalation_risk(self, history: List[Dict]) -> float:
        """Assess risk of needing escalation"""
        risk_indicators = 0
        
        for interaction in history:
            content = interaction.get("content", "").lower()
            if any(word in content for word in ["still", "not working", "confused", "help"]):
                risk_indicators += 1
        
        return min(risk_indicators / len(history), 1.0) if history else 0.0
    
    async def _suggest_follow_ups(self, history: List[Dict]) -> List[str]:
        """Suggest follow-up actions"""
        suggestions = ["clarification", "examples"]
        
        # Add specific suggestions based on conversation content
        last_interaction = history[-1] if history else {}
        content = last_interaction.get("content", "").lower()
        
        if "code" in content or "implementation" in content:
            suggestions.append("code_examples")
        if "deploy" in content or "production" in content:
            suggestions.append("deployment_guide")
        if "error" in content or "issue" in content:
            suggestions.append("troubleshooting")
        
        return suggestions
    
    async def _recommend_personalization(self, user_id: str, persona: Optional[Dict], query_analysis: Dict) -> Dict[str, Any]:
        """Recommend personalization strategies"""
        if not persona:
            return {
                "personalization_level": "minimal",
                "learning_opportunities": ["build_preferences", "track_satisfaction"],
                "confidence": 0.3
            }
        
        total_interactions = persona.get("total_interactions", 0)
        confidence_score = persona.get("confidence_score", 0.0)
        
        recommendations = {
            "personalization_level": "high" if confidence_score > 0.8 else "medium" if confidence_score > 0.5 else "low",
            "user_expertise_areas": list(persona.get("domain_expertise", {}).keys()),
            "preferred_interaction_time": await self._get_preferred_time(persona),
            "learning_opportunities": await self._identify_learning_opportunities(user_id, persona),
            "adaptation_suggestions": await self._get_adaptation_suggestions(persona, query_analysis),
            "confidence": confidence_score
        }
        
        return recommendations
    
    async def _get_preferred_time(self, persona: Dict) -> Optional[str]:
        """Get user's preferred interaction time"""
        temporal_patterns = persona.get("temporal_patterns", {})
        if temporal_patterns:
            # Find hour with most interactions
            max_hour = max(temporal_patterns.items(), key=lambda x: x[1])
            return f"hour_{max_hour[0]}"
        return None
    
    async def _identify_learning_opportunities(self, user_id: str, persona: Dict) -> List[str]:
        """Identify opportunities to learn more about user"""
        opportunities = []
        
        confidence = persona.get("confidence_score", 0.0)
        total_interactions = persona.get("total_interactions", 0)
        
        if confidence < 0.5:
            opportunities.append("gather_preferences")
        if total_interactions < 10:
            opportunities.append("build_interaction_history")
        if not persona.get("domain_expertise"):
            opportunities.append("identify_expertise_areas")
        
        return opportunities
    
    async def _get_adaptation_suggestions(self, persona: Dict, query_analysis: Dict) -> List[str]:
        """Get specific adaptation suggestions"""
        suggestions = []
        
        interaction_style = persona.get("interaction_style", {})
        
        if interaction_style.get("technical_preference", 0) > 0.7 and not query_analysis.get("has_technical_terms"):
            suggestions.append("add_technical_details")
        
        if query_analysis.get("urgency_indicators") and interaction_style.get("preferred_detail_level") == "detailed":
            suggestions.append("prioritize_key_points")
        
        return suggestions
    
    async def _calculate_recommendation_confidence(self, recommendations: Dict) -> float:
        """Calculate overall confidence score for recommendations"""
        confidence_scores = []
        
        for category, rec in recommendations.items():
            if isinstance(rec, dict) and "confidence" in rec:
                confidence_scores.append(rec["confidence"])
        
        return np.mean(confidence_scores) if confidence_scores else 0.0
    
    async def _store_recommendations(self, user_id: str, recommendations: Dict):
        """Store recommendations for tracking effectiveness"""
        try:
            async with self.db_pool.acquire() as conn:
                for rec_type, rec_data in recommendations.items():
                    if rec_type != "confidence" and isinstance(rec_data, dict):
                        await conn.execute("""
                            INSERT INTO optimization_recommendations 
                            (user_id, recommendation_type, recommendation_data, confidence_score)
                            VALUES ($1, $2, $3, $4)
                        """, user_id, rec_type, json.dumps(rec_data), rec_data.get("confidence", 0.0))
                        
        except Exception as e:
            logger.error(f"Failed to store recommendations: {e}")
    
    async def start_optimization_loop(self):
        """Start continuous optimization monitoring"""
        self.is_running = True
        
        while self.is_running:
            try:
                await self._monitor_adaptation_effectiveness()
                await asyncio.sleep(90 * 60)  # 90 minutes
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _monitor_adaptation_effectiveness(self):
        """Monitor effectiveness of applied adaptations"""
        try:
            # Analyze how well recommendations are working
            async with self.db_pool.acquire() as conn:
                # Get recent recommendations that have been applied
                recent_recs = await conn.fetch("""
                    SELECT * FROM optimization_recommendations 
                    WHERE applied = true 
                    AND created_at > NOW() - INTERVAL '7 days'
                """)
                
                for rec in recent_recs:
                    await self._evaluate_recommendation_success(rec)
                    
            logger.info("Completed adaptation effectiveness monitoring")
            
        except Exception as e:
            logger.error(f"Failed to monitor adaptation effectiveness: {e}")
    
    async def _evaluate_recommendation_success(self, recommendation):
        """Evaluate success of a specific recommendation"""
        # Implementation for evaluating recommendation effectiveness
        # This would compare before/after metrics for users who received the recommendation
        pass 
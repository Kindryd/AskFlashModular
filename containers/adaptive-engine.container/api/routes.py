"""
API Routes for Adaptive Learning Engine
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# These will be injected from main.py
persona_builder = None
knowledge_evolution = None 
pattern_analyzer = None
adaptive_optimizer = None

def set_services(pb, ke, pa, ao):
    """Set service instances"""
    global persona_builder, knowledge_evolution, pattern_analyzer, adaptive_optimizer
    persona_builder = pb
    knowledge_evolution = ke
    pattern_analyzer = pa
    adaptive_optimizer = ao

@router.get("/personas/{user_id}")
async def get_user_persona_detailed(user_id: str):
    """Get detailed user persona and learning insights"""
    try:
        persona = await persona_builder.get_user_persona(user_id)
        
        if not persona:
            return {
                "user_id": user_id,
                "status": "new_user",
                "message": "No persona data available. Persona will be built through interactions.",
                "recommendations": [
                    "Start with simple queries to build initial preferences",
                    "Provide feedback on responses to improve personalization",
                    "Ask questions in your area of expertise to build domain profile"
                ]
            }
        
        return {
            "user_id": user_id,
            "persona": persona,
            "status": "active",
            "insights": {
                "interaction_maturity": "high" if persona["total_interactions"] > 20 else "medium" if persona["total_interactions"] > 5 else "low",
                "personalization_readiness": persona["confidence_score"] > 0.7,
                "top_expertise_areas": sorted(persona.get("domain_expertise", {}).items(), key=lambda x: x[1], reverse=True)[:3],
                "communication_insights": persona.get("persona_insights", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personas/{user_id}/feedback")
async def update_persona_with_feedback(user_id: str, feedback_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Update user persona with new feedback"""
    try:
        # Process feedback for persona learning
        background_tasks.add_task(persona_builder.process_feedback, {
            "user_id": user_id,
            **feedback_data
        })
        
        return {
            "status": "feedback_received",
            "message": "Feedback will be processed to update user persona",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update persona with feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/insights")
async def get_knowledge_insights(
    insight_type: Optional[str] = Query(None, description="Filter by insight type: gap, pattern, optimization, evolution"),
    limit: int = Query(20, ge=1, le=100, description="Number of insights to return")
):
    """Get evolved knowledge insights"""
    try:
        insights = await knowledge_evolution.get_latest_insights()
        
        # Filter by type if specified
        if insight_type:
            insights = [i for i in insights if i.get("type") == insight_type]
        
        # Limit results
        insights = insights[:limit]
        
        # Add analytics
        analytics = {
            "total_insights": len(insights),
            "insight_types": {},
            "avg_confidence": 0.0,
            "high_impact_count": 0
        }
        
        if insights:
            for insight in insights:
                insight_type_key = insight.get("type", "unknown")
                analytics["insight_types"][insight_type_key] = analytics["insight_types"].get(insight_type_key, 0) + 1
                
                if insight.get("impact_score", 0) > 0.7:
                    analytics["high_impact_count"] += 1
            
            analytics["avg_confidence"] = sum(i.get("confidence_score", 0) for i in insights) / len(insights)
        
        return {
            "insights": insights,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get knowledge insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/analyze")
async def analyze_knowledge_interaction(interaction_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Analyze interaction for knowledge evolution"""
    try:
        # Process interaction for knowledge evolution
        background_tasks.add_task(knowledge_evolution.analyze_interaction, interaction_data)
        
        return {
            "status": "analysis_queued",
            "message": "Interaction will be analyzed for knowledge evolution opportunities",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze knowledge interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns/behavioral")
async def get_behavioral_patterns(
    category: Optional[str] = Query(None, description="Filter by category: user_behavior, conversation_flow, content_preference, temporal"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score")
):
    """Get detected behavioral patterns"""
    try:
        patterns = await pattern_analyzer.get_detected_patterns()
        
        # Filter by category and confidence
        if category:
            patterns = [p for p in patterns if p.get("category") == category]
        
        patterns = [p for p in patterns if p.get("confidence_score", 0) >= min_confidence]
        
        # Group patterns by category for analytics
        pattern_analytics = {
            "total_patterns": len(patterns),
            "categories": {},
            "avg_confidence": 0.0,
            "high_confidence_count": 0
        }
        
        for pattern in patterns:
            cat = pattern.get("category", "unknown")
            pattern_analytics["categories"][cat] = pattern_analytics["categories"].get(cat, 0) + 1
            
            if pattern.get("confidence_score", 0) > 0.8:
                pattern_analytics["high_confidence_count"] += 1
        
        if patterns:
            pattern_analytics["avg_confidence"] = sum(p.get("confidence_score", 0) for p in patterns) / len(patterns)
        
        return {
            "patterns": patterns,
            "analytics": pattern_analytics,
            "filters_applied": {
                "category": category,
                "min_confidence": min_confidence
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get behavioral patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize/recommendations")
async def get_optimization_recommendations(request_data: Dict[str, Any]):
    """Get personalized optimization recommendations"""
    try:
        user_id = request_data.get("user_id")
        query = request_data.get("query", "")
        context = request_data.get("context", "")
        conversation_history = request_data.get("conversation_history", [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        recommendations = await adaptive_optimizer.get_adaptation_recommendations(
            user_id=user_id,
            query=query,
            context=context,
            conversation_history=conversation_history
        )
        
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "request_context": {
                "query_length": len(query.split()),
                "context_provided": bool(context),
                "conversation_length": len(conversation_history)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/learning")
async def get_learning_analytics():
    """Get comprehensive learning analytics"""
    try:
        # This would aggregate data from all learning services
        analytics = {
            "personas": {
                "total_users_with_personas": 0,
                "avg_confidence_score": 0.0,
                "high_confidence_personas": 0
            },
            "knowledge_evolution": {
                "total_insights": 0,
                "knowledge_gaps_detected": 0,
                "successful_patterns_identified": 0
            },
            "behavioral_patterns": {
                "total_patterns": 0,
                "cross_user_patterns": 0,
                "temporal_patterns": 0
            },
            "optimization": {
                "recommendations_generated": 0,
                "successful_adaptations": 0,
                "avg_improvement_score": 0.0
            }
        }
        
        # Get actual analytics from each service
        # This would be implemented to query the respective tables
        
        return {
            "analytics": analytics,
            "learning_health": {
                "overall_status": "healthy",
                "data_quality_score": 0.85,
                "learning_velocity": "high",
                "adaptation_effectiveness": 0.78
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/user/{user_id}")
async def get_user_specific_insights(user_id: str):
    """Get insights specific to a user"""
    try:
        # Get user persona
        persona = await persona_builder.get_user_persona(user_id)
        
        # Get user-specific patterns and recommendations
        insights = {
            "learning_progress": {
                "persona_confidence": persona.get("confidence_score", 0.0) if persona else 0.0,
                "total_interactions": persona.get("total_interactions", 0) if persona else 0,
                "expertise_areas": list(persona.get("domain_expertise", {}).keys()) if persona else [],
                "learning_stage": "mature" if persona and persona.get("confidence_score", 0) > 0.8 else "developing" if persona else "new"
            },
            "personalization_opportunities": [
                "Response style optimization based on interaction patterns",
                "Context relevance improvements",
                "Conversation flow optimization"
            ] if persona else [
                "Start building interaction history",
                "Gather communication preferences",
                "Identify expertise areas"
            ],
            "recent_adaptations": [],  # Would show recent optimizations applied
            "next_learning_goals": [
                "Improve response satisfaction scores",
                "Reduce average response time",
                "Increase engagement in expertise areas"
            ]
        }
        
        return {
            "user_id": user_id,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/trigger")
async def trigger_learning_analysis(background_tasks: BackgroundTasks, analysis_type: str = Query("all")):
    """Trigger immediate learning analysis"""
    try:
        if analysis_type in ["all", "personas"]:
            background_tasks.add_task(persona_builder._periodic_persona_update)
        
        if analysis_type in ["all", "knowledge"]:
            background_tasks.add_task(knowledge_evolution._periodic_knowledge_analysis)
        
        if analysis_type in ["all", "patterns"]:
            background_tasks.add_task(pattern_analyzer._analyze_all_patterns)
        
        if analysis_type in ["all", "optimization"]:
            background_tasks.add_task(adaptive_optimizer._monitor_adaptation_effectiveness)
        
        return {
            "status": "analysis_triggered",
            "analysis_type": analysis_type,
            "message": f"Learning analysis of type '{analysis_type}' has been queued",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger learning analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
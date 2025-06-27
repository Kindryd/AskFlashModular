"""
Intent Analyzer for AskFlash MCP System

This service analyzes user queries to understand intent, complexity,
and determine the best processing strategy.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

import redis.asyncio as redis
from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger(__name__)

class IntentAnalyzer:
    """
    Core intent analysis service
    
    Capabilities:
    - Query intent classification
    - Complexity assessment 
    - Sub-question generation
    - Search strategy determination
    - Context extraction
    """
    
    def __init__(self, openai_api_key: str, redis_client: redis.Redis):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.redis = redis_client
        
        # Intent classification categories
        self.intent_categories = {
            "informational": "User seeks factual information or explanations",
            "procedural": "User wants step-by-step instructions or how-to guidance", 
            "navigational": "User wants to find specific content or location",
            "transactional": "User wants to perform an action or complete a task",
            "comparative": "User wants to compare options or alternatives",
            "diagnostic": "User needs help troubleshooting or solving a problem",
            "creative": "User requests creative content or brainstorming",
            "analytical": "User wants analysis, insights, or data interpretation"
        }
        
    async def analyze_intent(self, task_id: str, query: str) -> Dict[str, Any]:
        """
        Analyze user query intent with ReAct methodology
        
        Args:
            task_id: Unique task identifier
            query: User query to analyze
            
        Returns:
            Intent analysis with classification, complexity, and strategy
        """
        try:
            logger.info(f"🧠 Starting intent analysis for task {task_id}")
            
            # ReAct Step 1: Initial Thought
            await self._emit_react_step(task_id, "thought", "I need to analyze the user's query to understand their intent and determine the best processing strategy.")
            
            # Validate query
            if not query or len(query.strip()) < settings.min_query_length:
                raise ValueError("Query is too short for meaningful analysis")
            
            if len(query) > settings.max_query_length:
                query = query[:settings.max_query_length] + "..."
            
            # ReAct Step 2: Action - Intent Classification
            await self._emit_react_step(task_id, "action", "Analyzing query intent using GPT-3.5 to classify user's goal and information needs")
            
            # Classify intent
            intent_classification = await self._classify_intent(query)
            
            # ReAct Step 3: Observation - Intent Results
            primary_intent = intent_classification.get("primary_intent", "unknown")
            await self._emit_react_step(task_id, "observation", f"Identified primary intent as '{primary_intent}' with confidence {intent_classification.get('confidence', 0):.2f}")
            
            # ReAct Step 4: Action - Complexity Assessment
            await self._emit_react_step(task_id, "action", "Assessing query complexity based on length, structure, and requirements")
            
            # Assess complexity
            complexity_assessment = await self._assess_complexity(query, intent_classification)
            
            # ReAct Step 5: Observation - Complexity Results
            complexity_level = complexity_assessment.get("complexity_level", "medium")
            await self._emit_react_step(task_id, "observation", f"Query complexity assessed as '{complexity_level}' requiring {complexity_assessment.get('estimated_time', 'unknown')} processing time")
            
            # ReAct Step 6: Thought - Strategy Planning
            await self._emit_react_step(task_id, "thought", "Based on the intent and complexity, I'll determine the optimal processing strategy including resource requirements and approach.")
            
            # ReAct Step 7: Action - Strategy Determination
            await self._emit_react_step(task_id, "action", "Determining processing strategy and resource requirements")
            
            # Determine processing strategy
            processing_strategy = await self._determine_strategy(query, intent_classification, complexity_assessment)
            
            # ReAct Step 8: Observation - Strategy Results
            web_search_needed = processing_strategy.get("web_search_required", False)
            strategy_approach = processing_strategy.get("approach", "standard")
            await self._emit_react_step(task_id, "observation", f"Strategy determined: {strategy_approach} approach, web search {'required' if web_search_needed else 'not needed'}")
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(intent_classification, complexity_assessment, processing_strategy)
            
            # Compile results
            analysis_result = {
                "task_id": task_id,
                "query": query,
                "intent_classification": intent_classification,
                "complexity_assessment": complexity_assessment,
                "processing_strategy": processing_strategy,
                "recommendations": recommendations,
                "metadata": {
                    "analyzer_version": "1.0.0",
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 0  # Will be calculated by caller
                }
            }
            
            # Cache analysis result
            await self._cache_analysis(task_id, analysis_result)
            
            # ReAct Step 9: Final Answer
            await self._emit_react_step(task_id, "final_answer", f"Intent analysis complete! Query categorized as '{primary_intent}' with '{complexity_level}' complexity. Ready for {strategy_approach} processing approach.")
            
            logger.info(f"✅ Intent analysis completed for task {task_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Intent analysis failed for task {task_id}: {e}")
            await self._emit_react_step(task_id, "error", f"Analysis failed: {str(e)}")
            raise
    
    async def _basic_query_analysis(self, query: str) -> Dict[str, Any]:
        """Extract basic characteristics from query"""
        words = query.split()
        sentences = query.split('.')
        
        # Detect question types
        question_words = ["what", "why", "how", "when", "where", "who", "which", "can", "should", "is", "are", "do", "does"]
        has_question_word = any(word.lower() in question_words for word in words[:3])
        has_question_mark = "?" in query
        
        # Detect temporal indicators
        temporal_words = ["today", "now", "current", "latest", "recent", "yesterday", "tomorrow", "this week", "last month"]
        has_temporal = any(word.lower() in temporal_words for word in words)
        
        # Detect web search indicators
        web_search_indicators = any(keyword.lower() in query.lower() for keyword in settings.web_search_keywords)
        
        return {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "character_count": len(query),
            "has_question_word": has_question_word,
            "has_question_mark": has_question_mark,
            "is_question": has_question_word or has_question_mark,
            "has_temporal_indicators": has_temporal,
            "requires_web_search": web_search_indicators,
            "language": "en",  # Could be enhanced with language detection
            "query_type": "question" if (has_question_word or has_question_mark) else "statement"
        }
    
    async def _classify_intent(self, query: str) -> Dict[str, Any]:
        """Use GPT to classify user intent"""
        
        system_prompt = f"""You are an expert at analyzing user intent in queries. Classify the following query into one of these categories:

{json.dumps(self.intent_categories, indent=2)}

Respond with a JSON object containing:
- primary_intent: the main category (one of the keys above)
- confidence: confidence score 0.0-1.0
- secondary_intents: array of other possible intents (if applicable)
- reasoning: brief explanation of the classification

Be precise and consider the context clues in the query."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.warning(f"GPT intent classification failed: {e}")
            # Fallback to rule-based classification
            return await self._fallback_intent_classification(query)
    
    async def _fallback_intent_classification(self, query: str) -> Dict[str, Any]:
        """Rule-based fallback for intent classification"""
        query_lower = query.lower()
        
        # Simple keyword-based classification
        if any(word in query_lower for word in ["what", "explain", "tell me about"]):
            return {
                "primary_intent": "informational",
                "confidence": 0.7,
                "secondary_intents": [],
                "reasoning": "Contains informational keywords"
            }
        elif any(word in query_lower for word in ["how", "step", "tutorial", "guide"]):
            return {
                "primary_intent": "procedural", 
                "confidence": 0.7,
                "secondary_intents": [],
                "reasoning": "Contains procedural keywords"
            }
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            return {
                "primary_intent": "comparative",
                "confidence": 0.7,
                "secondary_intents": [],
                "reasoning": "Contains comparative keywords"
            }
        else:
            return {
                "primary_intent": "informational",
                "confidence": 0.5,
                "secondary_intents": [],
                "reasoning": "Default classification"
            }
    
    async def _assess_complexity(self, query: str, intent: Dict) -> Dict[str, Any]:
        """Assess query complexity for processing strategy"""
        words = query.split()
        word_count = len(words)
        
        # Count complex indicators
        complex_indicators = 0
        
        # Multiple questions
        if query.count('?') > 1:
            complex_indicators += 1
            
        # Conditional language
        conditional_words = ["if", "when", "unless", "provided that", "assuming"]
        if any(word in query.lower() for word in conditional_words):
            complex_indicators += 1
            
        # Multiple entities or topics
        if query.count(' and ') > 1 or query.count(',') > 2:
            complex_indicators += 1
            
        # Technical jargon (simplified detection)
        if len([word for word in words if len(word) > 8]) > word_count * 0.2:
            complex_indicators += 1
            
        # Determine complexity level
        if word_count < 5:
            complexity_level = "very_low"
        elif word_count < settings.complexity_threshold_words and complex_indicators == 0:
            complexity_level = "low"
        elif word_count < 20 and complex_indicators <= 1:
            complexity_level = "medium"
        elif word_count < 40 or complex_indicators <= 2:
            complexity_level = "high"
        else:
            complexity_level = "very_high"
            
        return {
            "complexity_level": complexity_level,
            "word_count": word_count,
            "complex_indicators": complex_indicators,
            "estimated_processing_time_ms": self._estimate_processing_time(complexity_level),
            "requires_decomposition": complexity_level in ["high", "very_high"]
        }
    
    def _estimate_processing_time(self, complexity_level: str) -> int:
        """Estimate processing time based on complexity"""
        time_map = {
            "very_low": 2000,    # 2 seconds
            "low": 5000,         # 5 seconds  
            "medium": 10000,     # 10 seconds
            "high": 20000,       # 20 seconds
            "very_high": 35000   # 35 seconds
        }
        return time_map.get(complexity_level, 10000)
    
    async def _generate_sub_questions(self, query: str) -> List[str]:
        """Generate sub-questions for complex queries"""
        
        system_prompt = """You are an expert at breaking down complex questions into simpler sub-questions. 
        
Given a complex query, decompose it into 2-5 focused sub-questions that would help answer the original question comprehensively.

Respond with a JSON array of strings, each being a clear, specific sub-question.

Guidelines:
- Keep sub-questions focused and specific
- Ensure they logically contribute to answering the main question
- Avoid redundancy between sub-questions
- Make each sub-question answerable independently"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Complex query: {query}"}
                ],
                max_tokens=400,
                temperature=0.4
            )
            
            sub_questions = json.loads(response.choices[0].message.content)
            return sub_questions if isinstance(sub_questions, list) else []
            
        except Exception as e:
            logger.warning(f"Sub-question generation failed: {e}")
            return []
    
    async def _determine_strategy(self, query: str, intent: Dict, complexity: Dict) -> Dict[str, Any]:
        """Determine optimal processing strategy"""
        
        # Default strategy
        strategy = {
            "approach": "standard_query",
            "parallel_processing": False,
            "web_search_required": False,
            "embedding_priority": "high",
            "llm_model": "gpt-3.5-turbo",
            "estimated_stages": 5
        }
        
        # Adjust based on complexity
        if complexity["complexity_level"] in ["very_low", "low"]:
            strategy["approach"] = "quick_answer"
            strategy["estimated_stages"] = 3
            
        elif complexity["complexity_level"] == "very_high":
            strategy["approach"] = "complex_research"
            strategy["parallel_processing"] = True
            strategy["estimated_stages"] = 6
            strategy["llm_model"] = "gpt-4"
            
        # Check if web search is needed
        web_keywords = settings.web_search_keywords
        if any(keyword in query.lower() for keyword in web_keywords):
            strategy["web_search_required"] = True
            strategy["approach"] = "web_enhanced"
            
        # Adjust for intent type
        if intent.get("primary_intent") == "creative":
            strategy["llm_model"] = "gpt-4"
            strategy["embedding_priority"] = "medium"
            
        return strategy
    
    async def _generate_recommendations(self, intent: Dict, complexity: Dict, strategy: Dict) -> List[str]:
        """Generate processing recommendations"""
        recommendations = []
        
        if complexity["complexity_level"] in ["high", "very_high"]:
            recommendations.append("Consider breaking down into sub-questions")
            
        if strategy["web_search_required"]:
            recommendations.append("Include real-time web search for current information")
            
        if intent.get("primary_intent") == "comparative":
            recommendations.append("Structure response as clear comparison")
            
        if complexity["word_count"] > 30:
            recommendations.append("Use structured response format")
            
        return recommendations
    
    async def _cache_analysis(self, task_id: str, analysis: Dict[str, Any]):
        """Cache analysis result in Redis"""
        try:
            cache_key = f"intent_analysis:{task_id}"
            await self.redis.setex(
                cache_key, 
                600,  # 10 minute TTL
                json.dumps(analysis)
            )
        except Exception as e:
            logger.warning(f"Failed to cache analysis for {task_id}: {e}")
    
    async def _emit_react_step(self, task_id: str, step: str, message: str):
        """Emit ReAct step event via Redis"""
        try:
            react_data = {
                "task_id": task_id,
                "agent": "intent_analyzer",
                "step": step,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to react channel
            channel = f"ai:react:{task_id}"
            await self.redis.publish(channel, json.dumps(react_data))
            
        except Exception as e:
            logger.warning(f"Failed to emit ReAct step for {task_id}: {e}") 
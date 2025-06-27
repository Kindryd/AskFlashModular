"""
AI Executor for AskFlash MCP System

This service performs comprehensive AI reasoning using OpenAI models.
It synthesizes information from multiple sources and generates detailed responses.
"""

import json
import logging
import re
import tiktoken
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import redis.asyncio as redis
from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger(__name__)

class AIExecutor:
    """
    Core AI reasoning and execution service
    
    Capabilities:
    - Multi-document synthesis
    - Complex reasoning chains
    - Context-aware response generation
    - Source attribution
    - Token management
    """
    
    def __init__(self, openai_api_key: str, redis_client: redis.Redis):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.redis = redis_client
        
        # Token encoding for different models
        self.encoders = {
            "gpt-4": tiktoken.get_encoding("cl100k_base"),
            "gpt-3.5-turbo": tiktoken.get_encoding("cl100k_base"),
            "gpt-3.5-turbo-16k": tiktoken.get_encoding("cl100k_base")
        }
        
    async def execute_reasoning(self, task_id: str, reasoning_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AI reasoning with adaptive personalization
        
        Implements ReAct methodology with persona-driven optimization
        """
        try:
            query = reasoning_request["query"]
            context = reasoning_request.get("context", "")
            documents = reasoning_request.get("vector_hits", [])
            intent_analysis = reasoning_request.get("intent_analysis", {})
            
            # **ADAPTIVE INTEGRATION**: Extract adaptive recommendations
            adaptive_recommendations = reasoning_request.get("adaptive_recommendations", {})
            user_persona = reasoning_request.get("user_persona", {})
            response_style = reasoning_request.get("response_style", {})
            context_optimization = reasoning_request.get("context_optimization", {})
            conversation_flow = reasoning_request.get("conversation_flow", {})
            
            # Log adaptive optimization usage
            if adaptive_recommendations.get("confidence", 0) > 0.5:
                logger.info(f"🧠 Using adaptive optimization for task {task_id}: confidence {adaptive_recommendations.get('confidence', 0):.2f}")
                await self._emit_react_step(task_id, "thought", f"Adapting response for user based on learned persona (confidence: {adaptive_recommendations.get('confidence', 0):.1%})")
            
            # ReAct Step 1: Thought - Query Analysis
            await self._emit_react_step(task_id, "thought", "I need to analyze this query and determine the best approach for generating a comprehensive response.")
            
            # Process and validate documents
            processed_docs = await self._process_documents(documents, query)
            
            # ReAct Step 2: Observation - Document Analysis
            await self._emit_react_step(task_id, "observation", f"Found {len(processed_docs)} relevant documents to analyze and synthesize for the response.")
            
            # Determine processing strategy with adaptive optimization
            strategy = await self._determine_strategy(query, intent_analysis, len(processed_docs), adaptive_recommendations)
            
            # ReAct Step 3: Action - Strategy Selection
            await self._emit_react_step(task_id, "action", f"Selected {strategy.get('approach', 'standard')} approach based on query complexity and user preferences")
            
            # ReAct Step 4: Action - Document Analysis
            await self._emit_react_step(task_id, "action", f"Analyzing {len(processed_docs)} relevant documents using {strategy.get('model', 'unknown')}")
            
            # ReAct Step 5: Observation - Document Processing Results
            doc_summary = f"Found {len(processed_docs)} relevant documents with average relevance score of {sum(doc['relevance_score'] for doc in processed_docs) / len(processed_docs):.2f}" if processed_docs else "No relevant documents found"
            await self._emit_react_step(task_id, "observation", doc_summary)
            
            # Generate reasoning chain if complex task
            reasoning_steps = []
            if strategy.get("complexity_level") in ["high", "very_high"]:
                # ReAct Step 6: Thought - Complexity Assessment
                await self._emit_react_step(task_id, "thought", "This is a complex query that requires structured reasoning. I'll break it down into logical steps.")
                reasoning_steps = await self._generate_reasoning_chain(query, context, intent_analysis)
                # ReAct Step 7: Observation - Reasoning Chain
                await self._emit_react_step(task_id, "observation", f"Generated {len(reasoning_steps)} reasoning steps: {', '.join(reasoning_steps[:2])}{'...' if len(reasoning_steps) > 2 else ''}")
            
            # Construct comprehensive prompt
            system_prompt, user_prompt = await self._construct_prompts(
                query=query,
                context=context,
                documents=processed_docs,
                strategy=strategy,
                intent_analysis=intent_analysis,
                reasoning_steps=reasoning_steps
            )
            
            # ReAct Step 8: Action - AI Response Generation
            await self._emit_react_step(task_id, "action", f"Generating comprehensive response using {strategy.get('model', 'unknown')} with optimized prompts")
            
            # Generate response with retry logic
            response_data = await self._generate_response(
                model=strategy.get('model', settings.openai_model_primary),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_retries=2
            )
            
            # ReAct Step 9: Observation - Response Quality
            token_usage = response_data.get("token_usage", {})
            await self._emit_react_step(task_id, "observation", f"Generated response with {token_usage.get('total_tokens', 'unknown')} tokens. Now evaluating quality and sources.")
            
            # Post-process response
            final_response = await self._post_process_response(
                response_data=response_data,
                documents=processed_docs,
                strategy=strategy,
                query=query
            )
            
            # ReAct Step 10: Thought - Final Assessment
            confidence = self._calculate_confidence(final_response, processed_docs)
            await self._emit_react_step(task_id, "thought", f"Response quality assessment complete. Confidence score: {confidence:.2f}. The response addresses the query with proper source attribution.")
            
            # ReAct Step 11: Final Answer Preparation
            await self._emit_react_step(task_id, "action", "Finalizing response with metadata and source references")
            
            # Compile execution result
            execution_result = {
                "task_id": task_id,
                "query": query,
                "response": final_response,
                "reasoning_metadata": {
                    "model_used": strategy.get('model', settings.openai_model_primary),
                    "documents_processed": len(processed_docs),
                    "reasoning_steps": len(reasoning_steps),
                    "token_usage": response_data.get("token_usage", {}),
                    "processing_strategy": strategy.get("approach", "standard"),
                    "confidence_score": confidence
                },
                "sources": [doc.get("source_info", {}) for doc in processed_docs],
                "metadata": {
                    "executor_version": "1.0.0",
                    "execution_timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 0  # Will be calculated by caller
                }
            }
            
            # Cache execution result
            await self._cache_execution(task_id, execution_result)
            
            # ReAct Step 12: Final Answer
            await self._emit_react_step(task_id, "final_answer", f"Analysis complete! Providing comprehensive response based on {len(processed_docs)} sources with {confidence:.1%} confidence.")
            
            logger.info(f"✅ AI reasoning completed for task {task_id}")
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ AI reasoning failed for task {task_id}: {e}")
            await self._emit_react_step(task_id, "error", f"Reasoning failed: {str(e)}")
            raise
    
    def _select_model(self, strategy: Dict[str, Any], document_count: int) -> str:
        """Select appropriate model based on strategy and complexity"""
        
        # Use GPT-4 for complex tasks
        if strategy.get("complexity_level") == "very_high":
            return settings.openai_model_primary
        
        # Use GPT-4 for creative or analytical tasks
        intent = strategy.get("primary_intent", "")
        if intent in ["creative", "analytical"]:
            return settings.openai_model_primary
        
        # Use 16k model for large document sets
        if document_count > 5:
            return settings.openai_model_fallback
        
        # Use simple model for basic tasks
        if strategy.get("complexity_level") in ["very_low", "low"]:
            return settings.openai_model_simple
        
        # Default to primary model
        return settings.openai_model_primary
    
    async def _process_documents(self, documents: List[Dict], query: str) -> List[Dict[str, Any]]:
        """Process and prepare documents for reasoning"""
        processed_docs = []
        
        for i, doc in enumerate(documents[:settings.max_documents_per_query]):
            try:
                # Extract document content
                content = doc.get("content", "")
                if not content:
                    continue
                
                # Truncate if too long
                if len(content) > settings.max_document_length:
                    content = content[:settings.max_document_length] + "..."
                
                # Calculate relevance score (simplified)
                relevance_score = self._calculate_relevance(content, query)
                
                if relevance_score >= settings.relevance_threshold:
                    processed_doc = {
                        "id": doc.get("id", f"doc_{i}"),
                        "content": content,
                        "title": doc.get("title", f"Document {i+1}"),
                        "relevance_score": relevance_score,
                        "source_info": {
                            "id": doc.get("id", f"doc_{i}"),
                            "title": doc.get("title", ""),
                            "url": doc.get("url", ""),
                            "type": doc.get("type", "document")
                        }
                    }
                    processed_docs.append(processed_doc)
                    
            except Exception as e:
                logger.warning(f"Failed to process document {i}: {e}")
                continue
        
        # Sort by relevance
        processed_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info(f"Processed {len(processed_docs)} relevant documents")
        return processed_docs
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Calculate document relevance to query (simplified implementation)"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        # Calculate word overlap
        overlap = len(query_words.intersection(content_words))
        total_words = len(query_words)
        
        if total_words == 0:
            return 0.0
            
        return min(overlap / total_words, 1.0)
    
    async def _generate_reasoning_chain(self, query: str, context: str, intent_analysis: Dict) -> List[str]:
        """Generate reasoning steps for complex queries"""
        try:
            system_prompt = """You are an expert at breaking down complex reasoning tasks into clear steps.

Given a query and context, create a logical reasoning chain of 3-5 steps that would lead to a comprehensive answer.

Respond with a JSON array of strings, each representing a reasoning step.

Guidelines:
- Each step should build on the previous ones
- Steps should be specific and actionable
- Focus on logical flow and completeness
- Consider the query's intent and complexity"""

            user_prompt = f"""Query: {query}
Context: {context}
Intent Analysis: {json.dumps(intent_analysis, indent=2)}

Generate a reasoning chain for this task."""

            response = await self.client.chat.completions.create(
                model=settings.openai_model_simple,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.4
            )
            
            reasoning_steps = json.loads(response.choices[0].message.content)
            return reasoning_steps if isinstance(reasoning_steps, list) else []
            
        except Exception as e:
            logger.warning(f"Failed to generate reasoning chain: {e}")
            return []
    
    async def _construct_prompts(
        self, 
        query: str, 
        context: str, 
        documents: List[Dict], 
        strategy: Dict, 
        intent_analysis: Dict,
        reasoning_steps: List[str]
    ) -> Tuple[str, str]:
        """Construct system and user prompts for AI reasoning with adaptive personalization"""
        
        # Determine response format
        response_format = strategy.get("response_format", settings.default_response_format)
        intent_type = intent_analysis.get("primary_intent", "informational")
        
        # **ADAPTIVE INTEGRATION**: Build persona-driven system prompt
        adaptive_confidence = strategy.get("adaptive_confidence", 0.0)
        persona_guidance = ""
        
        if adaptive_confidence > 0.5:
            # Get adaptive preferences
            technical_depth = strategy.get("technical_depth", "medium")
            tone = strategy.get("tone", "professional")
            include_examples = strategy.get("include_examples", True)
            structured_format = strategy.get("structured_format", True)
            max_response_length = strategy.get("max_response_length", 800)
            personalization_level = strategy.get("personalization_level", "minimal")
            
            persona_guidance = f"""
PERSONALIZED RESPONSE GUIDANCE (Based on user preferences):
- Technical Depth: {technical_depth.upper()} - {"Provide detailed technical explanations" if technical_depth == "high" else "Use accessible language" if technical_depth == "low" else "Balance technical detail with clarity"}
- Communication Style: {tone.title()} tone
- Examples: {"Include practical examples and code snippets when relevant" if include_examples else "Focus on conceptual explanations without extensive examples"}
- Structure: {"Use clear headings, bullet points, and organized sections" if structured_format else "Provide flowing narrative response"}
- Response Length: Target approximately {max_response_length} words
- Personalization: {"Highly personalized based on user expertise and preferences" if personalization_level == "high" else "Moderately adapted to user patterns" if personalization_level == "medium" else "Standard response approach"}

USER PERSONA INSIGHTS:
{f"This user prefers {technical_depth} technical content with {tone} communication style." if adaptive_confidence > 0.7 else "Limited persona data available - use standard approach."}
"""
        
        # System prompt with adaptive personalization
        system_prompt = f"""You are an expert AI assistant specialized in {intent_type} queries. Your role is to provide comprehensive, accurate, and well-structured responses based on the provided context and documents.

{persona_guidance}

RESPONSE REQUIREMENTS:
- Format: {response_format}
- Include source citations when referencing documents
- Be precise and factual
- Structure your response clearly
- Maximum length: {strategy.get('max_response_length', settings.max_response_length)} words
- Technical depth: {strategy.get('technical_depth', 'medium').upper()}
- Tone: {strategy.get('tone', 'professional').title()}

REASONING APPROACH:
- Synthesize information from multiple sources
- Acknowledge uncertainty when information is incomplete
- Provide balanced perspectives when appropriate
- Use logical reasoning and evidence-based conclusions
{"- Include practical examples and code snippets when helpful" if strategy.get('include_examples', True) else "- Focus on clear explanations without extensive code examples"}

{"REASONING STEPS TO FOLLOW:" if reasoning_steps else ""}
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(reasoning_steps)) if reasoning_steps else ""}

Remember to cite sources using [Source: Document Title] format and adapt your response style to match the user's preferred level of technical detail."""

        # User prompt with documents
        user_prompt = f"""QUERY: {query}

{"CONTEXT: " + context if context else ""}

AVAILABLE DOCUMENTS:
"""
        
        for i, doc in enumerate(documents):
            user_prompt += f"""
[Document {i+1}: {doc['title']}]
{doc['content']}
(Relevance Score: {doc['relevance_score']:.2f})
"""
        
        user_prompt += f"""

Based on the above query, context, and documents, provide a comprehensive response that directly addresses the user's question. Use the reasoning steps if provided and cite relevant sources."""

        return system_prompt, user_prompt
    
    async def _generate_response(self, model: str, system_prompt: str, user_prompt: str, max_retries: int = 2) -> Dict[str, Any]:
        """Generate AI response with retry logic"""
        
        for attempt in range(max_retries + 1):
            try:
                # Calculate token limits
                total_tokens = self._count_tokens(system_prompt + user_prompt, model)
                max_tokens = min(settings.openai_max_tokens, 8192 - total_tokens - 100)  # Buffer
                
                if max_tokens < 100:
                    raise ValueError("Prompt too long for model context window")
                
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=settings.reasoning_temperature,
                    timeout=settings.openai_timeout
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "model": model,
                    "token_usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "finish_reason": response.choices[0].finish_reason
                }
                
            except Exception as e:
                logger.warning(f"Response generation attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries:
                    raise
                
                # Try with simpler model on retry
                if model == settings.openai_model_primary:
                    model = settings.openai_model_fallback
        
        raise Exception("All response generation attempts failed")
    
    def _count_tokens(self, text: str, model: str) -> int:
        """Count tokens for text using appropriate encoder"""
        encoder = self.encoders.get(model, self.encoders["gpt-3.5-turbo"])
        return len(encoder.encode(text))
    
    async def _post_process_response(self, response_data: Dict, documents: List[Dict], strategy: Dict, query: str) -> Dict[str, Any]:
        """Post-process and enhance the generated response"""
        
        content = response_data["content"]
        
        # Extract and validate source citations
        citations = self._extract_citations(content)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence({"content": content}, documents)
        
        # Structure the final response
        final_response = {
            "content": content,
            "confidence_score": confidence_score,
            "citations": citations,
            "response_type": strategy.get("response_format", "conversational"),
            "completeness_score": self._assess_completeness(content, query),
            "word_count": len(content.split()),
            "estimated_accuracy": min(confidence_score + 0.1, 1.0)  # Slight boost for well-cited responses
        }
        
        return final_response
    
    def _extract_citations(self, content: str) -> List[Dict[str, str]]:
        """Extract source citations from response content"""
        citations = []
        
        # Look for citation patterns like [Source: Document Title]
        citation_pattern = r'\[Source:\s*([^\]]+)\]'
        matches = re.findall(citation_pattern, content)
        
        for match in matches:
            citations.append({
                "source": match.strip(),
                "type": "document_reference"
            })
        
        return citations
    
    def _calculate_confidence(self, response: Dict[str, Any], documents: List[Dict]) -> float:
        """Calculate confidence score for response"""
        content = response.get("content", "")
        
        # Base confidence
        confidence = 0.5
        
        # Boost for citations
        citations = len(re.findall(r'\[Source:', content))
        if citations > 0:
            confidence += min(citations * 0.1, 0.3)
        
        # Boost for document coverage
        if documents:
            avg_relevance = sum(doc["relevance_score"] for doc in documents) / len(documents)
            confidence += avg_relevance * 0.2
        
        # Reduce for uncertainty language
        uncertainty_words = ["might", "possibly", "unclear", "uncertain", "unknown"]
        uncertainty_count = sum(1 for word in uncertainty_words if word in content.lower())
        confidence -= min(uncertainty_count * 0.05, 0.2)
        
        return min(max(confidence, 0.0), 1.0)
    
    def _assess_completeness(self, content: str, query: str) -> float:
        """Assess how completely the response addresses the query"""
        
        # Simple heuristic based on response length and query complexity
        query_words = len(query.split())
        response_words = len(content.split())
        
        # Base completeness
        if response_words < 50:
            return 0.3
        elif response_words < 150:
            return 0.6
        elif response_words < 300:
            return 0.8
        else:
            return 0.9
    
    async def _cache_execution(self, task_id: str, execution_result: Dict[str, Any]):
        """Cache execution result in Redis"""
        try:
            cache_key = f"executor_result:{task_id}"
            await self.redis.setex(
                cache_key,
                600,  # 10 minute TTL
                json.dumps(execution_result)
            )
        except Exception as e:
            logger.warning(f"Failed to cache execution result for {task_id}: {e}")
    
    async def _emit_react_step(self, task_id: str, step: str, message: str):
        """Emit ReAct step event via Redis"""
        try:
            react_data = {
                "task_id": task_id,
                "agent": "ai_executor",
                "step": step,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to react channel
            channel = f"ai:react:{task_id}"
            await self.redis.publish(channel, json.dumps(react_data))
            
        except Exception as e:
            logger.warning(f"Failed to emit ReAct step for {task_id}: {e}")
    
    async def _determine_strategy(self, query: str, intent_analysis: Dict, document_count: int, adaptive_recommendations: Dict) -> Dict[str, Any]:
        """
        Determine processing strategy using adaptive recommendations
        
        Implements ChatGPT's suggestion for persona-driven optimization
        """
        try:
            # Base strategy from intent analysis
            base_complexity = intent_analysis.get("complexity_assessment", {}).get("complexity_level", "medium")
            primary_intent = intent_analysis.get("primary_intent", "informational")
            
            # **ADAPTIVE INTEGRATION**: Get persona-driven recommendations
            response_style = adaptive_recommendations.get("response_style", {})
            context_optimization = adaptive_recommendations.get("context_optimization", {})
            conversation_flow = adaptive_recommendations.get("conversation_flow", {})
            user_persona = adaptive_recommendations.get("personalization", {})
            
            # Determine approach based on persona preferences
            approach = "standard"
            if conversation_flow.get("recommended_approach") == "technical_detailed":
                approach = "technical_deep_dive"
            elif conversation_flow.get("recommended_approach") == "explanatory":
                approach = "explanatory_narrative"
            elif conversation_flow.get("recommended_approach") == "comprehensive":
                approach = "comprehensive_analysis"
            
            # Adjust complexity based on user technical preference
            final_complexity = base_complexity
            if response_style.get("technical_depth") == "high":
                complexity_levels = ["very_low", "low", "medium", "high", "very_high"]
                current_index = complexity_levels.index(base_complexity) if base_complexity in complexity_levels else 2
                final_complexity = complexity_levels[min(current_index + 1, 4)]
            elif response_style.get("technical_depth") == "low":
                complexity_levels = ["very_low", "low", "medium", "high", "very_high"]
                current_index = complexity_levels.index(base_complexity) if base_complexity in complexity_levels else 2
                final_complexity = complexity_levels[max(current_index - 1, 0)]
            
            # Select model based on adapted strategy
            model = self._select_model({
                "complexity_level": final_complexity,
                "primary_intent": primary_intent
            }, document_count)
            
            # Determine response length preference
            max_response_length = 800  # Default
            if response_style.get("detail_level") == "detailed":
                max_response_length = 1200
            elif response_style.get("detail_level") == "brief":
                max_response_length = 400
            
            strategy = {
                "approach": approach,
                "complexity_level": final_complexity,
                "primary_intent": primary_intent,
                "model": model,
                "max_response_length": max_response_length,
                "include_examples": response_style.get("include_examples", True),
                "structured_format": response_style.get("structured_format", True),
                "technical_depth": response_style.get("technical_depth", "medium"),
                "tone": response_style.get("tone", "professional"),
                "personalization_level": user_persona.get("personalization_level", "minimal"),
                "escalation_risk": conversation_flow.get("escalation_risk", 0.0),
                "context_needs_optimization": context_optimization.get("needs_more_context", False),
                "context_relevance_score": context_optimization.get("context_relevance_score", 0.5),
                "adaptive_confidence": adaptive_recommendations.get("confidence", 0.0)
            }
            
            logger.info(f"🧠 Adaptive strategy: {approach} with {final_complexity} complexity for {response_style.get('technical_depth', 'medium')} technical depth")
            
            return strategy
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to determine adaptive strategy: {e}, using defaults")
            return {
                "approach": "standard",
                "complexity_level": intent_analysis.get("complexity_assessment", {}).get("complexity_level", "medium"),
                "primary_intent": intent_analysis.get("primary_intent", "informational"),
                "model": self._select_model({}, document_count),
                "max_response_length": 800,
                "include_examples": True,
                "structured_format": True,
                "technical_depth": "medium",
                "tone": "professional",
                "adaptive_confidence": 0.0
            } 
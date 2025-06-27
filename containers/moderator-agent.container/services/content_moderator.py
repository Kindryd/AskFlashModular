import asyncio
import logging
import time
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from urllib.parse import urlparse

import redis.asyncio as redis
from core.config import settings

logger = logging.getLogger(__name__)

class ContentModerator:
    """Content moderation service with safety checks and quality assessment"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.moderation_cache: Dict[str, Any] = {}
        
        # Compile regex patterns for efficiency
        self.profanity_pattern = self._compile_profanity_pattern()
        self.spam_patterns = self._compile_spam_patterns()
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            if settings.CACHE_ENABLED:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("✅ Redis connection established for moderation caching")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed, using memory cache: {e}")
            self.redis_client = None
    
    def _compile_profanity_pattern(self) -> re.Pattern:
        """Compile profanity detection pattern"""
        # Basic profanity list (extend as needed)
        profanity_words = [
            r'\bdamn\b', r'\bhell\b', r'\bcrap\b',
            # Add more patterns as needed
        ] + [re.escape(word) for word in settings.BLOCKED_WORDS]
        
        pattern = '|'.join(profanity_words)
        return re.compile(pattern, re.IGNORECASE)
    
    def _compile_spam_patterns(self) -> List[re.Pattern]:
        """Compile spam detection patterns"""
        spam_patterns = [
            re.compile(r'click\s+here', re.IGNORECASE),
            re.compile(r'limited\s+time\s+offer', re.IGNORECASE),
            re.compile(r'act\s+now', re.IGNORECASE),
            re.compile(r'free\s+money', re.IGNORECASE),
            re.compile(r'\$\d+.*guaranteed', re.IGNORECASE),
            re.compile(r'urgent.*response', re.IGNORECASE),
            re.compile(r'congratulations.*winner', re.IGNORECASE)
        ]
        return spam_patterns
    
    def _generate_cache_key(self, content: str, check_type: str = "full") -> str:
        """Generate cache key for moderation result"""
        cache_data = f"{content}:{check_type}:{settings.TOXICITY_THRESHOLD}"
        return f"moderation:{hashlib.md5(cache_data.encode()).hexdigest()}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached moderation result"""
        try:
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Use memory cache
                if cache_key in self.moderation_cache:
                    cached_item = self.moderation_cache[cache_key]
                    if time.time() - cached_item["timestamp"] < settings.CACHE_TTL:
                        return cached_item["data"]
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache moderation result"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key,
                    settings.CACHE_TTL,
                    json.dumps(result)
                )
            else:
                # Use memory cache with size limit
                if len(self.moderation_cache) >= settings.CACHE_MAX_SIZE:
                    # Remove oldest entry
                    oldest_key = min(
                        self.moderation_cache.keys(),
                        key=lambda k: self.moderation_cache[k]["timestamp"]
                    )
                    del self.moderation_cache[oldest_key]
                
                self.moderation_cache[cache_key] = {
                    "data": result,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    def _check_profanity(self, content: str) -> Tuple[bool, List[str]]:
        """Check for profanity in content"""
        if not settings.ENABLE_PROFANITY_FILTER:
            return False, []
        
        matches = self.profanity_pattern.findall(content.lower())
        has_profanity = len(matches) > 0
        
        return has_profanity, matches
    
    def _check_spam(self, content: str) -> Tuple[float, List[str]]:
        """Check for spam indicators"""
        if not settings.ENABLE_SPAM_DETECTION:
            return 0.0, []
        
        spam_indicators = []
        spam_score = 0.0
        
        # Check spam patterns
        for pattern in self.spam_patterns:
            if pattern.search(content):
                spam_indicators.append(pattern.pattern)
                spam_score += 0.2
        
        # Check for excessive capitalization
        caps_ratio = sum(1 for c in content if c.isupper()) / len(content) if content else 0
        if caps_ratio > 0.5:
            spam_indicators.append("excessive_caps")
            spam_score += 0.3
        
        # Check for excessive punctuation
        punct_ratio = sum(1 for c in content if c in "!?") / len(content) if content else 0
        if punct_ratio > 0.1:
            spam_indicators.append("excessive_punctuation")
            spam_score += 0.2
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', content):
            spam_indicators.append("repeated_characters")
            spam_score += 0.3
        
        return min(spam_score, 1.0), spam_indicators
    
    def _check_urls(self, content: str) -> Tuple[bool, List[str]]:
        """Check URLs in content"""
        urls = self.url_pattern.findall(content)
        suspicious_urls = []
        
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Check if domain is in allowed list
                if settings.ALLOWED_DOMAINS and domain not in settings.ALLOWED_DOMAINS:
                    suspicious_urls.append(url)
                
                # Check for suspicious patterns
                if any(suspicious in domain for suspicious in ['bit.ly', 'tinyurl', 'goo.gl']):
                    suspicious_urls.append(url)
                    
            except Exception:
                suspicious_urls.append(url)
        
        has_suspicious = len(suspicious_urls) > 0
        return has_suspicious, suspicious_urls
    
    def _assess_quality(self, content: str) -> Dict[str, Any]:
        """Assess content quality"""
        if not settings.ENABLE_QUALITY_ASSESSMENT:
            return {"quality_score": 1.0, "quality_issues": []}
        
        quality_issues = []
        quality_score = 1.0
        
        # Check length
        if len(content) < settings.MIN_CONTENT_LENGTH:
            quality_issues.append("too_short")
            quality_score -= 0.3
        elif len(content) > settings.MAX_CONTENT_LENGTH:
            quality_issues.append("too_long")
            quality_score -= 0.2
        
        # Check for coherence (basic)
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) > 1:
            # Check if sentences are reasonable length
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length < 3:
                quality_issues.append("fragmented_sentences")
                quality_score -= 0.2
            elif avg_sentence_length > 50:
                quality_issues.append("overly_long_sentences")
                quality_score -= 0.1
        
        # Check for repetition
        words = content.lower().split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.3:
                quality_issues.append("high_repetition")
                quality_score -= 0.3
        
        return {
            "quality_score": max(quality_score, 0.0),
            "quality_issues": quality_issues,
            "word_count": len(words) if 'words' in locals() else len(content.split()),
            "sentence_count": len(sentences)
        }
    
    def _calculate_toxicity_score(self, content: str) -> float:
        """Calculate basic toxicity score (simplified implementation)"""
        if not settings.ENABLE_TOXICITY_CHECK:
            return 0.0
        
        toxicity_score = 0.0
        
        # Check for aggressive language patterns
        aggressive_patterns = [
            r'\b(hate|stupid|idiot|moron)\b',
            r'\b(kill|die|death)\b',
            r'\b(racist|sexist)\b'
        ]
        
        for pattern in aggressive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                toxicity_score += 0.3
        
        # Check profanity contribution
        has_profanity, _ = self._check_profanity(content)
        if has_profanity:
            toxicity_score += 0.4
        
        return min(toxicity_score, 1.0)
    
    async def moderate_content(
        self, 
        content: str, 
        content_type: str = "text",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive content moderation"""
        
        if not content or not isinstance(content, str):
            return {
                "approved": False,
                "reason": "Invalid or empty content",
                "confidence": 1.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Check cache first
        cache_key = self._generate_cache_key(content, content_type)
        if settings.CACHE_ENABLED:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"🎯 Cache hit for content moderation")
                return cached_result
        
        try:
            logger.info(f"🛡️ Moderating {content_type} content ({len(content)} chars)")
            
            # Initialize result
            moderation_result = {
                "approved": True,
                "confidence": 1.0,
                "reason": "Content approved",
                "checks": {},
                "flags": [],
                "metadata": {
                    "content_type": content_type,
                    "content_length": len(content),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Profanity check
            has_profanity, profanity_matches = self._check_profanity(content)
            moderation_result["checks"]["profanity"] = {
                "detected": has_profanity,
                "matches": profanity_matches
            }
            
            if has_profanity:
                moderation_result["flags"].append("profanity_detected")
                moderation_result["confidence"] -= 0.3
            
            # Spam check
            spam_score, spam_indicators = self._check_spam(content)
            moderation_result["checks"]["spam"] = {
                "score": spam_score,
                "threshold": settings.SPAM_THRESHOLD,
                "indicators": spam_indicators
            }
            
            if spam_score > settings.SPAM_THRESHOLD:
                moderation_result["flags"].append("spam_detected")
                moderation_result["confidence"] -= 0.4
            
            # URL check
            has_suspicious_urls, suspicious_urls = self._check_urls(content)
            moderation_result["checks"]["urls"] = {
                "suspicious_detected": has_suspicious_urls,
                "suspicious_urls": suspicious_urls
            }
            
            if has_suspicious_urls and not settings.ALLOW_EXTERNAL_LINKS:
                moderation_result["flags"].append("suspicious_urls")
                moderation_result["confidence"] -= 0.2
            
            # Toxicity check
            toxicity_score = self._calculate_toxicity_score(content)
            moderation_result["checks"]["toxicity"] = {
                "score": toxicity_score,
                "threshold": settings.TOXICITY_THRESHOLD
            }
            
            if toxicity_score > settings.TOXICITY_THRESHOLD:
                moderation_result["flags"].append("high_toxicity")
                moderation_result["confidence"] -= 0.5
            
            # Quality assessment
            quality_assessment = self._assess_quality(content)
            moderation_result["checks"]["quality"] = quality_assessment
            
            if quality_assessment["quality_score"] < settings.QUALITY_THRESHOLD:
                moderation_result["flags"].append("low_quality")
                moderation_result["confidence"] -= 0.2
            
            # Final approval decision
            has_blocking_flags = any(
                flag in moderation_result["flags"] 
                for flag in ["profanity_detected", "spam_detected", "high_toxicity"]
            )
            
            if has_blocking_flags or moderation_result["confidence"] < settings.CONFIDENCE_THRESHOLD:
                moderation_result["approved"] = False
                moderation_result["reason"] = f"Content blocked due to: {', '.join(moderation_result['flags'])}"
            
            # Log moderation action if enabled
            if settings.LOG_MODERATION_ACTIONS:
                log_data = {
                    "content_length": len(content),
                    "approved": moderation_result["approved"],
                    "flags": moderation_result["flags"],
                    "confidence": moderation_result["confidence"]
                }
                logger.info(f"📊 Moderation result: {log_data}")
            
            # Cache the result
            if settings.CACHE_ENABLED:
                await self._cache_result(cache_key, moderation_result)
            
            return moderation_result
            
        except Exception as e:
            logger.error(f"❌ Content moderation failed: {e}")
            return {
                "approved": False,
                "reason": f"Moderation error: {str(e)}",
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def validate_ai_response(
        self, 
        response: str, 
        query: str = "", 
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """Validate AI-generated response"""
        
        sources = sources or []
        
        # Basic content moderation
        moderation_result = await self.moderate_content(
            response, 
            content_type="ai_response",
            context={"query": query, "sources": sources}
        )
        
        # Additional AI response specific checks
        ai_specific_checks = {
            "has_sources": len(sources) > 0,
            "source_attribution": settings.REQUIRE_SOURCE_ATTRIBUTION and len(sources) > 0,
            "response_relevance": self._check_response_relevance(response, query),
            "factual_claims": self._identify_factual_claims(response)
        }
        
        moderation_result["ai_response_checks"] = ai_specific_checks
        
        # Adjust approval based on AI-specific requirements
        if settings.REQUIRE_SOURCE_ATTRIBUTION and not ai_specific_checks["has_sources"]:
            moderation_result["flags"].append("missing_source_attribution")
            moderation_result["approved"] = False
            moderation_result["reason"] = "AI response requires source attribution"
        
        return moderation_result
    
    def _check_response_relevance(self, response: str, query: str) -> Dict[str, Any]:
        """Basic relevance check between query and response"""
        if not query:
            return {"relevance_score": 1.0, "method": "no_query"}
        
        # Simple keyword overlap check
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        common_words = query_words.intersection(response_words)
        relevance_score = len(common_words) / len(query_words) if query_words else 1.0
        
        return {
            "relevance_score": relevance_score,
            "method": "keyword_overlap",
            "common_words": list(common_words)
        }
    
    def _identify_factual_claims(self, content: str) -> List[str]:
        """Identify potential factual claims in content"""
        # Simple pattern matching for factual statements
        factual_patterns = [
            r'\d+%',  # Percentages
            r'\d+\s+(years?|months?|days?)',  # Time periods
            r'according to',  # Attribution
            r'studies show',  # Research claims
            r'research indicates',  # Research claims
        ]
        
        factual_claims = []
        for pattern in factual_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            factual_claims.extend(matches)
        
        return factual_claims
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get moderation service statistics"""
        cache_stats = {
            "memory_cache_size": len(self.moderation_cache),
            "cache_enabled": settings.CACHE_ENABLED,
            "redis_connected": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                cache_stats["redis_keys"] = await self.redis_client.dbsize()
            except Exception:
                cache_stats["redis_keys"] = "unknown"
        
        return {
            "service": "Moderator Agent",
            "version": settings.SERVICE_VERSION,
            "moderation_config": {
                "toxicity_threshold": settings.TOXICITY_THRESHOLD,
                "spam_threshold": settings.SPAM_THRESHOLD,
                "quality_threshold": settings.QUALITY_THRESHOLD,
                "confidence_threshold": settings.CONFIDENCE_THRESHOLD
            },
            "enabled_checks": {
                "toxicity": settings.ENABLE_TOXICITY_CHECK,
                "profanity": settings.ENABLE_PROFANITY_FILTER,
                "spam": settings.ENABLE_SPAM_DETECTION,
                "quality": settings.ENABLE_QUALITY_ASSESSMENT
            },
            "cache_stats": cache_stats,
            "performance": {
                "max_concurrent_checks": settings.MAX_CONCURRENT_CHECKS,
                "check_timeout": settings.CHECK_TIMEOUT,
                "retry_attempts": settings.RETRY_ATTEMPTS
            }
        } 
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
import json
import hashlib
from datetime import datetime, timedelta
import re

from duckduckgo_search import DDGS
import redis.asyncio as redis
from core.config import settings

logger = logging.getLogger(__name__)

class WebSearcher:
    """DuckDuckGo web search service with caching and result processing"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.search_cache: Dict[str, Any] = {}
        self.last_search_time = 0
        
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
                logger.info("✅ Redis connection established for caching")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed, using memory cache: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, query: str, search_type: str = "web") -> str:
        """Generate cache key for search query"""
        cache_data = f"{query}:{search_type}:{settings.DUCKDUCKGO_REGION}"
        return f"websearch:{hashlib.md5(cache_data.encode()).hexdigest()}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search result"""
        try:
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Use memory cache
                if cache_key in self.search_cache:
                    cached_item = self.search_cache[cache_key]
                    if time.time() - cached_item["timestamp"] < settings.CACHE_TTL:
                        return cached_item["data"]
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache search result"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key, 
                    settings.CACHE_TTL, 
                    json.dumps(result)
                )
            else:
                # Use memory cache with size limit
                if len(self.search_cache) >= settings.CACHE_MAX_SIZE:
                    # Remove oldest entry
                    oldest_key = min(
                        self.search_cache.keys(),
                        key=lambda k: self.search_cache[k]["timestamp"]
                    )
                    del self.search_cache[oldest_key]
                
                self.search_cache[cache_key] = {
                    "data": result,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    def _rate_limit(self):
        """Apply rate limiting between searches"""
        current_time = time.time()
        time_since_last = current_time - self.last_search_time
        
        if time_since_last < settings.REQUEST_DELAY:
            sleep_time = settings.REQUEST_DELAY - time_since_last
            time.sleep(sleep_time)
        
        self.last_search_time = time.time()
    
    def _extract_content(self, result: Dict[str, Any]) -> str:
        """Extract and clean content from search result"""
        content = result.get("body", "")
        
        if not content:
            return ""
        
        # Clean HTML tags if present
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Truncate if too long
        if len(content) > settings.MAX_CONTENT_LENGTH:
            content = content[:settings.MAX_CONTENT_LENGTH] + "..."
        
        return content
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for search result"""
        score = 0.0
        query_words = set(query.lower().split())
        
        # Score based on title match
        title = result.get("title", "").lower()
        title_words = set(title.split())
        title_match_ratio = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
        score += title_match_ratio * 0.4
        
        # Score based on content match
        content = result.get("body", "").lower()
        content_words = set(content.split())
        content_match_ratio = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0
        score += content_match_ratio * 0.3
        
        # Score based on URL relevance
        url = result.get("href", "").lower()
        url_match_ratio = len(query_words.intersection(set(url.split("/")))) / len(query_words) if query_words else 0
        score += url_match_ratio * 0.2
        
        # Bonus for exact phrase matches
        query_phrase = query.lower()
        if query_phrase in title:
            score += 0.3
        elif query_phrase in content:
            score += 0.2
        
        return min(score, 1.0)
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on similarity"""
        if not settings.ENABLE_DEDUPLICATION:
            return results
        
        unique_results = []
        seen_urls = set()
        
        for result in results:
            url = result.get("href", "")
            title = result.get("title", "")
            
            # Skip if exact URL already seen
            if url in seen_urls:
                continue
            
            # Check for similar titles
            is_similar = False
            for existing in unique_results:
                existing_title = existing.get("title", "")
                
                # Simple similarity check based on common words
                title_words = set(title.lower().split())
                existing_words = set(existing_title.lower().split())
                
                if title_words and existing_words:
                    similarity = len(title_words.intersection(existing_words)) / len(title_words.union(existing_words))
                    if similarity > settings.SIMILARITY_THRESHOLD:
                        is_similar = True
                        break
            
            if not is_similar:
                unique_results.append(result)
                seen_urls.add(url)
        
        return unique_results
    
    async def search_web(self, query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Perform web search using DuckDuckGo"""
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        max_results = max_results or settings.MAX_RESULTS
        cache_key = self._generate_cache_key(query, "web")
        
        # Check cache first
        if settings.CACHE_ENABLED:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"🎯 Cache hit for query: {query[:50]}...")
                return cached_result
        
        try:
            # Initialize Redis if not done
            if not self.redis_client and settings.CACHE_ENABLED:
                await self.initialize()
            
            # Apply rate limiting
            self._rate_limit()
            
            logger.info(f"🔍 Searching web for: {query[:50]}...")
            
            # Perform search with retry logic
            results = []
            for attempt in range(settings.RETRY_ATTEMPTS):
                try:
                    with DDGS() as ddgs:
                        ddgs_results = list(ddgs.text(
                            keywords=query,
                            region=settings.DUCKDUCKGO_REGION,
                            safesearch=settings.DUCKDUCKGO_SAFESEARCH,
                            timelimit=settings.DUCKDUCKGO_TIME,
                            max_results=max_results
                        ))
                        
                        results = ddgs_results
                        break
                        
                except Exception as e:
                    logger.warning(f"Search attempt {attempt + 1} failed: {e}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        await asyncio.sleep(settings.RETRY_DELAY)
                    else:
                        raise
            
            # Process results
            processed_results = []
            for result in results:
                try:
                    # Extract and clean content
                    content = self._extract_content(result)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(result, query)
                    
                    # Skip low relevance results
                    if relevance_score < settings.MIN_RELEVANCE_SCORE:
                        continue
                    
                    processed_result = {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "content": content,
                        "relevance_score": relevance_score,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    processed_results.append(processed_result)
                    
                except Exception as e:
                    logger.warning(f"Error processing result: {e}")
                    continue
            
            # Deduplicate results
            processed_results = self._deduplicate_results(processed_results)
            
            # Sort by relevance score
            processed_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Prepare final response
            search_response = {
                "query": query,
                "results": processed_results,
                "total_results": len(processed_results),
                "search_time": datetime.utcnow().isoformat(),
                "cached": False,
                "source": "duckduckgo"
            }
            
            # Cache the result
            if settings.CACHE_ENABLED:
                await self._cache_result(cache_key, search_response)
            
            logger.info(f"✅ Found {len(processed_results)} relevant results for: {query[:50]}...")
            return search_response
            
        except Exception as e:
            logger.error(f"❌ Web search failed for query '{query}': {e}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "search_time": datetime.utcnow().isoformat(),
                "cached": False,
                "error": str(e),
                "source": "duckduckgo"
            }
    
    async def search_instant_answers(self, query: str) -> Dict[str, Any]:
        """Get instant answers from DuckDuckGo"""
        cache_key = self._generate_cache_key(query, "instant")
        
        # Check cache first
        if settings.CACHE_ENABLED:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
        
        try:
            self._rate_limit()
            
            logger.info(f"🎯 Getting instant answer for: {query[:50]}...")
            
            with DDGS() as ddgs:
                instant_results = list(ddgs.answers(keywords=query))
            
            if instant_results:
                instant_answer = {
                    "query": query,
                    "answer": instant_results[0],
                    "source": "duckduckgo_instant",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False
                }
            else:
                instant_answer = {
                    "query": query,
                    "answer": None,
                    "source": "duckduckgo_instant",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False
                }
            
            # Cache the result
            if settings.CACHE_ENABLED:
                await self._cache_result(cache_key, instant_answer)
            
            return instant_answer
            
        except Exception as e:
            logger.error(f"❌ Instant answer search failed: {e}")
            return {
                "query": query,
                "answer": None,
                "error": str(e),
                "source": "duckduckgo_instant",
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get search statistics"""
        cache_stats = {
            "memory_cache_size": len(self.search_cache),
            "cache_enabled": settings.CACHE_ENABLED,
            "redis_connected": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                cache_stats["redis_keys"] = await self.redis_client.dbsize()
            except Exception:
                cache_stats["redis_keys"] = "unknown"
        
        return {
            "service": "Web Search Agent",
            "version": settings.SERVICE_VERSION,
            "search_config": {
                "max_results": settings.MAX_RESULTS,
                "region": settings.DUCKDUCKGO_REGION,
                "safesearch": settings.DUCKDUCKGO_SAFESEARCH,
                "deduplication": settings.ENABLE_DEDUPLICATION
            },
            "cache_stats": cache_stats,
            "performance": {
                "request_delay": settings.REQUEST_DELAY,
                "timeout": settings.SEARCH_TIMEOUT,
                "retry_attempts": settings.RETRY_ATTEMPTS
            }
        } 
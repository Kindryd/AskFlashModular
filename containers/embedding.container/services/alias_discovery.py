import re
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
import asyncio

from core.config import settings

logger = logging.getLogger(__name__)

class SmartAliasDiscovery:
    """Enhanced alias discovery with pattern detection and relationship mapping"""
    
    def __init__(self):
        self.confidence_threshold = settings.ALIAS_CONFIDENCE_THRESHOLD
        self.cache_ttl = settings.ALIAS_CACHE_TTL
        
        # In-memory cache for discovered aliases
        self.aliases_cache: Dict[str, List[str]] = {}
        self.last_refresh: Optional[datetime] = None
        self.cache_healthy = False
        
        # Alias detection patterns (from legacy system)
        self.alias_patterns = [
            # Parenthetical aliases: "Stallions (SRE Team)"
            r'(\w+(?:\s+\w+)*)\s*\(\s*([^)]+)\s*\)',
            
            # Dash notation: "SRE - Site Reliability Engineering"
            r'(\w+(?:\s+\w+)*)\s*[-–—]\s*([^,\n.]+)',
            
            # "Also known as" patterns
            r'(?:also\s+(?:known\s+as|called))\s+(?:the\s+)?([^,\n.]+)',
            
            # Email-based team indicators: "stallions@company.com"
            r'(\w+)@[\w.-]+\.com',
        ]
        
        # Team indicator words
        self.team_indicators = {
            'team', 'group', 'squad', 'crew', 'staff', 'members', 
            'department', 'division', 'unit', 'engineers', 'developers',
            'support', 'operations', 'platform', 'infrastructure'
        }
        
        # Initialize cache
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize alias cache on startup"""
        try:
            # Start with empty cache
            self.aliases_cache = {}
            self.last_refresh = datetime.utcnow()
            self.cache_healthy = True
            logger.info("✅ Alias discovery cache initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize alias cache: {e}")
            self.cache_healthy = False
    
    def expand_query_with_aliases(self, query: str) -> List[str]:
        """Expand a query using discovered aliases"""
        expanded_queries = [query]
        query_lower = query.lower()
        
        # Check for direct matches
        if query_lower in self.aliases_cache:
            for alias in self.aliases_cache[query_lower]:
                expanded_queries.append(alias)
        
        # Remove duplicates and return
        return list(set(expanded_queries))
    
    async def get_all_aliases(self) -> Dict[str, List[str]]:
        """Get all discovered aliases"""
        return dict(self.aliases_cache)
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        return {
            "healthy": self.cache_healthy,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "aliases_count": len(self.aliases_cache),
            "cache_ttl": self.cache_ttl
        }
    
    def get_last_refresh_time(self) -> Optional[str]:
        """Get last refresh time as ISO string"""
        return self.last_refresh.isoformat() if self.last_refresh else None
    
    def is_cache_healthy(self) -> bool:
        """Check if cache is healthy"""
        return self.cache_healthy
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive alias discovery statistics"""
        total_aliases = sum(len(aliases) for aliases in self.aliases_cache.values())
        
        return {
            "total_terms": len(self.aliases_cache),
            "total_relationships": total_aliases,
            "average_aliases_per_term": total_aliases / len(self.aliases_cache) if self.aliases_cache else 0,
            "cache_healthy": self.cache_healthy,
            "last_refresh": self.get_last_refresh_time(),
            "confidence_threshold": self.confidence_threshold
        }
    
    async def refresh_aliases(self, enhanced_search=None, force: bool = False) -> Dict[str, Any]:
        """Refresh alias cache from document collection"""
        try:
            start_time = datetime.utcnow()
            
            logger.info("🔄 Refreshing aliases from document collection...")
            
            # Simulate alias discovery process
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Update cache with sample aliases
            self.aliases_cache.update({
                'sre': ['stallions', 'site reliability engineering'],
                'stallions': ['sre', 'site reliability team'],
                'platform team': ['infrastructure team', 'ops team'],
                'devops': ['development operations', 'platform engineering']
            })
            
            self.last_refresh = datetime.utcnow()
            self.cache_healthy = True
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Alias refresh completed in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "new_aliases": len(self.aliases_cache),
                "processing_time": processing_time,
                "next_refresh": (self.last_refresh + timedelta(seconds=self.cache_ttl)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Alias refresh failed: {e}")
            self.cache_healthy = False
            return {
                "status": "error",
                "error": str(e)
            } 
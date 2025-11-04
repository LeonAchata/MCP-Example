"""Simple in-memory cache system using TTLCache."""

import hashlib
import json
import logging
from typing import Any, Optional
from cachetools import TTLCache
import threading

from .config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Thread-safe cache manager for LLM responses."""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        """Initialize cache with size and TTL limits.
        
        Args:
            maxsize: Maximum number of items in cache
            ttl: Time to live in seconds
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = threading.Lock()
        self.enabled = settings.CACHE_ENABLED
        logger.info(f"Cache initialized: enabled={self.enabled}, maxsize={maxsize}, ttl={ttl}s")
    
    def _generate_key(self, model: str, messages: list, **kwargs) -> str:
        """Generate a unique cache key from request parameters.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc)
            
        Returns:
            MD5 hash as cache key
        """
        # Create deterministic representation
        cache_data = {
            "model": model,
            "messages": messages,
            "params": {k: v for k, v in sorted(kwargs.items())}
        }
        
        # Generate hash
        data_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(data_string.encode()).hexdigest()
    
    def get(self, model: str, messages: list, **kwargs) -> Optional[dict]:
        """Retrieve cached response if available.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Cached response or None if not found
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(model, messages, **kwargs)
        
        with self.lock:
            value = self.cache.get(key)
            if value:
                logger.info(f"Cache HIT for model={model}, key={key[:8]}...")
            else:
                logger.debug(f"Cache MISS for model={model}, key={key[:8]}...")
            return value
    
    def set(self, model: str, messages: list, response: dict, **kwargs) -> None:
        """Store response in cache.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            response: Response to cache
            **kwargs: Additional parameters
        """
        if not self.enabled:
            return
        
        key = self._generate_key(model, messages, **kwargs)
        
        with self.lock:
            self.cache[key] = response
            logger.debug(f"Cached response for model={model}, key={key[:8]}...")
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            return {
                "enabled": self.enabled,
                "current_size": len(self.cache),
                "max_size": self.cache.maxsize,
                "ttl": self.cache.ttl
            }


# Singleton instance
cache_manager = CacheManager(
    maxsize=settings.CACHE_MAX_SIZE,
    ttl=settings.CACHE_TTL
)

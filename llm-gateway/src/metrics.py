"""Simple in-memory metrics tracking system."""

import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMMetrics:
    """Store metrics for LLM requests in memory."""
    
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    requests_by_model: Dict[str, int] = field(default_factory=dict)
    tokens_by_model: Dict[str, int] = field(default_factory=dict)
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    latencies: List[float] = field(default_factory=list)
    last_reset: datetime = field(default_factory=datetime.now)
    
    def record_request(
        self, 
        model: str, 
        tokens: int, 
        cost: float, 
        latency: float, 
        cached: bool,
        error: bool = False
    ) -> None:
        """Record a completed LLM request.
        
        Args:
            model: Model name used
            tokens: Total tokens consumed
            cost: Estimated cost in USD
            latency: Response time in milliseconds
            cached: Whether response was from cache
            error: Whether request resulted in error
        """
        self.total_requests += 1
        
        if error:
            self.errors += 1
            return
        
        self.total_tokens += tokens
        self.total_cost += cost
        self.latencies.append(latency)
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        # Track by model
        self.requests_by_model[model] = self.requests_by_model.get(model, 0) + 1
        self.tokens_by_model[model] = self.tokens_by_model.get(model, 0) + tokens
        self.cost_by_model[model] = self.cost_by_model.get(model, 0.0) + cost
        
        logger.debug(
            f"Metrics recorded: model={model}, tokens={tokens}, "
            f"cost=${cost:.4f}, latency={latency:.2f}ms, cached={cached}"
        )
    
    def get_stats(self) -> dict:
        """Get current metrics statistics.
        
        Returns:
            Dictionary with all metrics
        """
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        cache_hit_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        error_rate = (self.errors / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.total_requests - self.errors,
            "errors": self.errors,
            "error_rate_percent": round(error_rate, 2),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "average_latency_ms": round(avg_latency, 2),
            "requests_by_model": self.requests_by_model,
            "tokens_by_model": self.tokens_by_model,
            "cost_by_model": {k: round(v, 4) for k, v in self.cost_by_model.items()},
            "last_reset": self.last_reset.isoformat()
        }
    
    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.requests_by_model.clear()
        self.tokens_by_model.clear()
        self.cost_by_model.clear()
        self.latencies.clear()
        self.last_reset = datetime.now()
        logger.info("Metrics reset")


class MetricsManager:
    """Thread-safe metrics manager."""
    
    def __init__(self):
        self.metrics = LLMMetrics()
        self.lock = threading.Lock()
        self.enabled = settings.METRICS_ENABLED
        logger.info(f"Metrics initialized: enabled={self.enabled}")
    
    def record(
        self, 
        model: str, 
        tokens: int, 
        cost: float, 
        latency: float, 
        cached: bool,
        error: bool = False
    ) -> None:
        """Thread-safe record of metrics."""
        if not self.enabled:
            return
        
        with self.lock:
            self.metrics.record_request(model, tokens, cost, latency, cached, error)
    
    def get_stats(self) -> dict:
        """Thread-safe retrieval of stats."""
        with self.lock:
            return self.metrics.get_stats()
    
    def reset(self) -> None:
        """Thread-safe reset of metrics."""
        with self.lock:
            self.metrics.reset()


# Singleton instance
metrics_manager = MetricsManager()

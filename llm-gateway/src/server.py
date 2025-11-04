"""FastAPI server for LLM Gateway."""

import logging
import time
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .registry import get_all_llms, get_llm
from .cache import cache_manager
from .metrics import metrics_manager

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm-gateway")


# Request/Response models
class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class GenerateRequest(BaseModel):
    """Request to generate LLM response."""
    model: str = Field(..., description="Model name to use")
    messages: List[Message] = Field(..., description="Conversation messages")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(2000, gt=0, description="Maximum tokens to generate")


class Usage(BaseModel):
    """Token usage information."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class GenerateResponse(BaseModel):
    """Response from LLM generation."""
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model that generated the response")
    usage: Usage = Field(..., description="Token usage")
    finish_reason: str = Field(..., description="Why generation stopped")
    cached: bool = Field(..., description="Whether response was cached")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("LLM Gateway starting up...")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Cache enabled: {settings.CACHE_ENABLED}")
    logger.info(f"Metrics enabled: {settings.METRICS_ENABLED}")
    logger.info(f"Available LLMs: {len(get_all_llms())}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("LLM Gateway shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="LLM Gateway",
    description="Centralized gateway for multiple LLM providers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "llm-gateway",
        "version": "1.0.0"
    }


@app.get("/mcp/llm/list")
async def list_llms():
    """List all available LLMs in MCP format.
    
    Returns:
        List of available LLM providers
    """
    try:
        llms = get_all_llms()
        logger.info(f"Listed {len(llms)} available LLMs")
        return {"llms": llms}
    except Exception as e:
        logger.error(f"Error listing LLMs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list LLMs: {str(e)}"
        )


@app.post("/mcp/llm/generate", response_model=GenerateResponse)
async def generate_response(request: GenerateRequest):
    """Generate a response from the specified LLM.
    
    Args:
        request: Generation request with model, messages, and parameters
        
    Returns:
        Generated response with metadata
    """
    start_time = time.time()
    cached = False
    
    try:
        logger.info(f"Generation request: model={request.model}, messages={len(request.messages)}")
        
        # Convert Pydantic models to dicts
        messages = [msg.model_dump() for msg in request.messages]
        
        # Check cache
        cached_response = cache_manager.get(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if cached_response:
            cached = True
            response_data = cached_response
            logger.info(f"Returning cached response for model={request.model}")
        else:
            # Get LLM instance
            llm = get_llm(request.model)
            
            # Generate response
            response_data = await llm.generate(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Cache the response
            cache_manager.set(
                model=request.model,
                messages=messages,
                response=response_data,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        usage = response_data["usage"]
        
        # Estimate cost
        llm = get_llm(request.model)
        estimated_cost = llm.estimate_cost(
            usage["input_tokens"],
            usage["output_tokens"]
        )
        
        # Record metrics
        metrics_manager.record(
            model=request.model,
            tokens=usage["total_tokens"],
            cost=estimated_cost,
            latency=latency_ms,
            cached=cached
        )
        
        # Log success
        logger.info(
            f"Generation complete: model={request.model}, "
            f"tokens={usage['total_tokens']}, cost=${estimated_cost:.4f}, "
            f"latency={latency_ms:.2f}ms, cached={cached}"
        )
        
        # Return response
        return GenerateResponse(
            content=response_data["content"],
            model=response_data["model"],
            usage=Usage(**usage),
            finish_reason=response_data["finish_reason"],
            cached=cached,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=round(estimated_cost, 6)
        )
        
    except ValueError as e:
        # Invalid model or parameters
        logger.error(f"Validation error: {str(e)}")
        metrics_manager.record(
            model=request.model,
            tokens=0,
            cost=0.0,
            latency=(time.time() - start_time) * 1000,
            cached=False,
            error=True
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected error
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        metrics_manager.record(
            model=request.model,
            tokens=0,
            cost=0.0,
            latency=(time.time() - start_time) * 1000,
            cached=False,
            error=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@app.get("/metrics")
async def get_metrics():
    """Get current metrics and statistics.
    
    Returns:
        Current metrics data
    """
    try:
        stats = metrics_manager.get_stats()
        cache_stats = cache_manager.get_stats()
        
        return {
            "metrics": stats,
            "cache": cache_stats
        }
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@app.post("/metrics/reset")
async def reset_metrics():
    """Reset all metrics to zero.
    
    Returns:
        Confirmation message
    """
    try:
        metrics_manager.reset()
        logger.info("Metrics reset via API")
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics: {str(e)}"
        )


@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached responses.
    
    Returns:
        Confirmation message
    """
    try:
        cache_manager.clear()
        logger.info("Cache cleared via API")
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

"""Main entry point for Agent FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from config import setup_logging, settings
from mcp_client import MCPClient
from graph import create_workflow
from api.routes import router, set_workflow, set_mcp_client

logger = logging.getLogger(__name__)

# Global MCP client
mcp_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown.
    """
    global mcp_client
    
    # Startup
    logger.info("Starting Agent application...")
    
    try:
        # Initialize MCP client with HTTP REST transport
        logger.info("Initializing MCP client (HTTP REST)...")
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://toolbox:8000")
        mcp_client = MCPClient(mcp_server_url)
        await mcp_client.connect()
        
        # Create workflow
        logger.info("Creating LangGraph workflow...")
        workflow = create_workflow(mcp_client)
        
        # Set workflow and client for routes
        set_workflow(workflow)
        set_mcp_client(mcp_client)
        
        logger.info("Agent application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent application...")
    
    if mcp_client:
        await mcp_client.disconnect()
    
    logger.info("Agent application shut down")


# Create FastAPI app
app = FastAPI(
    title="LangGraph Agent with MCP",
    description="Agent that uses LangGraph + LLM Gateway + MCP Server",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LangGraph Agent with MCP",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "process": "/process"
        }
    }


if __name__ == "__main__":
    setup_logging(settings.log_level)
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )

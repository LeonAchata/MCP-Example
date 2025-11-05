"""WebSocket Agent - Main application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from config import settings
from mcp_client.client import MCPClient
from graph.workflow import create_workflow
from websocket.connection import ConnectionManager
from websocket.handlers import MessageHandler

logger = logging.getLogger(__name__)

# Global instances
mcp_client = None
workflow = None
manager = ConnectionManager()
message_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global mcp_client, workflow, message_handler
    
    logger.info("🚀 Starting WebSocket Agent...")
    
    try:
        # Initialize MCP Client
        logger.info(f"Connecting to MCP Toolbox at {settings.mcp_server_url}")
        mcp_client = MCPClient(settings.mcp_server_url)
        await mcp_client.connect()
        
        # Create workflow
        workflow = create_workflow(mcp_client)
        logger.info("LangGraph workflow created")
        
        # Initialize message handler
        message_handler = MessageHandler(workflow, mcp_client, manager)
        
        logger.info("✅ WebSocket Agent started successfully")
        logger.info(f"MCP Toolbox: {settings.mcp_server_url}")
        logger.info(f"LLM Gateway: {settings.llm_gateway_url}")
        logger.info(f"Default Model: {settings.default_model}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket Agent: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down WebSocket Agent...")
        if mcp_client:
            await mcp_client.close()
        logger.info("WebSocket Agent stopped")


# Create FastAPI app
app = FastAPI(
    title="MCP WebSocket Agent",
    description="WebSocket agent with MCP toolbox integration and Bedrock",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check MCP connection
        mcp_connected = mcp_client is not None and len(mcp_client.tools) > 0
        
        # Check LLM Gateway availability
        llm_gateway_available = bool(settings.llm_gateway_url and settings.default_model)
        
        return {
            "status": "healthy",
            "service": "websocket-agent",
            "mcp_connected": mcp_connected,
            "mcp_tools": len(mcp_client.tools) if mcp_client else 0,
            "llm_gateway_available": llm_gateway_available,
            "llm_gateway_url": settings.llm_gateway_url,
            "default_model": settings.default_model,
            "active_connections": manager.get_connection_count()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "MCP WebSocket Agent",
        "version": "1.0.0",
        "websocket_endpoint": "/ws",
        "health_check": "/health",
        "active_connections": manager.get_connection_count(),
        "mcp_toolbox": settings.mcp_server_url,
        "llm_gateway": settings.llm_gateway_url,
        "default_model": settings.default_model
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent interaction.
    
    Message format (Client -> Server):
    {
        "type": "message",
        "content": "Your message here"
    }
    
    Message format (Server -> Client):
    {
        "type": "start|step|tool_call|tool_result|response|complete|error",
        "content": "...",
        "timestamp": "2024-11-03T19:00:00"
    }
    """
    connection_id = await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_message(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "message": "Conectado al WebSocket Agent",
            "mcp_tools": len(mcp_client.tools) if mcp_client else 0,
            "llm_gateway": settings.llm_gateway_url,
            "default_model": settings.default_model
        })
        
        # Message loop
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received message from {connection_id}: {data.get('type', 'unknown')}")
            
            # Handle message
            await message_handler.handle_message(connection_id, data)
    
    except WebSocketDisconnect:
        logger.info(f"Client {connection_id} disconnected normally")
        manager.disconnect(connection_id)
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection {connection_id}: {e}", exc_info=True)
        manager.disconnect(connection_id)
        
        try:
            await manager.send_message(connection_id, {
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
        except:
            pass


@app.get("/connections")
async def get_connections():
    """Get active connections count."""
    return {
        "active_connections": manager.get_connection_count(),
        "service": "websocket-agent"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )

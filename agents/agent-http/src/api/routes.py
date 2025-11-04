"""FastAPI routes for Agent API."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()

# Global workflow instance (set by main.py)
workflow = None
mcp_client = None


class ProcessRequest(BaseModel):
    """Request model for /process endpoint."""
    input: str


class ProcessResponse(BaseModel):
    """Response model for /process endpoint."""
    result: str
    steps: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    mcp_connected: bool
    bedrock_available: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    logger.debug("GET /health")
    
    mcp_connected = mcp_client is not None and mcp_client.session is not None
    bedrock_available = True  # Assume Bedrock is available if credentials are set
    
    return HealthResponse(
        status="healthy" if mcp_connected else "degraded",
        mcp_connected=mcp_connected,
        bedrock_available=bedrock_available
    )


@router.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """
    Process user input through the agent workflow.
    
    Args:
        request: User input request
        
    Returns:
        Processed response with steps
    """
    logger.info(f"POST /process | Input: {request.input}")
    
    if workflow is None:
        logger.error("Workflow not initialized")
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    if mcp_client is None or mcp_client.session is None:
        logger.error("MCP client not connected")
        raise HTTPException(status_code=503, detail="MCP client not connected")
    
    try:
        # Invoke workflow
        initial_state = {
            "user_input": request.input,
            "messages": [],
            "final_answer": None,
            "steps": []
        }
        
        result = await workflow.ainvoke(initial_state)
        
        final_answer = result.get("final_answer", "No response generated")
        steps = result.get("steps", [])
        
        logger.info(f"POST /process | Response ready with {len(steps)} steps")
        
        return ProcessResponse(
            result=final_answer,
            steps=steps
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


def set_workflow(wf):
    """Set the workflow instance."""
    global workflow
    workflow = wf


def set_mcp_client(client):
    """Set the MCP client instance."""
    global mcp_client
    mcp_client = client

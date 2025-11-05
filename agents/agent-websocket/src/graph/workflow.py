"""LangGraph workflow definition for WebSocket agent."""

import logging
from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .nodes import (
    process_input_node,
    llm_node,
    tool_execution_node,
    final_answer_node,
    route_decision
)
from config import settings
from llm_client.client import LLMGatewayClient

logger = logging.getLogger(__name__)


def create_workflow(mcp_client):
    """
    Create and compile LangGraph workflow.
    
    Args:
        mcp_client: MCP client instance
        
    Returns:
        Compiled workflow
    """
    logger.info("Creating LangGraph workflow for WebSocket agent...")
    
    # Initialize LLM Gateway client
    llm_client = LLMGatewayClient(
        gateway_url=settings.llm_gateway_url,
        default_model=settings.default_model
    )
    
    logger.info(f"LLM Gateway client initialized: url={settings.llm_gateway_url}, model={settings.default_model}")
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Create wrapper for tool_execution that binds mcp_client
    async def tool_exec_wrapper(state):
        return await tool_execution_node(state, mcp_client)
    
    # Add nodes
    graph.add_node("process_input", process_input_node)
    graph.add_node("llm", lambda state: llm_node(state, llm_client, mcp_client))
    graph.add_node("tool_execution", tool_exec_wrapper)
    graph.add_node("final_answer", final_answer_node)
    
    # Add edges
    graph.add_edge(START, "process_input")
    graph.add_edge("process_input", "llm")
    
    # Conditional edge from LLM
    graph.add_conditional_edges(
        "llm",
        route_decision,
        {
            "tools": "tool_execution",
            "final": "final_answer"
        }
    )
    
    # Edge from tool execution back to LLM
    graph.add_edge("tool_execution", "llm")
    
    # Edge from final answer to end
    graph.add_edge("final_answer", END)
    
    # Compile workflow
    workflow = graph.compile()
    
    logger.info("LangGraph workflow compiled successfully")
    
    return workflow

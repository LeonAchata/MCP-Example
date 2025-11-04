"""LangGraph workflow definition."""

import logging
from langgraph.graph import StateGraph, START, END
from langchain_aws import ChatBedrock

from .state import AgentState
from .nodes import (
    process_input_node,
    llm_node,
    tool_execution_node,
    final_answer_node,
    route_decision
)
from config import settings

logger = logging.getLogger(__name__)


def create_workflow(mcp_client):
    """
    Create and compile LangGraph workflow.
    
    Args:
        mcp_client: MCP client instance
        
    Returns:
        Compiled workflow
    """
    logger.info("Creating LangGraph workflow...")
    
    # Initialize Bedrock LLM
    llm = ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        model_kwargs={
            "temperature": 0.0,
            "max_tokens": 2000
        }
    )
    
    logger.info(f"Bedrock client initialized with model: {settings.bedrock_model_id}")
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Create wrapper for tool_execution that binds mcp_client
    async def tool_exec_wrapper(state):
        return await tool_execution_node(state, mcp_client)
    
    # Add nodes
    graph.add_node("process_input", process_input_node)
    graph.add_node("llm", lambda state: llm_node(state, llm, mcp_client))
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

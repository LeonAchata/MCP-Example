"""Workflow nodes for WebSocket agent."""

import logging
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)


def process_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process initial user input.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    user_input = state.get("user_input", "")
    logger.info(f"Node: process_input | Processing: {user_input}")
    
    # Create initial human message
    human_message = HumanMessage(content=user_input)
    
    # Add step
    steps = state.get("steps", [])
    steps.append({
        "node": "process_input",
        "timestamp": datetime.now().isoformat(),
        "input": user_input
    })
    
    return {
        "messages": [human_message],
        "steps": steps
    }


def llm_node(state: Dict[str, Any], llm, mcp_client) -> Dict[str, Any]:
    """
    Call LLM (Bedrock) with tools.
    
    Args:
        state: Current agent state
        llm: Bedrock LLM instance
        mcp_client: MCP client for tools
        
    Returns:
        Updated state
    """
    logger.info("Node: llm | Calling Bedrock with MCP tools")
    
    messages = state.get("messages", [])
    steps = state.get("steps", [])
    
    # Get tools from MCP
    tools = mcp_client.get_tools_for_bedrock()
    tool_names = [t.get('name', 'unknown') if isinstance(t, dict) else str(t) for t in tools]
    logger.info(f"Node: llm | Available tools: {tool_names}")
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Call LLM
    response = llm_with_tools.invoke(messages)
    
    # Log response
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"Node: llm | Bedrock requested {len(response.tool_calls)} tool calls")
        for tc in response.tool_calls:
            logger.info(f"Node: llm | Tool call: {tc.get('name')} with args {tc.get('args')}")
    else:
        logger.info(f"Node: llm | Bedrock response: Final answer ready")
    
    # Add step
    steps.append({
        "node": "llm",
        "timestamp": datetime.now().isoformat(),
        "has_tool_calls": bool(hasattr(response, 'tool_calls') and response.tool_calls)
    })
    
    return {
        "messages": [response],
        "steps": steps
    }


async def tool_execution_node(state: Dict[str, Any], mcp_client) -> Dict[str, Any]:
    """
    Execute tools requested by LLM via MCP.
    
    Args:
        state: Current agent state
        mcp_client: MCP client for tools
        
    Returns:
        Updated state
    """
    logger.info("Node: tool_execution | Executing tools via MCP")
    
    messages = state.get("messages", [])
    steps = state.get("steps", [])
    
    # Get last AI message with tool calls
    last_message = messages[-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        logger.warning("Node: tool_execution | No tool calls found")
        return {"steps": steps}
    
    tool_calls = last_message.tool_calls
    tool_messages = []
    executed_tools = []
    
    logger.info(f"Node: tool_execution | Executing {len(tool_calls)} tools via MCP")
    
    # Execute each tool
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id")
        
        try:
            # Call tool via MCP
            result = await mcp_client.call_tool(tool_name, tool_args)
            
            # Create tool message (sin status para compatibilidad con Bedrock)
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
            
            executed_tools.append({
                "name": tool_name,
                "args": tool_args,
                "result": result
            })
            
            logger.info(f"Node: tool_execution | Tool {tool_name} executed successfully")
        
        except Exception as e:
            logger.error(f"Node: tool_execution | Error executing {tool_name}: {e}")
            
            # Create error message (sin status)
            tool_message = ToolMessage(
                content=f"Error: {str(e)}",
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
            
            executed_tools.append({
                "name": tool_name,
                "args": tool_args,
                "error": str(e)
            })
    
    # Add step
    steps.append({
        "node": "tool_execution",
        "timestamp": datetime.now().isoformat(),
        "tools": executed_tools
    })
    
    return {
        "messages": tool_messages,
        "steps": steps
    }


def final_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract final answer from messages.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Node: final_answer | Extracting final response")
    
    messages = state.get("messages", [])
    steps = state.get("steps", [])
    
    # Get last AI message
    final_answer = None
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            final_answer = message.content
            break
    
    if not final_answer:
        final_answer = "No pude generar una respuesta."
        logger.warning("Node: final_answer | No AI message found")
    else:
        logger.info(f"Node: final_answer | Final answer: {final_answer[:100]}...")
    
    # Add step
    steps.append({
        "node": "final_answer",
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "final_answer": final_answer,
        "steps": steps
    }


def route_decision(state: Dict[str, Any]) -> str:
    """
    Route based on whether LLM wants to use tools.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info("Router: Routing to tool_execution")
        return "tools"
    else:
        logger.info("Router: Routing to final_answer")
        return "final"

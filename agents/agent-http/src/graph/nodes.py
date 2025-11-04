"""Graph nodes for LangGraph workflow."""

import logging
import json
from datetime import datetime
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)


def process_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user input and initialize state.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info(f"Node: process_input | Initializing state")
    
    user_input = state.get("user_input", "")
    
    # Add user message to history
    messages = [HumanMessage(content=user_input)]
    
    # Add step for tracking
    steps = state.get("steps", [])
    steps.append({
        "node": "process_input",
        "timestamp": datetime.now().isoformat(),
        "input": user_input
    })
    
    logger.info(f"Node: process_input | User input: {user_input}")
    
    return {
        "messages": messages,
        "steps": steps
    }


def llm_node(state: Dict[str, Any], llm, mcp_client) -> Dict[str, Any]:
    """
    Call Bedrock LLM to process messages and decide next action.
    
    Args:
        state: Current agent state
        llm: Bedrock LLM instance
        mcp_client: MCP client for tools
        
    Returns:
        Updated state
    """
    logger.info("Node: llm | Calling Bedrock Claude 3.5")
    
    messages = state.get("messages", [])
    steps = state.get("steps", [])
    
    # Get tools from MCP in Bedrock format
    tools = mcp_client.get_tools_for_bedrock()
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Call LLM
    response = llm_with_tools.invoke(messages)
    
    # Log response
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_names = [tc.get('name', 'unknown') for tc in response.tool_calls]
        logger.info(f"Node: llm | Bedrock response: Tool calls requested {tool_names}")
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
            
            # Create tool message
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
            
        except Exception as e:
            logger.error(f"Node: tool_execution | Error executing {tool_name}: {str(e)}")
            # Create error tool message
            tool_message = ToolMessage(
                content=f"Error: {str(e)}",
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
    
    logger.info(f"Node: tool_execution | Tool execution completed")
    
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
    Extract and format final answer.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Node: final_answer | Formatting response")
    
    messages = state.get("messages", [])
    steps = state.get("steps", [])
    
    # Get last AI message
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage):
        final_answer = last_message.content
    else:
        final_answer = str(last_message)
    
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
    Decide next node based on LLM response.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    messages = state.get("messages", [])
    last_message = messages[-1]
    
    # If there are tool calls, go to tool execution
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.debug("Route decision: tools")
        return "tools"
    
    # Otherwise, go to final answer
    logger.debug("Route decision: final")
    return "final"

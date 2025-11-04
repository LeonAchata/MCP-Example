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


def llm_node(state: Dict[str, Any], llm_client, mcp_client) -> Dict[str, Any]:
    """
    Call LLM Gateway to process messages and decide next action.
    
    Args:
        state: Current agent state
        llm_client: LLM Gateway client
        mcp_client: MCP client for tools
        
    Returns:
        Updated state
    """
    logger.info("Node: llm | Calling LLM via Gateway")
    
    messages = state.get("messages", [])
    steps = state.get("steps", [])
    
    # Get tools from MCP in standard format
    tools = mcp_client.get_tools_for_bedrock()
    
    # Create system message with tool information
    tool_descriptions = []
    for tool in tools:
        tool_info = f"- {tool['name']}: {tool.get('description', 'No description')}"
        if 'inputSchema' in tool:
            tool_info += f"\n  Parameters: {json.dumps(tool['inputSchema'].get('properties', {}))}"
        tool_descriptions.append(tool_info)
    
    system_prompt = f"""You are a helpful AI assistant with access to the following tools:

{chr(10).join(tool_descriptions)}

When you need to use a tool, respond with a tool call in this exact format:
TOOL_CALL: tool_name
ARGUMENTS: {{"arg1": "value1", "arg2": "value2"}}

If you don't need any tools, just respond normally to help the user."""
    
    # Prepare messages for LLM with system prompt
    llm_messages = [HumanMessage(content=system_prompt)] + messages
    
    # Call LLM via Gateway (synchronous call in async context handled by workflow)
    import asyncio
    response = asyncio.run(llm_client.generate(
        messages=llm_messages,
        temperature=0.7,
        max_tokens=2000
    ))
    
    # Check if response contains tool calls
    response_text = response.content
    has_tool_call = "TOOL_CALL:" in response_text
    
    if has_tool_call:
        # Parse tool call from response
        try:
            lines = response_text.strip().split('\n')
            tool_name = None
            tool_args = {}
            
            for line in lines:
                if line.startswith("TOOL_CALL:"):
                    tool_name = line.replace("TOOL_CALL:", "").strip()
                elif line.startswith("ARGUMENTS:"):
                    args_str = line.replace("ARGUMENTS:", "").strip()
                    tool_args = json.loads(args_str)
            
            if tool_name:
                # Add tool call info to response
                response.additional_kwargs["tool_calls"] = [{
                    "name": tool_name,
                    "args": tool_args,
                    "id": f"call_{datetime.now().timestamp()}"
                }]
                # Store as attribute for compatibility
                response.tool_calls = response.additional_kwargs["tool_calls"]
                logger.info(f"Node: llm | Parsed tool call: {tool_name}")
        except Exception as e:
            logger.error(f"Node: llm | Error parsing tool call: {str(e)}")
            has_tool_call = False
    
    logger.info(f"Node: llm | Response received: has_tool_calls={has_tool_call}")
    
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

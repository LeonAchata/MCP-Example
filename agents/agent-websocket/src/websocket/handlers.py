"""WebSocket message handlers."""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handle WebSocket messages and workflow execution."""
    
    def __init__(self, workflow, mcp_client, connection_manager):
        """
        Initialize message handler.
        
        Args:
            workflow: LangGraph workflow
            mcp_client: MCP client instance
            connection_manager: WebSocket connection manager
        """
        self.workflow = workflow
        self.mcp_client = mcp_client
        self.manager = connection_manager
        logger.info("MessageHandler initialized")
    
    async def handle_message(self, connection_id: str, data: Dict[str, Any]):
        """
        Handle incoming WebSocket message.
        
        Args:
            connection_id: Connection ID
            data: Message data
        """
        try:
            message_type = data.get("type", "message")
            
            if message_type == "message":
                await self._handle_user_message(connection_id, data)
            elif message_type == "ping":
                await self._handle_ping(connection_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.manager.send_message(connection_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self.manager.send_message(connection_id, {
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            })
    
    async def _handle_user_message(self, connection_id: str, data: Dict[str, Any]):
        """
        Process user message through the agent workflow.
        
        Args:
            connection_id: Connection ID
            data: Message data
        """
        user_input = data.get("content", "")
        
        if not user_input:
            await self.manager.send_message(connection_id, {
                "type": "error",
                "message": "Empty message content"
            })
            return
        
        logger.info(f"Processing message from {connection_id}: {user_input}")
        
        # Send start notification
        await self.manager.send_message(connection_id, {
            "type": "start",
            "message": "Procesando tu solicitud...",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Create initial state
            initial_state = {
                "messages": [],
                "user_input": user_input,
                "steps": [],
                "final_answer": None
            }
            
            # Stream workflow execution
            step_count = 0
            async for chunk in self.workflow.astream(initial_state):
                step_count += 1
                await self._process_workflow_chunk(connection_id, chunk, step_count)
            
            # Get final result
            final_result = await self.workflow.ainvoke(initial_state)
            final_answer = final_result.get("final_answer", "No response generated")
            
            # Send final response
            await self.manager.send_message(connection_id, {
                "type": "response",
                "content": final_answer,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send completion
            await self.manager.send_message(connection_id, {
                "type": "complete",
                "steps": len(final_result.get("steps", [])),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Message processing completed for {connection_id}")
        
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}", exc_info=True)
            await self.manager.send_message(connection_id, {
                "type": "error",
                "message": f"Error processing request: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _process_workflow_chunk(self, connection_id: str, chunk: Dict[str, Any], step_num: int):
        """
        Process a chunk from the workflow stream.
        
        Args:
            connection_id: Connection ID
            chunk: Workflow chunk
            step_num: Step number
        """
        # Extract node name from chunk
        for node_name, node_data in chunk.items():
            logger.debug(f"Workflow step {step_num}: {node_name}")
            
            # Send step notification
            await self.manager.send_message(connection_id, {
                "type": "step",
                "node": node_name,
                "step_number": step_num,
                "message": self._get_node_message(node_name),
                "timestamp": datetime.now().isoformat()
            })
            
            # Check for tool calls
            if node_name == "tool_execution" and isinstance(node_data, dict):
                steps = node_data.get("steps", [])
                for step in steps:
                    if step.get("node") == "tool_execution" and "tools" in step:
                        for tool_info in step["tools"]:
                            # Send tool call notification
                            await self.manager.send_message(connection_id, {
                                "type": "tool_call",
                                "tool": tool_info["name"],
                                "args": tool_info["args"],
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Send tool result
                            await self.manager.send_message(connection_id, {
                                "type": "tool_result",
                                "tool": tool_info["name"],
                                "result": tool_info["result"],
                                "timestamp": datetime.now().isoformat()
                            })
    
    def _get_node_message(self, node_name: str) -> str:
        """
        Get user-friendly message for a node.
        
        Args:
            node_name: Node name
            
        Returns:
            User-friendly message
        """
        messages = {
            "process_input": "Procesando entrada...",
            "llm": "Consultando a Bedrock...",
            "tool_execution": "Ejecutando herramientas via MCP...",
            "final_answer": "Generando respuesta final..."
        }
        return messages.get(node_name, f"Ejecutando {node_name}...")
    
    async def _handle_ping(self, connection_id: str):
        """
        Handle ping message.
        
        Args:
            connection_id: Connection ID
        """
        await self.manager.send_message(connection_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })

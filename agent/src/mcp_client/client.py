"""MCP Client implementation (renamed module)."""

import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client for connecting to MCP server."""
    
    def __init__(self, server_command: List[str]):
        """
        Initialize MCP client.
        
        Args:
            server_command: Command to start MCP server (for stdio transport)
        """
        self.server_command = server_command
        self.session: Optional[ClientSession] = None
        self.tools: Dict[str, Any] = {}
        self._client_context = None
        self._read_stream = None
        self._write_stream = None
        
    async def connect(self):
        """Connect to MCP server and discover tools."""
        try:
            logger.info(f"Connecting to MCP server with command: {' '.join(self.server_command)}")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:],
                env=None
            )
            
            # Connect to server
            self._client_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._client_context.__aenter__()
            
            # Create session
            self.session = ClientSession(self._read_stream, self._write_stream)
            await self.session.__aenter__()
            
            # Initialize session
            await self.session.initialize()
            
            logger.info("Connected to MCP server successfully")
            
            # Discover tools
            await self.discover_tools()
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise
    
    async def discover_tools(self):
        """Discover available tools from MCP server."""
        try:
            logger.info("Discovering tools from MCP server...")
            
            tools_response = await self.session.list_tools()
            
            for tool in tools_response.tools:
                self.tools[tool.name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
            
            tool_names = list(self.tools.keys())
            logger.info(f"Discovered {len(tool_names)} tools from MCP server: {', '.join(tool_names)}")
            
        except Exception as e:
            logger.error(f"Failed to discover tools: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            logger.info(f"MCP call: {tool_name}({arguments})")
            
            if tool_name not in self.tools:
                raise ValueError(f"Tool {tool_name} not found. Available tools: {list(self.tools.keys())}")
            
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract text content from result
            if result.content and len(result.content) > 0:
                response = result.content[0].text
                logger.info(f"MCP response: {response}")
                return response
            else:
                logger.warning(f"No content in MCP response for tool {tool_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self._client_context:
                await self._client_context.__aexit__(None, None, None)
            logger.info("Disconnected from MCP server")
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {str(e)}")
    
    def get_tools_for_bedrock(self) -> List[Dict[str, Any]]:
        """
        Get tools formatted for Bedrock function calling.
        
        Returns:
            List of tools in Bedrock format
        """
        bedrock_tools = []
        
        for tool_name, tool_info in self.tools.items():
            bedrock_tool = {
                "toolSpec": {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "inputSchema": {
                        "json": tool_info["input_schema"]
                    }
                }
            }
            bedrock_tools.append(bedrock_tool)
        
        return bedrock_tools

"""MCP Client - HTTP REST Implementation.

This client connects to an MCP Toolbox Server via HTTP REST,
following the MCP protocol structure and semantics.
"""

import logging
from typing import Any, Dict, List
import httpx

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client for connecting to MCP Toolbox via HTTP REST."""
    
    def __init__(self, toolbox_url: str, timeout: float = 30.0):
        """
        Initialize MCP client.
        
        Args:
            toolbox_url: Base URL of the MCP Toolbox Server
                        (e.g., http://toolbox:8000 in Docker,
                         http://toolbox-service.namespace.svc.cluster.local in K8s)
            timeout: Request timeout in seconds
        """
        self.toolbox_url = toolbox_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.tools: Dict[str, Any] = {}
        self.session = self  # For compatibility with existing code
        
        logger.info(f"MCP Client initialized - Toolbox URL: {self.toolbox_url}")
    
    async def connect(self):
        """
        Connect to MCP Toolbox and discover tools.
        
        This method establishes connection to the toolbox server
        and retrieves available tools following MCP protocol.
        """
        try:
            logger.info(f"Connecting to MCP Toolbox at {self.toolbox_url}")
            
            # Test connection
            response = await self.client.get(f"{self.toolbox_url}/health")
            response.raise_for_status()
            health_data = response.json()
            
            logger.info(f"Connected to {health_data.get('service', 'MCP Toolbox')}")
            logger.info(f"Protocol: {health_data.get('protocol', 'MCP over HTTP')}")
            
            # Discover tools
            await self.discover_tools()
            
            logger.info("MCP Client connected successfully")
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to connect to MCP Toolbox: {str(e)}")
            raise ConnectionError(f"Cannot connect to MCP Toolbox at {self.toolbox_url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during connection: {str(e)}")
            raise
    
    async def discover_tools(self):
        """
        Discover available tools from MCP Toolbox.
        
        Follows MCP protocol's tools/list specification.
        """
        try:
            logger.info("Discovering tools from MCP Toolbox...")
            
            # Call MCP tools/list endpoint
            response = await self.client.post(f"{self.toolbox_url}/mcp/tools/list")
            response.raise_for_status()
            
            tools_data = response.json()
            tools_list = tools_data.get("tools", [])
            
            # Store tools in MCP format
            for tool in tools_list:
                self.tools[tool["name"]] = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool.get("inputSchema", {})
                }
            
            tool_names = list(self.tools.keys())
            logger.info(f"Discovered {len(tool_names)} tools: {', '.join(tool_names)}")
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to discover tools: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error parsing tools response: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP Toolbox.
        
        Follows MCP protocol's tools/call specification.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict
            
        Returns:
            Tool execution result (string)
        """
        try:
            logger.info(f"MCP call: {tool_name}({arguments})")
            
            # Validate tool exists
            if tool_name not in self.tools:
                available = list(self.tools.keys())
                raise ValueError(
                    f"Tool '{tool_name}' not found. Available tools: {available}"
                )
            
            # Call MCP tools/call endpoint
            response = await self.client.post(
                f"{self.toolbox_url}/mcp/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            response.raise_for_status()
            
            # Parse MCP response
            result_data = response.json()
            content = result_data.get("content", [])
            
            if not content:
                logger.warning(f"Tool {tool_name} returned no content")
                return None
            
            # Extract text from first content item (MCP format)
            result_text = content[0].get("text", "")
            
            logger.info(f"MCP response: {result_text}")
            return result_text
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling tool {tool_name}: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Network error calling tool {tool_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from MCP Toolbox and cleanup resources."""
        try:
            logger.info("Disconnecting from MCP Toolbox...")
            await self.client.aclose()
            logger.info("MCP Client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
    
    def get_tools_for_bedrock(self) -> List[Dict[str, Any]]:
        """
        Get tools formatted for Amazon Bedrock function calling.
        
        Converts MCP tool schemas to Bedrock's expected format.
        
        Returns:
            List of tools in Bedrock format
        """
        bedrock_tools = []
        
        for tool_name, tool_info in self.tools.items():
            bedrock_tool = {
                "name": tool_name,
                "description": tool_info["description"],
                "input_schema": tool_info["input_schema"]
            }
            bedrock_tools.append(bedrock_tool)
        
        logger.debug(f"Converted {len(bedrock_tools)} tools to Bedrock format")
        return bedrock_tools
    
    def get_tools_description(self) -> List[Dict[str, Any]]:
        """
        Get tools description for LangChain.
        
        Returns:
            List of tool descriptions
        """
        tools_desc = []
        for name, info in self.tools.items():
            tools_desc.append({
                "name": name,
                "description": info["description"],
                "input_schema": info["input_schema"]
            })
        return tools_desc
    
    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.info("MCP Client closed")

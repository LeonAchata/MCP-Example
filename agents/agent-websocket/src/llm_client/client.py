"""LLM Gateway client using MCP protocol over HTTP."""

import logging
import httpx
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

logger = logging.getLogger(__name__)


class LLMGatewayClient:
    """Client for communicating with LLM Gateway using MCP protocol."""
    
    def __init__(self, gateway_url: str, default_model: str = "bedrock-nova-pro"):
        """Initialize LLM Gateway client.
        
        Args:
            gateway_url: Base URL of the LLM Gateway (e.g., http://llm-gateway:8003)
            default_model: Default model to use if not specified
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.default_model = default_model
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for LLM calls
        logger.info(f"LLM Gateway client initialized: url={gateway_url}, model={default_model}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available LLM models.
        
        Returns:
            List of available models with their metadata
            
        Raises:
            Exception: If the request fails
        """
        try:
            url = f"{self.gateway_url}/mcp/llm/list"
            logger.debug(f"Listing models from: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            models = data.get("llms", [])
            
            logger.info(f"Retrieved {len(models)} available models")
            return models
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing models: {str(e)}")
            raise Exception(f"Failed to list models: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error listing models: {str(e)}")
            raise
    
    def _convert_langchain_messages_to_mcp(
        self, 
        messages: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        """Convert LangChain messages to MCP format.
        
        Args:
            messages: List of LangChain message objects
            
        Returns:
            List of message dictionaries in MCP format
        """
        mcp_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                # Default to user for unknown types
                role = "user"
            
            mcp_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return mcp_messages
    
    def _convert_mcp_response_to_langchain(self, response_data: Dict[str, Any]) -> AIMessage:
        """Convert MCP response to LangChain AIMessage.
        
        Args:
            response_data: Response from LLM Gateway
            
        Returns:
            AIMessage object
        """
        content = response_data.get("content", "")
        
        # Add metadata
        additional_kwargs = {
            "model": response_data.get("model"),
            "finish_reason": response_data.get("finish_reason"),
            "cached": response_data.get("cached", False),
            "latency_ms": response_data.get("latency_ms"),
            "estimated_cost_usd": response_data.get("estimated_cost_usd")
        }
        
        # Add usage information
        usage = response_data.get("usage", {})
        if usage:
            additional_kwargs["usage"] = usage
        
        return AIMessage(
            content=content,
            additional_kwargs=additional_kwargs
        )
    
    async def generate(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIMessage:
        """Generate a response from the LLM.
        
        Args:
            messages: List of LangChain message objects
            model: Model to use (if None, uses default_model)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            AIMessage with the generated response
            
        Raises:
            Exception: If generation fails
        """
        model_to_use = model or self.default_model
        
        try:
            # Convert messages to MCP format
            mcp_messages = self._convert_langchain_messages_to_mcp(messages)
            
            # Prepare request
            url = f"{self.gateway_url}/mcp/llm/generate"
            payload = {
                "model": model_to_use,
                "messages": mcp_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            logger.info(
                f"Generating response: model={model_to_use}, "
                f"messages={len(mcp_messages)}, temp={temperature}"
            )
            logger.debug(f"Request payload: {payload}")
            
            # Make request
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            logger.info(
                f"Generation complete: model={response_data.get('model')}, "
                f"tokens={response_data.get('usage', {}).get('total_tokens')}, "
                f"cached={response_data.get('cached')}, "
                f"latency={response_data.get('latency_ms')}ms"
            )
            
            # Convert to LangChain message
            return self._convert_mcp_response_to_langchain(response_data)
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(f"HTTP error generating response: {e.response.status_code} - {error_detail}")
            raise Exception(f"LLM Gateway error ({e.response.status_code}): {error_detail}")
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error generating response: {str(e)}", exc_info=True)
            raise
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from LLM Gateway.
        
        Returns:
            Metrics data
        """
        try:
            url = f"{self.gateway_url}/metrics"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise

"""Base abstract class for all LLM implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """Abstract base class for LLM providers.
    
    All LLM implementations must inherit from this class and implement
    the required methods.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name/identifier for this LLM.
        
        Returns:
            String identifier (e.g., 'bedrock-nova-pro', 'gpt-4o')
        """
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name.
        
        Returns:
            Provider name (e.g., 'aws', 'openai', 'google')
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of this LLM.
        
        Returns:
            Description string
        """
        pass
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary with standardized response:
            {
                "content": str,          # Generated text
                "usage": {
                    "input_tokens": int,
                    "output_tokens": int,
                    "total_tokens": int
                },
                "finish_reason": str,    # 'stop', 'length', etc
                "model": str             # Model used
            }
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost of a request in USD.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert LLM info to MCP-compatible schema.
        
        Returns:
            Dictionary with LLM metadata
        """
        return {
            "name": self.name,
            "provider": self.provider,
            "description": self.description,
            "capabilities": ["chat", "text-generation"]
        }
    
    def validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """Validate message format.
        
        Args:
            messages: List of message dictionaries
            
        Raises:
            ValueError: If messages format is invalid
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        valid_roles = {"system", "user", "assistant"}
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"Message {i} must be a dictionary")
            
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"Message {i} must have 'role' and 'content' keys")
            
            if msg["role"] not in valid_roles:
                raise ValueError(
                    f"Message {i} has invalid role '{msg['role']}'. "
                    f"Must be one of: {valid_roles}"
                )
            
            if not isinstance(msg["content"], str):
                raise ValueError(f"Message {i} content must be a string")

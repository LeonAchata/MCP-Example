"""OpenAI LLM implementation."""

import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from openai import OpenAIError

from .base import BaseLLM
from ..config import settings

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI GPT-4o implementation."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        
        self.model_name = settings.OPENAI_DEFAULT_MODEL
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORG_ID
        )
        
        logger.info(f"OpenAI client initialized: model={self.model_name}")
    
    @property
    def name(self) -> str:
        return "gpt-4o"
    
    @property
    def provider(self) -> str:
        return "openai"
    
    @property
    def description(self) -> str:
        return "OpenAI GPT-4o - Advanced language model with multimodal capabilities"
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using OpenAI.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Standardized response dictionary
        """
        self.validate_messages(messages)
        
        try:
            logger.info(f"Calling OpenAI: model={self.model_name}, messages={len(messages)}")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract response
            choice = response.choices[0]
            content = choice.message.content
            finish_reason = choice.finish_reason
            
            # Extract usage
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            logger.info(
                f"OpenAI response: tokens={total_tokens}, "
                f"finish_reason={finish_reason}"
            )
            
            return {
                "content": content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                },
                "finish_reason": finish_reason,
                "model": response.model
            }
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {str(e)}")
            raise
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for GPT-4o.
        
        Pricing (as of 2024):
        - Input: $0.005 per 1K tokens
        - Output: $0.015 per 1K tokens
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * 0.005
        output_cost = (output_tokens / 1000) * 0.015
        return input_cost + output_cost

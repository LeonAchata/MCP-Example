"""Google Gemini LLM implementation."""

import logging
from typing import List, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import BaseLLM
from ..config import settings

logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """Google Gemini Pro implementation."""
    
    def __init__(self):
        """Initialize Gemini client."""
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider")
        
        self.model_name = settings.GEMINI_DEFAULT_MODEL
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Gemini client initialized: model={self.model_name}")
    
    @property
    def name(self) -> str:
        return "gemini-pro"
    
    @property
    def provider(self) -> str:
        return "google"
    
    @property
    def description(self) -> str:
        return "Google Gemini Pro - Advanced multimodal AI model"
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert standard messages to Gemini format.
        
        Args:
            messages: Standard message format
            
        Returns:
            Tuple of (system_instruction, history, last_message)
        """
        system_instruction = None
        history = []
        
        for msg in messages[:-1]:  # All except last
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
        
        # Last message should be from user
        last_message = messages[-1]["content"] if messages else ""
        
        return system_instruction, history, last_message
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using Gemini.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Standardized response dictionary
        """
        self.validate_messages(messages)
        
        # Convert to Gemini format
        system_instruction, history, last_message = self._convert_messages_to_gemini_format(messages)
        
        try:
            logger.info(f"Calling Gemini: model={self.model_name}, messages={len(messages)}")
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Safety settings (permissive for development)
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Start chat with history
            chat = self.model.start_chat(history=history)
            
            # Send message
            response = chat.send_message(
                last_message,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Extract response
            content = response.text
            
            # Gemini doesn't provide detailed token counts in the same way
            # We'll estimate based on character count (rough approximation)
            input_tokens = sum(len(msg["content"]) for msg in messages) // 4
            output_tokens = len(content) // 4
            total_tokens = input_tokens + output_tokens
            
            # Get finish reason
            finish_reason = "stop"  # Gemini uses different system
            if response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason)
            
            logger.info(
                f"Gemini response: estimated_tokens={total_tokens}, "
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
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Gemini error: {str(e)}")
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Gemini Pro.
        
        Pricing (as of 2024):
        - Input: $0.00025 per 1K tokens
        - Output: $0.0005 per 1K tokens
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * 0.00025
        output_cost = (output_tokens / 1000) * 0.0005
        return input_cost + output_cost

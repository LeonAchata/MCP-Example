"""AWS Bedrock LLM implementation."""

import json
import logging
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError

from .base import BaseLLM
from ..config import settings

logger = logging.getLogger(__name__)


class BedrockLLM(BaseLLM):
    """AWS Bedrock Nova Pro implementation."""
    
    def __init__(self):
        """Initialize Bedrock client."""
        self.model_id = settings.BEDROCK_MODEL_ID
        self.region = settings.AWS_REGION
        
        # Initialize boto3 client
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Bedrock client initialized: model={self.model_id}, region={self.region}")
    
    @property
    def name(self) -> str:
        return "bedrock-nova-pro"
    
    @property
    def provider(self) -> str:
        return "aws"
    
    @property
    def description(self) -> str:
        return "AWS Bedrock Nova Pro - Advanced multimodal AI model"
    
    def _convert_messages_to_bedrock_format(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert standard messages to Bedrock format.
        
        Args:
            messages: Standard message format
            
        Returns:
            Tuple of (system_prompt, conversation_messages)
        """
        system_prompt = None
        conversation = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                conversation.append({"role": "user", "content": [{"text": content}]})
            elif role == "assistant":
                conversation.append({"role": "assistant", "content": [{"text": content}]})
        
        return system_prompt, conversation
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using Bedrock.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Standardized response dictionary
        """
        self.validate_messages(messages)
        
        # Convert to Bedrock format
        system_prompt, conversation = self._convert_messages_to_bedrock_format(messages)
        
        # Prepare request body
        body = {
            "messages": conversation,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": max_tokens
            }
        }
        
        if system_prompt:
            body["system"] = [{"text": system_prompt}]
        
        try:
            # Call Bedrock API
            logger.info(f"Calling Bedrock: model={self.model_id}, messages={len(conversation)}")
            
            response = self.client.converse(
                modelId=self.model_id,
                messages=conversation,
                system=[{"text": system_prompt}] if system_prompt else None,
                inferenceConfig={
                    "temperature": temperature,
                    "maxTokens": max_tokens
                }
            )
            
            # Extract response
            output_message = response["output"]["message"]
            content = output_message["content"][0]["text"]
            
            # Extract usage
            usage = response.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            total_tokens = usage.get("totalTokens", input_tokens + output_tokens)
            
            # Get finish reason
            finish_reason = response.get("stopReason", "stop")
            
            logger.info(
                f"Bedrock response: tokens={total_tokens}, "
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
                "model": self.model_id
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Bedrock API error: {error_code} - {error_message}")
            raise Exception(f"Bedrock error: {error_code} - {error_message}")
        
        except Exception as e:
            logger.error(f"Unexpected error calling Bedrock: {str(e)}")
            raise
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Bedrock Nova Pro.
        
        Pricing (as of 2024):
        - Input: $0.0008 per 1K tokens
        - Output: $0.0032 per 1K tokens
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * 0.0008
        output_cost = (output_tokens / 1000) * 0.0032
        return input_cost + output_cost

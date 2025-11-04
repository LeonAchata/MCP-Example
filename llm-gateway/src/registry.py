"""LLM Registry - Central registry for all LLM providers."""

import logging
from typing import Dict, Type, List, Optional

from .models.base import BaseLLM
from .models.bedrock import BedrockLLM
from .models.openai import OpenAILLM
from .models.gemini import GeminiLLM

logger = logging.getLogger(__name__)

# Global LLM registry mapping model names to their classes
LLM_REGISTRY: Dict[str, Type[BaseLLM]] = {
    "bedrock-nova-pro": BedrockLLM,
    "gpt-4o": OpenAILLM,
    "gemini-pro": GeminiLLM,
}


def get_all_llms() -> List[Dict]:
    """Get all available LLMs in MCP format.
    
    Returns:
        List of LLM schemas
    """
    llms = []
    for llm_name, llm_class in LLM_REGISTRY.items():
        try:
            llm_instance = llm_class()
            llms.append(llm_instance.to_mcp_schema())
        except Exception as e:
            logger.warning(f"Could not initialize LLM '{llm_name}': {str(e)}")
            # Skip LLMs that fail to initialize (e.g., missing credentials)
            continue
    
    logger.info(f"Retrieved {len(llms)} available LLMs from registry")
    return llms


def get_llm(name: str) -> BaseLLM:
    """Get an LLM instance by name.
    
    Args:
        name: The name of the LLM to retrieve
        
    Returns:
        An instance of the requested LLM
        
    Raises:
        ValueError: If the LLM is not found in the registry
    """
    if name not in LLM_REGISTRY:
        available = ", ".join(LLM_REGISTRY.keys())
        raise ValueError(f"LLM '{name}' not found. Available LLMs: {available}")
    
    llm_class = LLM_REGISTRY[name]
    try:
        return llm_class()
    except Exception as e:
        logger.error(f"Failed to initialize LLM '{name}': {str(e)}")
        raise ValueError(f"Could not initialize LLM '{name}': {str(e)}")


def register_llm(name: str, llm_class: Type[BaseLLM]) -> None:
    """Register a new LLM in the registry.
    
    Args:
        name: The name to register the LLM under
        llm_class: The LLM class to register
        
    Raises:
        ValueError: If an LLM with the same name already exists
    """
    if name in LLM_REGISTRY:
        raise ValueError(f"LLM '{name}' is already registered")
    
    LLM_REGISTRY[name] = llm_class
    logger.info(f"Registered new LLM: {name}")


__all__ = [
    "LLM_REGISTRY",
    "get_all_llms",
    "get_llm",
    "register_llm",
    "BedrockLLM",
    "OpenAILLM",
    "GeminiLLM",
]

"""Configuration for Agent."""

import logging
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Agent settings."""
    
    # MCP Server (for tools)
    mcp_server_url: str = "http://toolbox:8000"
    
    # LLM Gateway (for LLM calls)
    llm_gateway_url: str = "http://llm-gateway:8003"
    default_model: str = "bedrock-nova-pro"
    
    # Logging
    log_level: str = "DEBUG"
    
    # API
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def setup_logging(log_level: str = "DEBUG"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


settings = Settings()

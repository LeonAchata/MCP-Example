"""Configuration for Agent."""

import logging
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Agent settings."""
    
    # MCP Server
    mcp_server_url: str = "http://mcp-server:8000"
    
    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str
    aws_secret_access_key: str
    bedrock_model_id: str = "us.amazon.nova-pro-v1:0"
    
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

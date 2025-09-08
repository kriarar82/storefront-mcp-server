"""
Configuration settings for the Product MCP Server
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuration for the MCP server"""
    
    # Java microservice configuration
    product_service_url: str = "http://localhost:8080"
    product_service_timeout: int = 30
    
    # MCP server configuration
    server_name: str = "product-info-server"
    server_version: str = "1.0.0"
    
    # Logging configuration
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Create configuration from environment variables"""
        return cls(
            product_service_url=os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8080"),
            product_service_timeout=int(os.getenv("PRODUCT_SERVICE_TIMEOUT", "30")),
            server_name=os.getenv("MCP_SERVER_NAME", "product-info-server"),
            server_version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

# Default configuration
DEFAULT_CONFIG = ServerConfig.from_env()

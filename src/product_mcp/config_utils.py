"""
Configuration utilities for the Product MCP Server
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .config import ServerConfig, Environment

def get_config(environment: Optional[str] = None) -> ServerConfig:
    """
    Get configuration for the specified environment or auto-detect from environment variables.
    
    Args:
        environment: Environment name (development, production, test, docker)
                   If None, will use ENVIRONMENT env var or default to development
    
    Returns:
        ServerConfig: Configured server configuration
    """
    if environment:
        try:
            env_enum = Environment(environment.lower())
            return ServerConfig.for_environment(env_enum)
        except ValueError:
            logging.warning(f"Unknown environment '{environment}', using environment variables")
            return ServerConfig.from_env()
    else:
        return ServerConfig.from_env()

def validate_config(config: ServerConfig) -> bool:
    """
    Validate configuration and log any errors.
    
    Args:
        config: ServerConfig to validate
        
    Returns:
        bool: True if valid, False if errors found
    """
    errors = config.validate()
    if errors:
        logging.error("Configuration validation failed:")
        for error in errors:
            logging.error(f"  - {error}")
        return False
    return True

def setup_logging(config: ServerConfig) -> None:
    """
    Set up logging based on configuration.
    
    Args:
        config: ServerConfig containing logging configuration
    """
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific logger levels
    if config.debug:
        logging.getLogger('httpx').setLevel(logging.DEBUG)
        logging.getLogger('mcp').setLevel(logging.DEBUG)
    else:
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('mcp').setLevel(logging.INFO)

def get_environment_info(config: ServerConfig) -> Dict[str, Any]:
    """
    Get environment information for debugging and monitoring.
    
    Args:
        config: ServerConfig to get info from
        
    Returns:
        Dict containing environment information
    """
    return {
        "environment": config.environment.value,
        "debug": config.debug,
        "server_name": config.server_name,
        "server_version": config.server_version,
        "service_url": config.service_url,
        "log_level": config.log_level,
        "host": config.host,
        "port": config.port,
        "security_enabled": bool(config.security.secret_key),
        "cors_enabled": config.security.enable_cors,
        "metrics_enabled": config.monitoring.metrics_enabled
    }

def create_env_file_template(environment: Environment, output_path: Optional[str] = None) -> str:
    """
    Create a template environment file for the specified environment.
    
    Args:
        environment: Environment to create template for
        output_path: Optional path to save the template
        
    Returns:
        str: Template content
    """
    templates = {
        Environment.DEVELOPMENT: """# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Java Microservice Configuration
PRODUCT_SERVICE_URL=http://localhost:8080
PRODUCT_SERVICE_TIMEOUT=30

# MCP Server Configuration
MCP_SERVER_NAME=product-info-server-dev
MCP_SERVER_VERSION=1.0.0-dev

# Logging Configuration
LOG_LEVEL=DEBUG

# Development specific settings
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Monitoring and Health Checks
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true
""",
        Environment.PRODUCTION: """# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Java Microservice Configuration
PRODUCT_SERVICE_URL=http://product-service:8080
PRODUCT_SERVICE_TIMEOUT=60

# MCP Server Configuration
MCP_SERVER_NAME=product-info-server
MCP_SERVER_VERSION=1.0.0

# Logging Configuration
LOG_LEVEL=INFO

# Production specific settings
ENABLE_CORS=false
CORS_ORIGINS=

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Performance
MAX_CONNECTIONS=100
CONNECTION_POOL_SIZE=20

# Monitoring and Health Checks
HEALTH_CHECK_INTERVAL=60
METRICS_ENABLED=true
SENTRY_DSN=your-sentry-dsn-here
""",
        Environment.TEST: """# Test Environment Configuration
ENVIRONMENT=test
DEBUG=true

# Java Microservice Configuration
PRODUCT_SERVICE_URL=http://localhost:8081
PRODUCT_SERVICE_TIMEOUT=10

# MCP Server Configuration
MCP_SERVER_NAME=product-info-server-test
MCP_SERVER_VERSION=1.0.0-test

# Logging Configuration
LOG_LEVEL=WARNING

# Test specific settings
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000

# Test timeouts
TEST_TIMEOUT=5
MOCK_EXTERNAL_SERVICES=true
""",
        Environment.DOCKER: """# Docker Environment Configuration
ENVIRONMENT=docker
DEBUG=false

# Java Microservice Configuration
PRODUCT_SERVICE_URL=http://product-service:8080
PRODUCT_SERVICE_TIMEOUT=30

# MCP Server Configuration
MCP_SERVER_NAME=product-info-server-docker
MCP_SERVER_VERSION=1.0.0

# Logging Configuration
LOG_LEVEL=INFO

# Docker specific settings
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Container networking
HOST=0.0.0.0
PORT=8000

# Health checks
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true
"""
    }
    
    template = templates.get(environment, templates[Environment.DEVELOPMENT])
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(template)
        logging.info(f"Environment template created: {output_path}")
    
    return template

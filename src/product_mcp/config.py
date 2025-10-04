"""
Configuration settings for the Product MCP Server
Supports environment-based configuration with validation and fallbacks.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class Environment(Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"
    DOCKER = "docker"

@dataclass
class SecurityConfig:
    """Security-related configuration"""
    secret_key: Optional[str] = None
    allowed_hosts: List[str] = field(default_factory=list)
    enable_cors: bool = False
    cors_origins: List[str] = field(default_factory=list)

@dataclass
class PerformanceConfig:
    """Performance-related configuration"""
    max_connections: int = 100
    connection_pool_size: int = 20
    health_check_interval: int = 30

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    metrics_enabled: bool = True
    sentry_dsn: Optional[str] = None
    health_check_interval: int = 30

@dataclass
class ServerConfig:
    """Configuration for the MCP server"""
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Java microservice configuration
    product_service_url: str = "http://localhost:8080"
    product_service_timeout: int = 30
    
    # MCP server configuration
    server_name: str = "product-info-server"
    server_version: str = "1.0.0"
    
    # Logging configuration
    log_level: str = "INFO"
    
    # Network configuration
    host: str = "localhost"
    port: int = 8000
    
    # Nested configurations
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'ServerConfig':
        """Create configuration from environment variables and optional env file"""
        # Load environment file if specified
        if env_file and Path(env_file).exists():
            cls._load_env_file(env_file)
        
        # Determine environment
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        try:
            environment = Environment(env_str)
        except ValueError:
            logging.warning(f"Unknown environment '{env_str}', defaulting to development")
            environment = Environment.DEVELOPMENT
        
        # Parse CORS origins
        cors_origins = []
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        if cors_origins_str:
            cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
        
        # Parse allowed hosts
        allowed_hosts = []
        allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "")
        if allowed_hosts_str:
            allowed_hosts = [host.strip() for host in allowed_hosts_str.split(",") if host.strip()]
        
        return cls(
            environment=environment,
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on"),
            product_service_url=os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8080"),
            product_service_timeout=int(os.getenv("PRODUCT_SERVICE_TIMEOUT", "30")),
            server_name=os.getenv("MCP_SERVER_NAME", "product-info-server"),
            server_version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            host=os.getenv("HOST", "localhost"),
            port=int(os.getenv("PORT", "8000")),
            security=SecurityConfig(
                secret_key=os.getenv("SECRET_KEY"),
                allowed_hosts=allowed_hosts,
                enable_cors=os.getenv("ENABLE_CORS", "false").lower() in ("true", "1", "yes", "on"),
                cors_origins=cors_origins
            ),
            performance=PerformanceConfig(
                max_connections=int(os.getenv("MAX_CONNECTIONS", "100")),
                connection_pool_size=int(os.getenv("CONNECTION_POOL_SIZE", "20")),
                health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
            ),
            monitoring=MonitoringConfig(
                metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() in ("true", "1", "yes", "on"),
                sentry_dsn=os.getenv("SENTRY_DSN"),
                health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
            )
        )
    
    @classmethod
    def for_environment(cls, environment: Environment) -> 'ServerConfig':
        """Create configuration for a specific environment"""
        config_dir = Path(__file__).parent.parent.parent / "config"
        env_file = config_dir / f"env.{environment.value}"
        
        if env_file.exists():
            return cls.from_env(str(env_file))
        else:
            logging.warning(f"Environment file {env_file} not found, using defaults")
            return cls.from_env()
    
    @staticmethod
    def _load_env_file(env_file: str) -> None:
        """Load environment variables from a file"""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logging.error(f"Error loading environment file {env_file}: {e}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.product_service_url:
            errors.append("PRODUCT_SERVICE_URL is required")
        
        if not self.server_name:
            errors.append("MCP_SERVER_NAME is required")
        
        if not self.server_version:
            errors.append("MCP_SERVER_VERSION is required")
        
        # Validate URL format
        if self.product_service_url and not self.product_service_url.startswith(('http://', 'https://')):
            errors.append("PRODUCT_SERVICE_URL must start with http:// or https://")
        
        # Validate numeric fields
        if self.product_service_timeout <= 0:
            errors.append("PRODUCT_SERVICE_TIMEOUT must be positive")
        
        if self.port <= 0 or self.port > 65535:
            errors.append("PORT must be between 1 and 65535")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            if not self.security.secret_key:
                errors.append("SECRET_KEY is required in production")
            if not self.security.allowed_hosts:
                errors.append("ALLOWED_HOSTS is required in production")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "product_service_url": self.product_service_url,
            "product_service_timeout": self.product_service_timeout,
            "server_name": self.server_name,
            "server_version": self.server_version,
            "log_level": self.log_level,
            "host": self.host,
            "port": self.port,
            "security": {
                "secret_key": self.security.secret_key,
                "allowed_hosts": self.security.allowed_hosts,
                "enable_cors": self.security.enable_cors,
                "cors_origins": self.security.cors_origins
            },
            "performance": {
                "max_connections": self.performance.max_connections,
                "connection_pool_size": self.performance.connection_pool_size,
                "health_check_interval": self.performance.health_check_interval
            },
            "monitoring": {
                "metrics_enabled": self.monitoring.metrics_enabled,
                "sentry_dsn": self.monitoring.sentry_dsn,
                "health_check_interval": self.monitoring.health_check_interval
            }
        }

# Default configuration
DEFAULT_CONFIG = ServerConfig.from_env()

"""
Configuration settings for the Product MCP Server
Supports environment-based configuration with validation and fallbacks.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
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
class SemanticSearchConfig:
    """Semantic search configuration"""
    model_name: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.3
    max_results: int = 10
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour in seconds

@dataclass
class RequestMapping:
    """Configuration for API request mappings"""
    endpoint: str
    method: str  # GET, POST, PUT, DELETE
    description: str
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    response_parser: Optional[str] = None  # Custom parser function name
    param_types: Optional[Dict[str, str]] = None  # Parameter type mappings

@dataclass
class GenericAPIConfig:
    """Configuration for generic API passthrough"""
    enable_generic_api: bool = True
    request_mappings: Dict[str, RequestMapping] = field(default_factory=dict)
    default_timeout: int = 30
    enable_request_logging: bool = True
    enable_response_logging: bool = True

@dataclass
class ServerConfig:
    """Configuration for the MCP server"""
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Microservice configuration
    service_url: str = "http://localhost:8080"
    service_timeout: int = 30
    
    # MCP server configuration
    server_name: str = "generic-mcp-server"
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
    semantic_search: SemanticSearchConfig = field(default_factory=SemanticSearchConfig)
    generic_api: GenericAPIConfig = field(default_factory=GenericAPIConfig)
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'ServerConfig':
        """Create configuration from environment variables and optional env file"""
        # Determine environment first
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        try:
            environment = Environment(env_str)
        except ValueError:
            logging.warning(f"Unknown environment '{env_str}', defaulting to development")
            environment = Environment.DEVELOPMENT
        
        # Load environment file if specified, or auto-load based on environment
        if env_file and Path(env_file).exists():
            logging.info(f"Loading specified environment file: {env_file}")
            cls._load_env_file(env_file)
        else:
            # Auto-load environment-specific .env file
            env_file_path = f"config/env.{environment.value}"
            if Path(env_file_path).exists():
                logging.info(f"Loading environment-specific file: {env_file_path}")
                cls._load_env_file(env_file_path)
                logging.info(f"Loaded environment configuration from {env_file_path}")
            else:
                logging.warning(f"Environment file not found: {env_file_path}")
        
        # Load dotenv for additional environment variables
        load_dotenv()
        
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
            service_url=os.getenv("SERVICE_URL", "http://localhost:8080"),
            service_timeout=int(os.getenv("SERVICE_TIMEOUT", "30")),
            server_name=os.getenv("MCP_SERVER_NAME", "generic-mcp-server"),
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
            ),
            semantic_search=SemanticSearchConfig(
                model_name=os.getenv("SEMANTIC_MODEL_NAME", "all-MiniLM-L6-v2"),
                similarity_threshold=float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", "0.3")),
                max_results=int(os.getenv("SEMANTIC_MAX_RESULTS", "10")),
                enable_caching=os.getenv("SEMANTIC_ENABLE_CACHING", "true").lower() in ("true", "1", "yes", "on"),
                cache_ttl=int(os.getenv("SEMANTIC_CACHE_TTL", "3600"))
            ),
            generic_api=GenericAPIConfig(
                enable_generic_api=os.getenv("GENERIC_API_ENABLED", "true").lower() in ("true", "1", "yes", "on"),
                default_timeout=int(os.getenv("GENERIC_API_TIMEOUT", "30")),
                enable_request_logging=os.getenv("GENERIC_API_LOG_REQUESTS", "true").lower() in ("true", "1", "yes", "on"),
                enable_response_logging=os.getenv("GENERIC_API_LOG_RESPONSES", "true").lower() in ("true", "1", "yes", "on"),
                request_mappings=cls._get_default_request_mappings()
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
                        # Set environment variable (override existing if present)
                        os.environ[key] = value
        except Exception as e:
            logging.error(f"Error loading environment file {env_file}: {e}")
    
    @staticmethod
    def _get_default_request_mappings() -> Dict[str, RequestMapping]:
        """Get default request mappings for common API endpoints"""
        # Try to load from external file first
        try:
            from .mapping_loader import load_tool_mappings
            mappings = load_tool_mappings()
            if mappings:
                return mappings
        except Exception as e:
            logging.warning(f"Could not load external mappings: {e}")
        
        # Fallback to hardcoded defaults
        return {
            "get_item": RequestMapping(
                endpoint="/api/items/{id}",
                method="GET",
                description="Get a specific item by ID",
                required_params=["id"],
                response_parser="parse_item"
            ),
            "get_categories": RequestMapping(
                endpoint="/api/categories",
                method="GET",
                description="Get all available categories",
                response_parser="parse_categories"
            ),
            "get_items_by_category": RequestMapping(
                endpoint="/api/items/category/{category}",
                method="GET",
                description="Get items by category",
                required_params=["category"],
                optional_params=["limit"],
                response_parser="parse_items_list"
            ),
            "search_items": RequestMapping(
                endpoint="/api/items/search",
                method="POST",
                description="Search items with filters",
                required_params=["query"],
                optional_params=["filter", "top"],
                response_parser="parse_items_list"
            ),
            "generic_request": RequestMapping(
                endpoint="/api/{path}",
                method="POST",
                description="Generic API request passthrough",
                required_params=["path"],
                optional_params=["method", "body", "params", "headers"]
            )
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.service_url:
            errors.append("SERVICE_URL is required")
        
        if not self.server_name:
            errors.append("MCP_SERVER_NAME is required")
        
        if not self.server_version:
            errors.append("MCP_SERVER_VERSION is required")
        
        # Validate URL format
        if self.service_url and not self.service_url.startswith(('http://', 'https://')):
            errors.append("SERVICE_URL must start with http:// or https://")
        
        # Validate numeric fields
        if self.service_timeout <= 0:
            errors.append("SERVICE_TIMEOUT must be positive")
        
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
            "service_url": self.service_url,
            "service_timeout": self.service_timeout,
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
            },
            "semantic_search": {
                "model_name": self.semantic_search.model_name,
                "similarity_threshold": self.semantic_search.similarity_threshold,
                "max_results": self.semantic_search.max_results,
                "enable_caching": self.semantic_search.enable_caching,
                "cache_ttl": self.semantic_search.cache_ttl
            },
            "generic_api": {
                "enable_generic_api": self.generic_api.enable_generic_api,
                "default_timeout": self.generic_api.default_timeout,
                "enable_request_logging": self.generic_api.enable_request_logging,
                "enable_response_logging": self.generic_api.enable_response_logging,
                "request_mappings": {
                    name: {
                        "endpoint": mapping.endpoint,
                        "method": mapping.method,
                        "description": mapping.description,
                        "required_params": mapping.required_params,
                        "optional_params": mapping.optional_params,
                        "response_parser": mapping.response_parser
                    } for name, mapping in self.generic_api.request_mappings.items()
                }
            }
        }

# Default configuration
DEFAULT_CONFIG = ServerConfig.from_env()

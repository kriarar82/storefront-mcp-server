# Configuration Guide

This document describes the environment-based configuration system for the Product MCP Server.

## Overview

The Product MCP Server supports multiple environments with different configuration settings. The configuration system automatically detects the environment and loads the appropriate settings.

## Supported Environments

- **development**: Local development environment
- **production**: Production deployment
- **test**: Testing environment
- **docker**: Docker container environment

## Configuration Files

Environment-specific configuration files are located in the `config/` directory:

- `config/env.development` - Development settings
- `config/env.production` - Production settings
- `config/env.test` - Test settings
- `config/env.docker` - Docker settings

## Configuration Structure

The configuration system is organized into several categories:

### Core Configuration
- `ENVIRONMENT`: Environment name (development, production, test, docker)
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Service Configuration
- `PRODUCT_SERVICE_URL`: URL of the Java microservice
- `PRODUCT_SERVICE_TIMEOUT`: Timeout for service calls (seconds)

### Server Configuration
- `MCP_SERVER_NAME`: Name of the MCP server
- `MCP_SERVER_VERSION`: Version of the MCP server
- `HOST`: Host to bind to
- `PORT`: Port to listen on

### Security Configuration
- `SECRET_KEY`: Secret key for security (required in production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `ENABLE_CORS`: Enable CORS (true/false)
- `CORS_ORIGINS`: Comma-separated list of CORS origins

### Performance Configuration
- `MAX_CONNECTIONS`: Maximum number of connections
- `CONNECTION_POOL_SIZE`: Connection pool size
- `HEALTH_CHECK_INTERVAL`: Health check interval (seconds)

### Monitoring Configuration
- `METRICS_ENABLED`: Enable metrics collection (true/false)
- `SENTRY_DSN`: Sentry DSN for error tracking
- `HEALTH_CHECK_INTERVAL`: Health check interval (seconds)

## Usage

### Environment Detection

The system automatically detects the environment in the following order:

1. `ENVIRONMENT` environment variable
2. Default to `development`

### Loading Configuration

```python
from product_mcp.config_utils import get_config

# Auto-detect environment
config = get_config()

# Specify environment
config = get_config("production")
```

### Configuration Validation

```python
from product_mcp.config_utils import validate_config

config = get_config()
if not validate_config(config):
    print("Configuration is invalid")
```

### CLI Configuration Management

The system includes a CLI tool for managing configurations:

```bash
# Validate configuration
python -m product_mcp.config_cli validate

# Show current configuration
python -m product_mcp.config_cli show

# Show configuration as JSON
python -m product_mcp.config_cli show --json

# Create environment template
python -m product_mcp.config_cli create-template production

# Test configuration
python -m product_mcp.config_cli test
```

## Environment-Specific Settings

### Development Environment
- Debug mode enabled
- Verbose logging
- CORS enabled for local development
- Shorter timeouts for faster feedback

### Production Environment
- Debug mode disabled
- INFO level logging
- CORS disabled
- Security keys required
- Performance optimizations
- Monitoring enabled

### Test Environment
- Debug mode enabled
- WARNING level logging
- Short timeouts
- Mock services enabled

### Docker Environment
- Optimized for container deployment
- CORS enabled for container networking
- Health checks configured

## Deployment

### Docker Compose

The `docker-compose.yml` file automatically loads the Docker environment configuration:

```bash
# Use default Docker configuration
docker-compose up

# Override environment
ENVIRONMENT=production docker-compose up
```

### Azure Container Apps

The Azure deployment script loads environment-specific configuration:

```bash
# Deploy to production
ENVIRONMENT=production ./deployment/azure/deploy.sh

# Deploy to development
ENVIRONMENT=development ./deployment/azure/deploy.sh
```

## Best Practices

1. **Never commit sensitive data**: Use environment variables for secrets
2. **Use environment-specific files**: Keep configurations separate
3. **Validate configurations**: Always validate before deployment
4. **Document changes**: Update this guide when adding new settings
5. **Test configurations**: Use the CLI tools to test configurations

## Troubleshooting

### Common Issues

1. **Configuration not loading**: Check that the environment file exists and is readable
2. **Validation errors**: Use the CLI to validate and see specific error messages
3. **Environment not detected**: Ensure the `ENVIRONMENT` variable is set correctly

### Debug Configuration

```python
from product_mcp.config_utils import get_environment_info

config = get_config()
info = get_environment_info(config)
print(info)
```

## Adding New Configuration

1. Add the new setting to the `ServerConfig` class in `config.py`
2. Add environment variable parsing in the `from_env` method
3. Add validation rules in the `validate` method
4. Update environment files with the new setting
5. Update this documentation

## Security Considerations

- Never hardcode secrets in configuration files
- Use environment variables for sensitive data
- Validate all configuration inputs
- Use different secrets for different environments
- Regularly rotate secrets in production

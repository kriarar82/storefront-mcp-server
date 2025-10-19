#!/usr/bin/env python3
"""
Configuration CLI for the Product MCP Server
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .config import Environment
from .config_utils import get_config, validate_config, create_env_file_template

def validate_command(args):
    """Validate configuration"""
    # If environment is specified, load from that environment file
    if args.environment:
        from .config import ServerConfig, Environment
        try:
            env_enum = Environment(args.environment.lower())
            config = ServerConfig.for_environment(env_enum)
        except ValueError:
            config = get_config(args.environment)
    else:
        config = get_config()
    
    is_valid = validate_config(config)
    
    if is_valid:
        print("✅ Configuration is valid")
        return 0
    else:
        print("❌ Configuration validation failed")
        return 1

def show_command(args):
    """Show current configuration"""
    # If environment is specified, load from that environment file
    if args.environment:
        from .config import ServerConfig, Environment
        try:
            env_enum = Environment(args.environment.lower())
            config = ServerConfig.for_environment(env_enum)
        except ValueError:
            config = get_config(args.environment)
    else:
        config = get_config()
    
    if args.json:
        print(json.dumps(config.to_dict(), indent=2))
    else:
        print(f"Environment: {config.environment.value}")
        print(f"Debug: {config.debug}")
        print(f"Server Name: {config.server_name}")
        print(f"Server Version: {config.server_version}")
        print(f"Service URL: {config.service_url}")
        print(f"Service Timeout: {config.service_timeout}")
        print(f"Log Level: {config.log_level}")
        print(f"Host: {config.host}")
        print(f"Port: {config.port}")
        print(f"CORS Enabled: {config.security.enable_cors}")
        print(f"CORS Origins: {', '.join(config.security.cors_origins)}")
        print(f"Metrics Enabled: {config.monitoring.metrics_enabled}")

def create_template_command(args):
    """Create environment file template"""
    environment = Environment(args.environment)
    output_path = args.output or f"config/env.{environment.value}"
    
    template = create_env_file_template(environment, output_path)
    
    if not args.output:
        print(f"Template created: {output_path}")
    else:
        print(f"Template created: {output_path}")

def test_command(args):
    """Test configuration by creating a server instance"""
    try:
        from .server import ProductMCPServer
        config = get_config(args.environment)
        server = ProductMCPServer(config)
        print("✅ Configuration test passed - server can be created successfully")
        return 0
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return 1

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Product MCP Server Configuration CLI")
    parser.add_argument("--environment", "-e", 
                       choices=[env.value for env in Environment],
                       help="Environment to use (default: from ENVIRONMENT env var)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument("--environment", "-e", 
                               choices=[env.value for env in Environment],
                               help="Environment to validate configuration for")
    validate_parser.set_defaults(func=validate_command)
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show current configuration")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.add_argument("--environment", "-e", 
                           choices=[env.value for env in Environment],
                           help="Environment to show configuration for")
    show_parser.set_defaults(func=show_command)
    
    # Create template command
    template_parser = subparsers.add_parser("create-template", help="Create environment file template")
    template_parser.add_argument("environment", choices=[env.value for env in Environment],
                                help="Environment to create template for")
    template_parser.add_argument("--output", "-o", help="Output file path")
    template_parser.set_defaults(func=create_template_command)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test configuration")
    test_parser.set_defaults(func=test_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())

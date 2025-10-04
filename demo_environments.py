#!/usr/bin/env python3
"""
Demo script showing how to use different environments
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from product_mcp.config import Environment
from product_mcp.config_utils import get_config, validate_config

def demo_environment_usage():
    """Demonstrate different ways to use environments"""
    print("🚀 Environment Configuration Demo")
    print("=" * 40)
    
    # Method 1: Auto-detect from ENVIRONMENT variable
    print("\n1️⃣ Auto-detect from ENVIRONMENT variable:")
    print("-" * 40)
    
    # Set environment variable
    os.environ["ENVIRONMENT"] = "production"
    config = get_config()
    print(f"   Environment: {config.environment.value}")
    print(f"   Debug: {config.debug}")
    print(f"   Server Name: {config.server_name}")
    
    # Method 2: Specify environment directly
    print("\n2️⃣ Specify environment directly:")
    print("-" * 40)
    
    config = get_config("development")
    print(f"   Environment: {config.environment.value}")
    print(f"   Debug: {config.debug}")
    print(f"   Server Name: {config.server_name}")
    
    # Method 3: Use for_environment class method
    print("\n3️⃣ Use for_environment class method:")
    print("-" * 40)
    
    from product_mcp.config import ServerConfig
    config = ServerConfig.for_environment(Environment.DOCKER)
    print(f"   Environment: {config.environment.value}")
    print(f"   Debug: {config.debug}")
    print(f"   Server Name: {config.server_name}")
    
    # Method 4: Show configuration differences
    print("\n4️⃣ Configuration differences by environment:")
    print("-" * 40)
    
    environments = ["development", "production", "test", "docker"]
    
    for env_name in environments:
        config = get_config(env_name)
        print(f"   {env_name.upper()}:")
        print(f"     Debug: {config.debug}")
        print(f"     Log Level: {config.log_level}")
        print(f"     CORS: {config.security.enable_cors}")
        print(f"     Timeout: {config.product_service_timeout}s")
    
    # Method 5: Validate configurations
    print("\n5️⃣ Configuration validation:")
    print("-" * 40)
    
    for env_name in environments:
        config = get_config(env_name)
        is_valid = validate_config(config)
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"   {env_name.upper()}: {status}")
        
        if not is_valid:
            errors = config.validate()
            for error in errors:
                print(f"     - {error}")

def demo_environment_switching():
    """Demonstrate switching between environments"""
    print("\n🔄 Environment Switching Demo")
    print("=" * 40)
    
    # Simulate different deployment scenarios
    scenarios = [
        ("Local Development", "development"),
        ("CI/CD Testing", "test"),
        ("Docker Deployment", "docker"),
        ("Production Deployment", "production")
    ]
    
    for scenario_name, env_name in scenarios:
        print(f"\n📋 {scenario_name}:")
        print("-" * 30)
        
        # Set environment
        os.environ["ENVIRONMENT"] = env_name
        config = get_config()
        
        print(f"   Environment: {config.environment.value}")
        print(f"   Server Name: {config.server_name}")
        print(f"   Debug Mode: {config.debug}")
        print(f"   Log Level: {config.log_level}")
        print(f"   CORS Enabled: {config.security.enable_cors}")
        print(f"   Metrics Enabled: {config.monitoring.metrics_enabled}")
        
        # Show environment-specific settings
        if config.environment == Environment.PRODUCTION:
            print(f"   Security: Secret key {'set' if config.security.secret_key else 'not set'}")
            print(f"   Allowed Hosts: {len(config.security.allowed_hosts)} configured")
        elif config.environment == Environment.DOCKER:
            print(f"   Host: {config.host}")
            print(f"   Port: {config.port}")

if __name__ == "__main__":
    demo_environment_usage()
    demo_environment_switching()
    
    print(f"\n🎉 Demo completed!")
    print(f"\n💡 Try these commands:")
    print(f"   python -m src.product_mcp.config_cli validate")
    print(f"   python -m src.product_mcp.config_cli show")
    print(f"   ENVIRONMENT=production python -m src.product_mcp.server")

#!/usr/bin/env python3
"""
Command Line Interface for Product MCP Server
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from product_mcp.server import main as server_main
from product_mcp.test_client import main as test_main
from product_mcp.config import ServerConfig


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Product MCP Server - A Model Context Protocol server for product information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s server                    # Start the MCP server
  %(prog)s server --url http://localhost:9000  # Start with custom microservice URL
  %(prog)s test                      # Run test suite
  %(prog)s test --server-command "python -m src.product_mcp.server"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the MCP server")
    server_parser.add_argument(
        "--url",
        default=None,
        help="Java microservice URL (default: from environment or http://localhost:8080)"
    )
    server_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Request timeout in seconds (default: 30)"
    )
    server_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Logging level (default: INFO)"
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.add_argument(
        "--server-command",
        default="python -m src.product_mcp.server",
        help="Command to start the MCP server for testing"
    )
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "server":
        # Set environment variables if provided
        if args.url:
            import os
            os.environ["PRODUCT_SERVICE_URL"] = args.url
        if args.timeout:
            import os
            os.environ["PRODUCT_SERVICE_TIMEOUT"] = str(args.timeout)
        if args.log_level:
            import os
            os.environ["LOG_LEVEL"] = args.log_level
        
        print("🚀 Starting Product MCP Server...")
        print("📡 Connecting to Java microservice...")
        print("🔧 Available tools: get_product, search_products, get_categories, get_products_by_category")
        print("=" * 60)
        
        try:
            asyncio.run(server_main())
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")
            sys.exit(1)
    
    elif args.command == "test":
        print("🧪 Running Product MCP Server Test Suite...")
        try:
            asyncio.run(test_main())
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user")
        except Exception as e:
            print(f"❌ Test error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

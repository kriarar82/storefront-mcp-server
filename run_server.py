#!/usr/bin/env python3
"""
Convenience script to run the Product MCP Server
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from product_mcp.server import main

if __name__ == "__main__":
    print("🚀 Starting Product MCP Server...")
    print("📡 Connecting to Java microservice...")
    print("🔧 Available tools: get_product, search_products, get_categories, get_products_by_category")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

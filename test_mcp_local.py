#!/usr/bin/env python3
"""
Test MCP server locally using stdio protocol
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.client.stdio import stdio_client
from mcp.types import CallToolRequest

async def test_mcp_server_local():
    """Test the MCP server locally using stdio"""
    print("🧪 Testing MCP Server Locally (stdio)")
    print("=" * 50)
    
    # Server parameters for local testing
    server_params = {
        "command": "python",
        "args": ["-m", "src.product_mcp.server"],
        "env": {
            "ENVIRONMENT": "development",
            "PRODUCT_SERVICE_URL": "http://localhost:8080"
        }
    }
    
    try:
        async with stdio_client(server_params) as (read, write):
            # Initialize the session
            print("🔄 Initializing MCP session...")
            init_result = await read()
            print(f"✅ Session initialized: {init_result}")
            
            # List available tools
            print("\n📋 Listing available tools...")
            tools_result = await read()
            print(f"✅ Tools available: {json.dumps(tools_result, indent=2)}")
            
            # Test search_products tool
            print("\n🔍 Testing search_products tool...")
            search_request = CallToolRequest(
                name="search_products",
                arguments={"query": "laptop", "top": 5}
            )
            await write(search_request)
            search_result = await read()
            print(f"✅ Search result: {json.dumps(search_result, indent=2)}")
            
            # Test get_categories tool
            print("\n📂 Testing get_categories tool...")
            categories_request = CallToolRequest(
                name="get_categories",
                arguments={}
            )
            await write(categories_request)
            categories_result = await read()
            print(f"✅ Categories result: {json.dumps(categories_result, indent=2)}")
            
            # Test get_products_by_category tool
            print("\n🏷️ Testing get_products_by_category tool...")
            category_request = CallToolRequest(
                name="get_products_by_category",
                arguments={"category": "Electronics", "limit": 3}
            )
            await write(category_request)
            category_result = await read()
            print(f"✅ Category result: {json.dumps(category_result, indent=2)}")
            
            # Test get_product tool
            print("\n🔍 Testing get_product tool...")
            product_request = CallToolRequest(
                name="get_product",
                arguments={"product_id": "1"}
            )
            await write(product_request)
            product_result = await read()
            print(f"✅ Product result: {json.dumps(product_result, indent=2)}")
            
            print("\n🎉 All MCP tests completed successfully!")
            
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_mcp_server_local())

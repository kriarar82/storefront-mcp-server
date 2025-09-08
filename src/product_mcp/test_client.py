#!/usr/bin/env python3
"""
Test client for the Product MCP Server
This script demonstrates how to interact with the MCP server programmatically.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class MCPTestClient:
    """Test client for the Product MCP Server"""
    
    def __init__(self, server_command: str = "python -m src.product_mcp.server"):
        self.server_command = server_command
        self.process = None
    
    async def start_server(self):
        """Start the MCP server process"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command.split(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("✅ MCP Server started successfully")
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            sys.exit(1)
    
    async def stop_server(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🛑 MCP Server stopped")
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server and get response"""
        if not self.process:
            raise RuntimeError("Server not started")
        
        # Send message
        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
        
        return json.loads(response_line.decode().strip())
    
    async def test_initialization(self):
        """Test MCP server initialization"""
        print("\n🔧 Testing MCP server initialization...")
        
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        try:
            response = await self.send_message(init_message)
            print(f"✅ Initialization response: {json.dumps(response, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def test_list_tools(self):
        """Test listing available tools"""
        print("\n🔧 Testing tool listing...")
        
        list_tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        try:
            response = await self.send_message(list_tools_message)
            print(f"✅ Available tools: {json.dumps(response, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Tool listing failed: {e}")
            return False
    
    async def test_get_categories(self):
        """Test getting product categories"""
        print("\n🔧 Testing get_categories tool...")
        
        get_categories_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_categories",
                "arguments": {}
            }
        }
        
        try:
            response = await self.send_message(get_categories_message)
            print(f"✅ Categories response: {json.dumps(response, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Get categories failed: {e}")
            return False
    
    async def test_search_products(self):
        """Test searching for products"""
        print("\n🔧 Testing search_products tool...")
        
        search_products_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "search_products",
                "arguments": {
                    "query": "laptop",
                    "limit": 5
                }
            }
        }
        
        try:
            response = await self.send_message(search_products_message)
            print(f"✅ Search products response: {json.dumps(response, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Search products failed: {e}")
            return False
    
    async def test_get_product(self):
        """Test getting a specific product"""
        print("\n🔧 Testing get_product tool...")
        
        get_product_message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_product",
                "arguments": {
                    "product_id": "12345"
                }
            }
        }
        
        try:
            response = await self.send_message(get_product_message)
            print(f"✅ Get product response: {json.dumps(response, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Get product failed: {e}")
            return False
    
    async def test_get_products_by_category(self):
        """Test getting products by category"""
        print("\n🔧 Testing get_products_by_category tool...")
        
        get_products_by_category_message = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_products_by_category",
                "arguments": {
                    "category": "electronics",
                    "limit": 3
                }
            }
        }
        
        try:
            response = await self.send_message(get_products_by_category_message)
            print(f"✅ Get products by category response: {json.dumps(response, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Get products by category failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting MCP Server Test Suite")
        print("=" * 50)
        
        try:
            await self.start_server()
            
            # Wait a moment for server to initialize
            await asyncio.sleep(1)
            
            tests = [
                self.test_initialization,
                self.test_list_tools,
                self.test_get_categories,
                self.test_search_products,
                self.test_get_product,
                self.test_get_products_by_category
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if await test():
                    passed += 1
                await asyncio.sleep(0.5)  # Small delay between tests
            
            print("\n" + "=" * 50)
            print(f"📊 Test Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed!")
            else:
                print("⚠️  Some tests failed. Check the Java microservice connection.")
            
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user")
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
        finally:
            await self.stop_server()

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Product MCP Server")
    parser.add_argument(
        "--server-command",
        default="python mcp_server.py",
        help="Command to start the MCP server (default: python mcp_server.py)"
    )
    
    args = parser.parse_args()
    
    client = MCPTestClient(args.server_command)
    await client.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

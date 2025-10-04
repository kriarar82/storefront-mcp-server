#!/usr/bin/env python3
"""
Container-friendly MCP Server runner
This version keeps the server running and provides HTTP health checks
"""

import asyncio
import sys
import signal
import os
from pathlib import Path
from aiohttp import web
import logging

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from product_mcp.server import ProductMCPServer
from product_mcp.config_utils import get_config, setup_logging

# Global server instance
mcp_server = None
http_server = None

async def health_check(request):
    """HTTP health check endpoint"""
    try:
        # Check if MCP server is initialized
        if mcp_server is None:
            return web.json_response({"status": "unhealthy", "reason": "MCP server not initialized"}, status=503)
        
        # Check if product service is reachable
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{mcp_server.config.product_service_url}/health")
                if response.status_code < 500:
                    return web.json_response({
                        "status": "healthy",
                        "mcp_server": mcp_server.config.server_name,
                        "version": mcp_server.config.server_version,
                        "environment": mcp_server.config.environment.value,
                        "product_service": "reachable"
                    })
                else:
                    return web.json_response({
                        "status": "degraded",
                        "reason": f"Product service returned {response.status_code}"
                    }, status=503)
        except Exception as e:
            return web.json_response({
                "status": "degraded",
                "reason": f"Product service unreachable: {str(e)}"
            }, status=503)
            
    except Exception as e:
        return web.json_response({"status": "unhealthy", "reason": str(e)}, status=500)

async def mcp_server_runner():
    """Run the MCP server in a way that keeps it alive"""
    global mcp_server
    
    try:
        # Load configuration
        config = get_config()
        setup_logging(config)
        
        # Create MCP server
        mcp_server = ProductMCPServer(config)
        
        # Start the MCP server (this will run indefinitely)
        print("🚀 Starting MCP server...")
        await mcp_server.run()
        
    except Exception as e:
        print(f"❌ MCP server error: {e}")
        logging.error(f"MCP server error: {e}")
        raise

async def start_http_server():
    """Start HTTP server for health checks"""
    global http_server
    
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/healthz', health_check)  # Kubernetes style
    app.router.add_get('/', health_check)
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', '8000'))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"🌐 HTTP health check server started on port {port}")
    print(f"   Health check: http://localhost:{port}/health")
    
    return runner

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    if http_server:
        asyncio.create_task(http_server.cleanup())
    sys.exit(0)

async def main():
    """Main entry point"""
    global http_server
    
    print("🚀 Starting Product MCP Server (Container Mode)...")
    print("📡 Connecting to Java microservice...")
    print("🔧 Available tools: get_product, search_products, get_categories, get_products_by_category")
    print("🌐 HTTP health checks enabled")
    print("=" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start HTTP server for health checks
        http_server = await start_http_server()
        
        # Start MCP server in background
        mcp_task = asyncio.create_task(mcp_server_runner())
        
        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [mcp_task], 
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logging.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        if http_server:
            await http_server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
FastAPI server that exposes MCP tools as REST endpoints
"""

import asyncio
import os
import signal
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from product_mcp.config import ServerConfig, Environment
from product_mcp.config_utils import get_config, validate_config, setup_logging, get_environment_info
from product_mcp.server import ProductMCPServer

# Global variables
app = FastAPI(
    title="Product MCP Server API",
    description="REST API for Product MCP Server tools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

mcp_server = None
config = None

# Pydantic models for request/response
class SearchProductsRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class GetProductsByCategoryRequest(BaseModel):
    category: str
    limit: Optional[int] = 10

class GetProductRequest(BaseModel):
    product_id: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server on startup"""
    global mcp_server, config
    
    try:
        print("🚀 Starting Product MCP Server (FastAPI Mode)...")
        
        # Load configuration
        config = get_config('production')
        validate_config(config)
        setup_logging(config)
        
        # Log environment info
        env_info = get_environment_info(config)
        print(f"📋 Environment: {env_info['environment']}")
        print(f"🔧 Configuration loaded successfully")
        print(f"🔗 Product Service URL: {config.product_service_url}")
        
        # Create MCP server instance
        mcp_server = ProductMCPServer(config)
        print("✅ MCP server initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize MCP server: {e}")
        raise

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "product-mcp-server-api",
            "version": "1.0.0",
            "environment": config.environment.value if config else "production",
            "mcp_server": "available" if mcp_server else "not_available",
            "tools": ["get_product", "search_products", "get_categories", "get_products_by_category"],
            "product_service_url": config.product_service_url if config else "not_configured"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/tools", response_model=List[Dict[str, Any]])
async def list_tools():
    """List available MCP tools"""
    try:
        return [
            {
                "name": "get_product",
                "description": "Get detailed information about a specific product by ID",
                "parameters": {
                    "product_id": {"type": "string", "description": "Product ID"}
                }
            },
            {
                "name": "search_products",
                "description": "Search for products by name, description, or other criteria",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                }
            },
            {
                "name": "get_categories",
                "description": "Get all available product categories",
                "parameters": {}
            },
            {
                "name": "get_products_by_category",
                "description": "Get products filtered by a specific category",
                "parameters": {
                    "category": {"type": "string", "description": "Category name"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                }
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.post("/api/tools/search_products", response_model=Dict[str, Any])
async def search_products(request: SearchProductsRequest):
    """Search for products by query"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.search_products(request.query, top=request.limit)
        
        return {
            "success": True,
            "query": request.query,
            "limit": request.limit,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/tools/search_products", response_model=Dict[str, Any])
async def search_products_get(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results")
):
    """Search for products by query (GET version)"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.search_products(query, top=limit)
        
        return {
            "success": True,
            "query": query,
            "limit": limit,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/tools/get_categories", response_model=Dict[str, Any])
async def get_categories():
    """Get all available product categories"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.get_categories()
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get categories failed: {str(e)}")

@app.get("/api/tools/get_categories", response_model=Dict[str, Any])
async def get_categories_get():
    """Get all available product categories (GET version)"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.get_categories()
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get categories failed: {str(e)}")

@app.post("/api/tools/get_products_by_category", response_model=Dict[str, Any])
async def get_products_by_category(request: GetProductsByCategoryRequest):
    """Get products filtered by category"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.get_products_by_category(request.category, request.limit)
        
        return {
            "success": True,
            "category": request.category,
            "limit": request.limit,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get products by category failed: {str(e)}")

@app.get("/api/tools/get_products_by_category", response_model=Dict[str, Any])
async def get_products_by_category_get(
    category: str = Query(..., description="Category name"),
    limit: int = Query(10, description="Maximum number of results")
):
    """Get products filtered by category (GET version)"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.get_products_by_category(category, limit)
        
        return {
            "success": True,
            "category": category,
            "limit": limit,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get products by category failed: {str(e)}")

@app.post("/api/tools/get_product", response_model=Dict[str, Any])
async def get_product(request: GetProductRequest):
    """Get detailed information about a specific product by ID"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.get_product(request.product_id)
        
        return {
            "success": True,
            "product_id": request.product_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get product failed: {str(e)}")

@app.get("/api/tools/get_product/{product_id}", response_model=Dict[str, Any])
async def get_product_get(product_id: str):
    """Get detailed information about a specific product by ID (GET version)"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")
        
        # Call the MCP tool
        result = await mcp_server.product_client.get_product(product_id)
        
        return {
            "success": True,
            "product_id": product_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get product failed: {str(e)}")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Product MCP Server API",
        "version": "1.0.0",
        "description": "REST API for Product MCP Server tools",
        "documentation": "/docs",
        "health": "/health",
        "tools": "/api/tools"
    }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point"""
    print("🚀 Starting Product MCP Server (FastAPI Mode)...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get port from environment
    port = int(os.getenv('PORT', '8000'))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🌐 Starting FastAPI server on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print(f"🛠️  Available Tools: http://{host}:{port}/api/tools")
    
    # Run the FastAPI server
    uvicorn.run(
        "run_server_fastapi:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()

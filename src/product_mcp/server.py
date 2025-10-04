#!/usr/bin/env python3
"""
MCP Server for Product Information
Communicates with a Java microservice to provide product data to AI agents.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from .config import ServerConfig, DEFAULT_CONFIG, Environment
from .config_utils import get_config, validate_config, setup_logging, get_environment_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductInfo:
    """Data class for product information"""
    id: str
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int
    image_url: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None

class ProductServiceClient:
    """Client for communicating with the Java microservice"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.base_url = config.product_service_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=config.product_service_timeout)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_product(self, product_id: str) -> Optional[ProductInfo]:
        """Get a single product by ID"""
        try:
            response = await self.client.get(f"{self.base_url}/api/products/{product_id}")
            response.raise_for_status()
            data = response.json()
            return self._parse_product(data)
        except httpx.HTTPError as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching product {product_id}: {e}")
            return None
    
    async def search_products(self, query: str, filter: Optional[str] = None, 
                            top: int = 10) -> List[ProductInfo]:
        """Search for products using POST with request body"""
        try:
            request_body = {
                "query": query,
                "top": top
            }
            if filter:
                request_body["filter"] = filter
            
            response = await self.client.post(
                f"{self.base_url}/api/products/search", 
                json=request_body
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data.get("products", []):
                product = self._parse_product(item)
                if product:
                    products.append(product)
            
            return products
        except httpx.HTTPError as e:
            logger.error(f"Error searching products: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching products: {e}")
            return []
    
    async def get_categories(self) -> List[str]:
        """Get all available product categories"""
        try:
            response = await self.client.get(f"{self.base_url}/api/products/categories")
            response.raise_for_status()
            data = response.json()
            return data.get("categories", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching categories: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching categories: {e}")
            return []
    
    async def get_products_by_category(self, category: str, limit: int = 10) -> List[ProductInfo]:
        """Get products by category"""
        try:
            params = {"limit": limit}
            response = await self.client.get(f"{self.base_url}/api/products/category/{category}", params=params)
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data.get("products", []):
                product = self._parse_product(item)
                if product:
                    products.append(product)
            
            return products
        except httpx.HTTPError as e:
            logger.error(f"Error fetching products for category {category}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching products for category {category}: {e}")
            return []
    
    def _parse_product(self, data: Dict[str, Any]) -> Optional[ProductInfo]:
        """Parse product data from the microservice response"""
        try:
            return ProductInfo(
                id=str(data.get("id", "")),
                name=data.get("name", ""),
                description=data.get("description", ""),
                price=float(data.get("price", 0.0)),
                category=data.get("category", ""),
                stock_quantity=int(data.get("stockQuantity", 0)),
                image_url=data.get("imageUrl"),
                specifications=data.get("specifications", {})
            )
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing product data: {e}")
            return None

class ProductMCPServer:
    """MCP Server for product information"""
    
    def __init__(self, config: ServerConfig = None):
        if config is None:
            config = DEFAULT_CONFIG
        
        # Validate configuration
        if not validate_config(config):
            raise ValueError("Invalid configuration provided")
        
        self.config = config
        self.server = Server(config.server_name)
        self.product_client = ProductServiceClient(config)
        self._setup_handlers()
        
        # Log environment info
        env_info = get_environment_info(config)
        logger.info(f"Starting MCP server with configuration: {env_info}")
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_product",
                    description="Get detailed information about a specific product by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "The unique identifier of the product"
                            }
                        },
                        "required": ["product_id"]
                    }
                ),
                Tool(
                    name="search_products",
                    description="Search for products by name, description, or other criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for products"
                            },
                            "filter": {
                                "type": "string",
                                "description": "Optional filter expression (e.g., \"category eq 'Electronics' and price gt 100\")"
                            },
                            "top": {
                                "type": "integer",
                                "description": "Maximum number of products to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_categories",
                    description="Get all available product categories",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_products_by_category",
                    description="Get products filtered by a specific category",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "The category to filter by"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of products to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["category"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "get_product":
                    product_id = arguments.get("product_id")
                    if not product_id:
                        return [TextContent(type="text", text="Error: product_id is required")]
                    
                    product = await self.product_client.get_product(product_id)
                    if product:
                        return [TextContent(
                            type="text",
                            text=self._format_product_info(product)
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"Product with ID '{product_id}' not found"
                        )]
                
                elif name == "search_products":
                    query = arguments.get("query")
                    if not query:
                        return [TextContent(type="text", text="Error: query is required")]
                    
                    filter_expr = arguments.get("filter")
                    top = arguments.get("top", 10)
                    
                    products = await self.product_client.search_products(query, filter_expr, top)
                    if products:
                        return [TextContent(
                            type="text",
                            text=self._format_products_list(products)
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"No products found for query: '{query}'"
                        )]
                
                elif name == "get_categories":
                    categories = await self.product_client.get_categories()
                    if categories:
                        return [TextContent(
                            type="text",
                            text=f"Available categories: {', '.join(categories)}"
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text="No categories available"
                        )]
                
                elif name == "get_products_by_category":
                    category = arguments.get("category")
                    if not category:
                        return [TextContent(type="text", text="Error: category is required")]
                    
                    limit = arguments.get("limit", 10)
                    products = await self.product_client.get_products_by_category(category, limit)
                    if products:
                        return [TextContent(
                            type="text",
                            text=self._format_products_list(products)
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"No products found in category: '{category}'"
                        )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            
            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing tool '{name}': {str(e)}"
                )]
    
    def _format_product_info(self, product: ProductInfo) -> str:
        """Format product information for display"""
        info = f"""Product Information:
ID: {product.id}
Name: {product.name}
Description: {product.description}
Price: ${product.price:.2f}
Category: {product.category}
Stock Quantity: {product.stock_quantity}"""
        
        if product.image_url:
            info += f"\nImage URL: {product.image_url}"
        
        if product.specifications:
            info += "\nSpecifications:"
            for key, value in product.specifications.items():
                info += f"\n  {key}: {value}"
        
        return info
    
    def _format_products_list(self, products: List[ProductInfo]) -> str:
        """Format a list of products for display"""
        if not products:
            return "No products found."
        
        result = f"Found {len(products)} product(s):\n\n"
        for i, product in enumerate(products, 1):
            result += f"{i}. {product.name} (ID: {product.id})\n"
            result += f"   Price: ${product.price:.2f} | Category: {product.category}\n"
            result += f"   Stock: {product.stock_quantity} | {product.description[:100]}...\n\n"
        
        return result
    
    async def run(self):
        """Run the MCP server"""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="product-info-server",
                        server_version="1.0.0",
                        capabilities={}
                    )
                )
        finally:
            await self.product_client.close()

async def main():
    """Main entry point"""
    # Get configuration based on environment
    config = get_config()
    
    # Set up logging based on configuration
    setup_logging(config)
    
    # Create and run server
    server = ProductMCPServer(config)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

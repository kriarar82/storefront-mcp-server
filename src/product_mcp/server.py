#!/usr/bin/env python3
"""
Generic MCP Server
Communicates with any microservice to provide data to AI agents through configurable tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import httpx
import time

# Optional semantic search imports
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    logging.warning("Semantic search dependencies not available. Install sentence-transformers, numpy, and scikit-learn to enable semantic search.")
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

from .config import ServerConfig, DEFAULT_CONFIG, Environment, RequestMapping
from .config_utils import get_config, validate_config, setup_logging, get_environment_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceData:
    """Generic data class for service responses"""
    id: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class SemanticSearchCache:
    """Simple in-memory cache for semantic search results"""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result if not expired"""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache a result with current timestamp"""
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cached results"""
        self.cache.clear()

class GenericAPIClient:
    """Generic HTTP client for making API requests to the microservice"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.base_url = config.service_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=config.generic_api.default_timeout)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def make_request(self, mapping: 'RequestMapping', params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a generic HTTP request based on mapping configuration"""
        try:
            # Build URL
            url = self.base_url + mapping.endpoint
            
            # Replace path parameters
            for param in mapping.required_params + mapping.optional_params:
                if param in params:
                    url = url.replace(f"{{{param}}}", str(params[param]))
            
            # Prepare request data
            request_kwargs = {}
            
            if mapping.method.upper() == "GET":
                # For GET requests, add optional params as query parameters
                query_params = {}
                for param in mapping.optional_params:
                    if param in params:
                        query_params[param] = params[param]
                if query_params:
                    request_kwargs["params"] = query_params
            else:
                # For POST/PUT/DELETE requests, send data in body
                body_data = {}
                for param in mapping.required_params + mapping.optional_params:
                    if param in params:
                        body_data[param] = params[param]
                if body_data:
                    request_kwargs["json"] = body_data
            
            # Log request if enabled
            if self.config.generic_api.enable_request_logging:
                logger.info(f"Making {mapping.method} request to {url} with params: {params}")
            
            # Make the request
            response = await self.client.request(
                method=mapping.method,
                url=url,
                **request_kwargs
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Log response if enabled
            if self.config.generic_api.enable_response_logging:
                logger.info(f"Response from {url}: {response.status_code}")
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": True
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in request to {mapping.endpoint}: {e}")
            return {
                "status_code": getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500,
                "error": str(e),
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in request to {mapping.endpoint}: {e}")
            return {
                "status_code": 500,
                "error": str(e),
                "success": False
            }

class GenericServiceClient:
    """Generic client for communicating with any microservice"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.base_url = config.service_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=config.service_timeout)
        
        # Initialize semantic search components (optional)
        self.semantic_model = None
        self.data_embeddings = {}
        self.semantic_cache = None
        
        if SEMANTIC_SEARCH_AVAILABLE and config.semantic_search.enable_caching:
            self.semantic_cache = SemanticSearchCache(config.semantic_search.cache_ttl)
        
        # Initialize generic API client
        self.generic_client = GenericAPIClient(config)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        await self.generic_client.close()
    
    def _parse_response(self, response_data: Dict[str, Any], parser_name: Optional[str] = None) -> List[ServiceData]:
        """Parse response data using the specified parser"""
        if not response_data.get("success", False):
            return []
        
        data = response_data.get("data", {})
        
        if parser_name == "parse_item":
            return [self._parse_item(data)] if self._parse_item(data) else []
        elif parser_name == "parse_categories":
            return data.get("categories", [])
        elif parser_name == "parse_items_list":
            items = []
            for item in data.get("items", []):
                parsed_item = self._parse_item(item)
                if parsed_item:
                    items.append(parsed_item)
            return items
        else:
            # Default parsing - try to extract items
            items = []
            if isinstance(data, list):
                for item in data:
                    parsed_item = self._parse_item(item)
                    if parsed_item:
                        items.append(parsed_item)
            elif isinstance(data, dict) and "items" in data:
                for item in data.get("items", []):
                    parsed_item = self._parse_item(item)
                    if parsed_item:
                        items.append(parsed_item)
            return items
    
    async def generic_api_request(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a generic API request using the configured mapping"""
        if not self.config.generic_api.enable_generic_api:
            return {
                "success": False,
                "error": "Generic API is disabled",
                "status_code": 400
            }
        
        # Get the mapping for this tool
        mapping = self.config.generic_api.request_mappings.get(tool_name)
        if not mapping:
            return {
                "success": False,
                "error": f"No mapping found for tool: {tool_name}",
                "status_code": 400
            }
        
        # Validate required parameters
        missing_params = []
        for param in mapping.required_params:
            if param not in params:
                missing_params.append(param)
        
        if missing_params:
            return {
                "success": False,
                "error": f"Missing required parameters: {', '.join(missing_params)}",
                "status_code": 400
            }
        
        # Make the request
        response = await self.generic_client.make_request(mapping, params)
        
        # Parse response if parser is specified
        if mapping.response_parser and response.get("success"):
            try:
                parsed_data = self._parse_response(response, mapping.response_parser)
                response["parsed_data"] = parsed_data
            except Exception as e:
                logger.error(f"Error parsing response for {tool_name}: {e}")
                response["parse_error"] = str(e)
        
        return response
    
    def _parse_item(self, data: Dict[str, Any]) -> Optional[ServiceData]:
        """Parse item data from the microservice response"""
        try:
            # Generic parsing - extract ID and store all data
            item_id = data.get("id") or data.get("item_id") or str(data.get("_id", ""))
            if not item_id:
                return None
            
            return ServiceData(
                id=str(item_id),
                data=data,
                metadata={
                    "parsed_at": time.time(),
                    "source": "microservice"
                }
            )
        except Exception as e:
            logger.error(f"Error parsing item data: {e}")
            return None
    

class GenericMCPServer:
    """Generic MCP Server for any microservice"""
    
    def __init__(self, config: ServerConfig = None):
        if config is None:
            config = DEFAULT_CONFIG
        
        # Validate configuration
        if not validate_config(config):
            raise ValueError("Invalid configuration provided")
        
        self.config = config
        self.server = Server(config.server_name)
        self.service_client = GenericServiceClient(config)
        self._setup_handlers()
        
        # Log environment info
        env_info = get_environment_info(config)
        logger.info(f"Starting generic MCP server with configuration: {env_info}")
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            # Get tools from configuration mappings
            tools = []
            
            # Add configured tools
            for tool_name, mapping in self.config.generic_api.request_mappings.items():
                if tool_name == "generic_request":
                    continue  # Skip the generic request tool, we'll add it separately
                
                # Build input schema from mapping
                properties = {}
                for param in mapping.required_params:
                    param_type = "string"  # default
                    if hasattr(mapping, 'param_types') and mapping.param_types and param in mapping.param_types:
                        param_type = mapping.param_types[param]
                    properties[param] = {
                        "type": param_type,
                        "description": f"Required parameter: {param}"
                    }
                for param in mapping.optional_params:
                    param_type = "string"  # default
                    if hasattr(mapping, 'param_types') and mapping.param_types and param in mapping.param_types:
                        param_type = mapping.param_types[param]
                    properties[param] = {
                        "type": param_type,
                        "description": f"Optional parameter: {param}"
                    }
                
                tools.append(Tool(
                    name=tool_name,
                    description=mapping.description,
                    inputSchema={
                        "type": "object",
                        "properties": properties,
                        "required": mapping.required_params
                    }
                ))
            
            # Add generic API tool
            tools.append(Tool(
                name="generic_api",
                description="Generic API request passthrough to the microservice. Supports any HTTP method and endpoint.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "API endpoint path (e.g., 'items/search', 'categories')"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE"],
                            "description": "HTTP method to use",
                            "default": "POST"
                        },
                        "body": {
                            "type": "object",
                            "description": "Request body data (for POST/PUT requests)"
                        },
                        "params": {
                            "type": "object",
                            "description": "Query parameters (for GET requests)"
                        },
                        "headers": {
                            "type": "object",
                            "description": "Additional HTTP headers"
                        }
                    },
                    "required": ["path"]
                }
            ))
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                # Check if it's a configured tool
                if name in self.config.generic_api.request_mappings:
                    response = await self.service_client.generic_api_request(name, arguments)
                    
                    if response.get("success"):
                        if "parsed_data" in response and response["parsed_data"]:
                            return [TextContent(
                                type="text",
                                text=self._format_service_data(response["parsed_data"])
                            )]
                        else:
                            return [TextContent(
                                type="text",
                                text=f"API Response (Status: {response.get('status_code')}):\n{json.dumps(response.get('data', {}), indent=2)}"
                            )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"API Error (Status: {response.get('status_code')}): {response.get('error', 'Unknown error')}"
                        )]
                
                elif name == "generic_api":
                    path = arguments.get("path")
                    if not path:
                        return [TextContent(type="text", text="Error: path is required")]
                    
                    # Create a custom mapping for this request
                    custom_mapping = RequestMapping(
                        endpoint=f"/api/{path}",
                        method=arguments.get("method", "POST"),
                        description="Generic API request",
                        required_params=[],
                        optional_params=list(arguments.keys())
                    )
                    
                    # Make the request using the generic client
                    response = await self.service_client.generic_client.make_request(custom_mapping, arguments)
                    
                    if response.get("success"):
                        return [TextContent(
                            type="text",
                            text=f"API Response (Status: {response.get('status_code')}):\n{json.dumps(response.get('data', {}), indent=2)}"
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"API Error (Status: {response.get('status_code')}): {response.get('error', 'Unknown error')}"
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
    
    def _format_service_data(self, data: List[ServiceData]) -> str:
        """Format service data for display"""
        if not data:
            return "No data found"
        
        if len(data) == 1:
            # Single item
            item = data[0]
            info = f"Service Data:\nID: {item.id}\n"
            
            # Format the data dictionary
            for key, value in item.data.items():
                if isinstance(value, (dict, list)):
                    info += f"{key}: {json.dumps(value, indent=2)}\n"
                else:
                    info += f"{key}: {value}\n"
            
            if item.metadata:
                info += f"\nMetadata: {json.dumps(item.metadata, indent=2)}"
            
            return info
        else:
            # Multiple items
            info = f"Found {len(data)} item(s):\n\n"
            for i, item in enumerate(data, 1):
                info += f"{i}. ID: {item.id}\n"
                # Show first few fields
                for key, value in list(item.data.items())[:3]:
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value)[:50] + "..." if len(json.dumps(value)) > 50 else json.dumps(value)
                    else:
                        value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    info += f"   {key}: {value_str}\n"
                info += "\n"
            
            return info
    
    async def run(self):
        """Run the MCP server"""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config.server_name,
                        server_version=self.config.server_version,
                        capabilities={}
                    )
                )
        finally:
            await self.service_client.close()

async def main():
    """Main entry point"""
    # Get configuration based on environment
    config = get_config()
    
    # Set up logging based on configuration
    setup_logging(config)
    
    # Create and run server
    server = GenericMCPServer(config)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

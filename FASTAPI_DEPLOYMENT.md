# FastAPI Deployment for MCP Server

## Overview

The MCP Server has been successfully deployed with FastAPI, exposing all MCP tools as REST API endpoints. This allows the MCP functionality to be accessed via HTTP instead of just stdio communication.

## Deployment Information

- **Service URL**: https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io
- **Environment**: Production
- **Container App**: storefront-mcp-server
- **Resource Group**: mcp-storefront-rg
- **Container Registry**: mcpstorefrontacr.azurecr.io

## Available Endpoints

### Health & Information
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with service information
- `GET /api/tools` - List all available MCP tools

### MCP Tools (REST API)
- `GET /api/tools/search_products` - Search products (GET)
- `POST /api/tools/search_products` - Search products (POST)
- `GET /api/tools/get_categories` - Get all categories
- `GET /api/tools/get_products_by_category` - Get products by category
- `GET /api/tools/get_product/{product_id}` - Get specific product

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Example Usage

### Search Products
```bash
# GET request
curl "https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io/api/tools/search_products?query=laptop&limit=5"

# POST request
curl -X POST "https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io/api/tools/search_products" \
  -H "Content-Type: application/json" \
  -d '{"query": "phone", "limit": 3}'
```

### Get Categories
```bash
curl "https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io/api/tools/get_categories"
```

### Get Products by Category
```bash
curl "https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io/api/tools/get_products_by_category?category=Electronics&limit=5"
```

### Get Specific Product
```bash
curl "https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io/api/tools/get_product/1"
```

## Response Format

All endpoints return JSON responses with the following structure:

```json
{
  "success": true,
  "query": "laptop",
  "limit": 5,
  "result": []
}
```

## Testing

### Python Test Script
```bash
python test_fastapi_endpoints.py
```

### Curl Test Script
```bash
./test_fastapi_curl.sh
```

## Architecture

```
Client → HTTP Request → FastAPI Server → MCP Server → Product Service Client → Azure Microservice
```

## Benefits

1. **HTTP Access**: MCP tools are now accessible via standard HTTP REST API
2. **Documentation**: Auto-generated Swagger/OpenAPI documentation
3. **Multiple Formats**: Support for both GET and POST requests
4. **Health Monitoring**: Built-in health check endpoints
5. **Production Ready**: Deployed on Azure Container Apps with proper monitoring

## Configuration

The FastAPI server uses the same configuration system as the MCP server:
- Environment-based configuration
- Production settings loaded from `config/env.production`
- Connects to Azure product service at `https://product-service.niceplant-d75cfbd0.eastus.azurecontainerapps.io`

## Monitoring

- Health checks: `/health`
- Container logs: `az containerapp logs show --name storefront-mcp-server --resource-group mcp-storefront-rg --follow`
- Container status: `az containerapp show --name storefront-mcp-server --resource-group mcp-storefront-rg`

# MCP Server Deployment Guide

This guide covers deploying the MCP (Model Context Protocol) server to Azure Container Apps and local Docker environments.

## 🏗️ Architecture

The MCP server is containerized and can be deployed in two ways:
1. **Local Development**: Using Docker Compose with a mock Java microservice
2. **Azure Container Apps**: Production deployment on Azure

## 📁 Directory Structure

```
deployment/
├── azure/
│   ├── container-app.yaml      # Kubernetes-style deployment config
│   ├── containerapp.yaml       # Azure Container Apps config
│   └── deploy.sh              # Azure deployment script
├── local/
│   └── test-local.sh          # Local testing script
└── README.md                  # This file
```

## 🚀 Local Development

### Prerequisites
- Docker
- Docker Compose

### Quick Start

1. **Build and test locally:**
   ```bash
   ./deployment/local/test-local.sh
   ```

2. **Manual Docker Compose:**
   ```bash
   # Build and start services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f mcp-server
   
   # Stop services
   docker-compose down
   ```

### Local Services

- **MCP Server**: `mcp-server` service
- **Mock Java Microservice**: `java-microservice` service (MockServer)
- **Network**: `mcp-network`

## ☁️ Azure Container Apps Deployment

### Prerequisites
- Azure CLI installed and logged in
- Azure subscription with Container Apps enabled
- Docker (for building images)

### Quick Deployment

1. **Run the deployment script:**
   ```bash
   ./deployment/azure/deploy.sh
   ```

2. **Manual deployment steps:**
   ```bash
   # Set variables
   RESOURCE_GROUP="mcp-storefront-rg"
   LOCATION="eastus"
   CONTAINER_REGISTRY="mcpstorefrontacr"
   
   # Create resource group
   az group create --name $RESOURCE_GROUP --location $LOCATION
   
   # Create container registry
   az acr create --resource-group $RESOURCE_GROUP --name $CONTAINER_REGISTRY --sku Basic --admin-enabled true
   
   # Build and push image
   az acr build --registry $CONTAINER_REGISTRY --image mcp-server:latest --file Dockerfile .
   
   # Create container app environment
   az containerapp env create --name mcp-storefront-env --resource-group $RESOURCE_GROUP --location $LOCATION
   
   # Deploy container app
   az containerapp create \
     --name mcp-server \
     --resource-group $RESOURCE_GROUP \
     --environment mcp-storefront-env \
     --image $CONTAINER_REGISTRY.azurecr.io/mcp-server:latest \
     --target-port 8080 \
     --ingress internal \
     --cpu 0.5 \
     --memory 1Gi
   ```

### Azure Resources Created

- **Resource Group**: `mcp-storefront-rg`
- **Container Registry**: `mcpstorefrontacr.azurecr.io`
- **Container Apps Environment**: `mcp-storefront-env`
- **Container App**: `mcp-server`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PRODUCT_SERVICE_URL` | Java microservice URL | `http://java-microservice:8080` |
| `PRODUCT_SERVICE_TIMEOUT` | HTTP timeout in seconds | `30` |
| `MCP_SERVER_NAME` | MCP server name | `product-info-server` |
| `MCP_SERVER_VERSION` | Server version | `1.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Resource Requirements

- **CPU**: 0.5 cores
- **Memory**: 1GB
- **Replicas**: 1-10 (auto-scaling)

## 📊 Monitoring and Logs

### Azure Container Apps

```bash
# View logs
az containerapp logs show --name mcp-server --resource-group mcp-storefront-rg --follow

# Check status
az containerapp show --name mcp-server --resource-group mcp-storefront-rg

# Scale app
az containerapp update --name mcp-server --resource-group mcp-storefront-rg --min-replicas 2 --max-replicas 5
```

### Local Docker

```bash
# View logs
docker-compose logs -f mcp-server

# Check status
docker-compose ps

# Scale service
docker-compose up -d --scale mcp-server=3
```

## 🧪 Testing

### Health Checks

The container includes health checks that verify:
1. Python environment is working
2. MCP server can import modules
3. Connection to Java microservice is possible

### Manual Testing

```bash
# Test MCP server directly
docker-compose exec mcp-server python -c "
import asyncio
import sys
sys.path.insert(0, '/app/src')
from product_mcp.server import ProductServiceClient

async def test():
    client = ProductServiceClient('http://java-microservice:1080')
    products = await client.search_products('laptop', top=5)
    print(f'Found {len(products)} products')
    await client.close()

asyncio.run(test())
"
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Azure Container Apps

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy to Azure Container Apps
      run: ./deployment/azure/deploy.sh
```

## 🛠️ Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check environment variables
   - Verify Java microservice is accessible
   - Review container logs

2. **Health checks failing**
   - Ensure Python dependencies are installed
   - Check network connectivity
   - Verify MCP server configuration

3. **Azure deployment issues**
   - Verify Azure CLI is logged in
   - Check resource group permissions
   - Ensure Container Apps is enabled in subscription

### Debug Commands

```bash
# Check container logs
docker logs <container-id>

# Inspect container
docker inspect <container-id>

# Execute shell in container
docker exec -it <container-id> /bin/bash

# Check Azure Container App logs
az containerapp logs show --name mcp-server --resource-group mcp-storefront-rg --follow
```

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)






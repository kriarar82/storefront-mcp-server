#!/bin/bash

# Pre-deployment validation script for Azure Container Apps
# This script validates the configuration and environment before deployment

set -e

echo "🔍 Pre-deployment validation for Azure Container Apps"
echo "=" * 50

# Configuration
RESOURCE_GROUP="mcp-storefront-rg"
LOCATION="eastus"
CONTAINER_REGISTRY="mcpstorefrontacr"
CONTAINER_APP_ENVIRONMENT="mcp-storefront-env"
CONTAINER_APP_NAME="storefront-mcp-server"
ENVIRONMENT="production"
CONFIG_FILE="config/env.${ENVIRONMENT}"

echo "📋 Deployment Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Container Registry: $CONTAINER_REGISTRY"
echo "   Container App: $CONTAINER_APP_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Config File: $CONFIG_FILE"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file $CONFIG_FILE not found!"
    exit 1
fi
echo "✅ Configuration file found: $CONFIG_FILE"

# Load configuration
echo "📖 Loading configuration..."
set -a
source "$CONFIG_FILE"
set +a

# Validate required environment variables
echo "🔍 Validating configuration..."

required_vars=(
    "ENVIRONMENT"
    "PRODUCT_SERVICE_URL"
    "MCP_SERVER_NAME"
    "MCP_SERVER_VERSION"
    "LOG_LEVEL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set!"
        exit 1
    fi
    echo "✅ $var: ${!var}"
done

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed!"
    exit 1
fi
echo "✅ Azure CLI is installed"

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi
echo "✅ Logged in to Azure"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    exit 1
fi
echo "✅ Docker is available"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found!"
    exit 1
fi
echo "✅ Dockerfile found"

# Test configuration with Python
echo "🐍 Testing configuration with Python..."
if python -c "
import sys
sys.path.insert(0, 'src')
from product_mcp.config_utils import get_config, validate_config
config = get_config('production')
if not validate_config(config):
    print('❌ Configuration validation failed!')
    sys.exit(1)
print('✅ Configuration validation passed!')
" 2>/dev/null; then
    echo "✅ Python configuration test passed"
else
    echo "❌ Python configuration test failed!"
    exit 1
fi

# Check if resource group exists or can be created
echo "🔍 Checking resource group..."
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "✅ Resource group $RESOURCE_GROUP exists"
else
    echo "⚠️  Resource group $RESOURCE_GROUP will be created"
fi

# Check if container registry exists
echo "🔍 Checking container registry..."
if az acr show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "✅ Container registry $CONTAINER_REGISTRY exists"
else
    echo "⚠️  Container registry $CONTAINER_REGISTRY will be created"
fi

# Check if container app environment exists
echo "🔍 Checking container app environment..."
if az containerapp env show --name $CONTAINER_APP_ENVIRONMENT --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "✅ Container app environment $CONTAINER_APP_ENVIRONMENT exists"
else
    echo "⚠️  Container app environment $CONTAINER_APP_ENVIRONMENT will be created"
fi

# Check if container app already exists
echo "🔍 Checking if container app already exists..."
if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "⚠️  Container app $CONTAINER_APP_NAME already exists - will be updated"
else
    echo "✅ Container app $CONTAINER_APP_NAME will be created"
fi

echo ""
echo "🎉 Pre-deployment validation completed successfully!"
echo ""
echo "📋 Summary:"
echo "   ✅ All required files and configurations are present"
echo "   ✅ Azure CLI is ready"
echo "   ✅ Configuration validation passed"
echo "   ✅ Ready for deployment"
echo ""
echo "🚀 To deploy, run:"
echo "   ./deployment/azure/deploy.sh"
echo ""

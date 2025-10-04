#!/bin/bash

# Azure Container Apps Deployment Script
# This script builds and deploys the MCP server to Azure Container Apps

set -e

# Configuration
RESOURCE_GROUP="mcp-storefront-rg"
LOCATION="eastus"
CONTAINER_REGISTRY="mcpstorefrontacr"
CONTAINER_APP_ENVIRONMENT="mcp-storefront-env"
CONTAINER_APP_NAME="storefront-mcp-server"
IMAGE_NAME="storefront-mcp-server"
IMAGE_TAG="latest"

# Environment configuration
ENVIRONMENT=${ENVIRONMENT:-production}
CONFIG_FILE="config/env.${ENVIRONMENT}"

echo "🚀 Starting Azure Container Apps deployment..."
echo "📋 Environment: $ENVIRONMENT"
echo "📁 Config file: $CONFIG_FILE"

# Load environment variables from config file if it exists
if [ -f "$CONFIG_FILE" ]; then
    echo "📖 Loading configuration from $CONFIG_FILE"
    set -a  # automatically export all variables
    source "$CONFIG_FILE"
    set +a
else
    echo "⚠️  Configuration file $CONFIG_FILE not found, using defaults"
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Create resource group if it doesn't exist
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Create Azure Container Registry if it doesn't exist
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_REGISTRY \
    --sku Basic \
    --admin-enabled true \
    --output table

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Build and push Docker image
echo "🔨 Building and pushing Docker image..."
az acr build \
    --registry $CONTAINER_REGISTRY \
    --image $IMAGE_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

# Create Container Apps environment if it doesn't exist
echo "🌍 Creating Container Apps environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# Create Container App
echo "🚀 Creating Container App..."
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENVIRONMENT \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
    --target-port 8000 \
    --ingress external \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars \
        ENVIRONMENT=${ENVIRONMENT:-production} \
        PRODUCT_SERVICE_URL=${PRODUCT_SERVICE_URL:-https://product-service.niceplant-d75cfbd0.eastus.azurecontainerapps.io} \
        PRODUCT_SERVICE_TIMEOUT=${PRODUCT_SERVICE_TIMEOUT:-60} \
        MCP_SERVER_NAME=${MCP_SERVER_NAME:-product-info-server} \
        MCP_SERVER_VERSION=${MCP_SERVER_VERSION:-1.0.0} \
        LOG_LEVEL=${LOG_LEVEL:-INFO} \
        DEBUG=${DEBUG:-false} \
        ENABLE_CORS=${ENABLE_CORS:-false} \
        CORS_ORIGINS=${CORS_ORIGINS:-} \
        SECRET_KEY=${SECRET_KEY:-your-secret-key-here} \
        ALLOWED_HOSTS=${ALLOWED_HOSTS:-your-domain.com,api.your-domain.com} \
        MAX_CONNECTIONS=${MAX_CONNECTIONS:-100} \
        CONNECTION_POOL_SIZE=${CONNECTION_POOL_SIZE:-20} \
        HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-60} \
        METRICS_ENABLED=${METRICS_ENABLED:-true} \
        SENTRY_DSN=${SENTRY_DSN:-your-sentry-dsn-here} \
    --cpu 0.5 \
    --memory 1Gi \
    --min-replicas 1 \
    --max-replicas 10 \
    --output table

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Deployment Information:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container Registry: $CONTAINER_REGISTRY"
echo "   Container App: $CONTAINER_APP_NAME"
echo "   Environment: $CONTAINER_APP_ENVIRONMENT"
echo ""
echo "🔍 To check the status:"
echo "   az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "📊 To view logs:"
echo "   az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"




# Product Information MCP Server

An MCP (Model Context Protocol) server that provides product information by communicating with a Java microservice. This server allows AI agents to query product data through a standardized interface.

## Features

- **Get Product Details**: Retrieve detailed information about a specific product by ID
- **Search Products**: Search for products by name, description, or other criteria
- **Category Management**: Get available categories and filter products by category
- **Async Communication**: Non-blocking communication with the Java microservice
- **Error Handling**: Robust error handling and logging
- **Configurable**: Environment-based configuration

## Prerequisites

- Python 3.8 or higher
- Java microservice running and accessible
- MCP client (AI agent) that can communicate with MCP servers

## Installation

### Option 1: Using pip (recommended)

```bash
# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Option 2: Manual installation

1. Clone or download this repository
2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the server (optional):

```bash
cp env.example .env
# Edit .env with your configuration
```

## Configuration

The server can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRODUCT_SERVICE_URL` | `http://localhost:8080` | URL of the Java microservice |
| `PRODUCT_SERVICE_TIMEOUT` | `30` | Timeout for HTTP requests in seconds |
| `MCP_SERVER_NAME` | `product-info-server` | Name of the MCP server |
| `MCP_SERVER_VERSION` | `1.0.0` | Version of the MCP server |
| `LOG_LEVEL` | `INFO` | Logging level |

## Usage

### Running the Server

#### Option 1: Using the CLI (recommended)

```bash
# Start the server
python -m src.product_mcp.cli server

# Start with custom configuration
python -m src.product_mcp.cli server --url http://localhost:9000 --log-level DEBUG

# Run tests
python -m src.product_mcp.cli test
```

#### Option 2: Using convenience scripts

```bash
# Using the run script
python run_server.py

# Using the activation script
./activate.sh
python run_server.py
```

#### Option 3: Direct module execution

```bash
python -m src.product_mcp.server
```

The server will start and listen for MCP protocol messages via stdio.

### Available Tools

The server provides the following tools to AI agents:

#### 1. `get_product`
Get detailed information about a specific product.

**Parameters:**
- `product_id` (string, required): The unique identifier of the product

**Example:**
```json
{
  "name": "get_product",
  "arguments": {
    "product_id": "12345"
  }
}
```

#### 2. `search_products`
Search for products by name, description, or other criteria.

**Parameters:**
- `query` (string, required): Search query for products
- `category` (string, optional): Category filter
- `limit` (integer, optional): Maximum number of products to return (default: 10)

**Example:**
```json
{
  "name": "search_products",
  "arguments": {
    "query": "laptop",
    "category": "electronics",
    "limit": 5
  }
}
```

#### 3. `get_categories`
Get all available product categories.

**Parameters:** None

**Example:**
```json
{
  "name": "get_categories",
  "arguments": {}
}
```

#### 4. `get_products_by_category`
Get products filtered by a specific category.

**Parameters:**
- `category` (string, required): The category to filter by
- `limit` (integer, optional): Maximum number of products to return (default: 10)

**Example:**
```json
{
  "name": "get_products_by_category",
  "arguments": {
    "category": "electronics",
    "limit": 20
  }
}
```

## Java Microservice API

The MCP server expects the Java microservice to provide the following REST endpoints:

### GET /api/products/{id}
Get a single product by ID.

**Response:**
```json
{
  "id": "12345",
  "name": "Product Name",
  "description": "Product description",
  "price": 99.99,
  "category": "electronics",
  "stockQuantity": 10,
  "imageUrl": "https://example.com/image.jpg",
  "specifications": {
    "color": "black",
    "weight": "1.5kg"
  }
}
```

### GET /api/products/search
Search for products.

**Query Parameters:**
- `q`: Search query
- `category`: Optional category filter
- `limit`: Maximum number of results

**Response:**
```json
{
  "products": [
    {
      "id": "12345",
      "name": "Product Name",
      "description": "Product description",
      "price": 99.99,
      "category": "electronics",
      "stockQuantity": 10,
      "imageUrl": "https://example.com/image.jpg",
      "specifications": {}
    }
  ]
}
```

### GET /api/products/categories
Get all available categories.

**Response:**
```json
{
  "categories": ["electronics", "clothing", "books"]
}
```

### GET /api/products/category/{category}
Get products by category.

**Query Parameters:**
- `limit`: Maximum number of results

**Response:**
```json
{
  "products": [
    {
      "id": "12345",
      "name": "Product Name",
      "description": "Product description",
      "price": 99.99,
      "category": "electronics",
      "stockQuantity": 10,
      "imageUrl": "https://example.com/image.jpg",
      "specifications": {}
    }
  ]
}
```

## Testing

You can test the MCP server using several methods:

### Option 1: Using the CLI

```bash
python -m src.product_mcp.cli test
```

### Option 2: Direct test client

```bash
python -m src.product_mcp.test_client
```

### Option 3: Using pytest (if installed)

```bash
pytest src/product_mcp/
```

## Error Handling

The server includes comprehensive error handling:

- **HTTP Errors**: Network and HTTP errors are caught and logged
- **Data Parsing**: Invalid JSON responses are handled gracefully
- **Missing Data**: Missing required fields are handled with appropriate error messages
- **Timeouts**: Request timeouts are configured and handled

## Logging

The server uses Python's built-in logging module. Log levels can be configured via the `LOG_LEVEL` environment variable.

## Development

### Project Structure

```
Storefront-MCP/
├── src/
│   └── product_mcp/
│       ├── __init__.py       # Package initialization
│       ├── server.py          # Main MCP server implementation
│       ├── config.py          # Configuration management
│       ├── test_client.py     # Test client for the MCP server
│       └── cli.py             # Command line interface
├── venv/                     # Virtual environment (created locally)
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup script
├── pyproject.toml           # Modern Python packaging configuration
├── env.example              # Environment variables template
├── run_server.py            # Convenience script to run the server
├── activate.sh              # Virtual environment activation script
└── README.md                # This file
```

### Adding New Tools

To add new tools to the MCP server:

1. Add the tool definition in the `handle_list_tools()` function
2. Add the tool handler in the `handle_call_tool()` function
3. Implement the corresponding method in the `ProductServiceClient` class
4. Update the Java microservice to support the new endpoint

## License

This project is provided as-is for demonstration purposes.

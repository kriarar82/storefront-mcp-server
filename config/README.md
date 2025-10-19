# Tool Mappings Configuration

This directory contains configuration files for mapping MCP tools to microservice API endpoints.

## Files

- `tool_mappings.yaml` - YAML format mappings (recommended)
- `tool_mappings.json` - JSON format mappings
- `tool_mappings.properties` - Properties format mappings (simple)
- `example_mappings.yaml` - Example mappings for different use cases
- `env.development` - Development environment variables
- `env.production` - Production environment variables

## Tool Mappings Format

### YAML Format (Recommended)

```yaml
mappings:
  tool_name:
    endpoint: "/api/path/{param}"
    method: "GET|POST|PUT|DELETE"
    description: "Human readable description"
    required_params: ["param1", "param2"]
    optional_params: ["param3", "param4"]
    response_parser: "parser_name"

response_parsers:
  parser_name:
    type: "single_item|list"
    id_field: "field_name"
    data_fields: ["field1", "field2"]
    list_field: "field_name"  # for list type
    item_fields: ["field1", "field2"]  # for list type
```

### JSON Format

```json
{
  "mappings": {
    "tool_name": {
      "endpoint": "/api/path/{param}",
      "method": "GET",
      "description": "Human readable description",
      "required_params": ["param1"],
      "optional_params": ["param2"],
      "response_parser": "parser_name"
    }
  },
  "response_parsers": {
    "parser_name": {
      "type": "single_item",
      "id_field": "id",
      "data_fields": ["name", "description"]
    }
  }
}
```

### Properties Format (Simple)

```properties
# Tool configuration
tool_name.endpoint=/api/path/{param}
tool_name.method=GET
tool_name.description=Human readable description
tool_name.required_params=param1,param2
tool_name.optional_params=param3,param4
tool_name.response_parser=parser_name
```

**Note**: Properties format doesn't support response parser configuration. Use YAML or JSON for complex configurations.

## Configuration Options

### Tool Mapping Fields

- **endpoint**: API endpoint pattern with `{param}` placeholders
- **method**: HTTP method (GET, POST, PUT, DELETE)
- **description**: Tool description shown to AI agents
- **required_params**: Parameters that must be provided
- **optional_params**: Parameters that are optional
- **response_parser**: Parser to use for response processing

### Response Parser Types

#### Single Item Parser
```yaml
parse_item:
  type: "single_item"
  id_field: "id"  # Field containing the item ID
  data_fields: ["name", "description", "price"]  # Fields to include
```

#### List Parser
```yaml
parse_items_list:
  type: "list"
  list_field: "items"  # Field containing the list
  item_fields: ["id", "name", "price"]  # Fields for each item
```

## Examples

### E-commerce API
```yaml
mappings:
  get_product:
    endpoint: "/api/products/{product_id}"
    method: "GET"
    description: "Get product details by ID"
    required_params: ["product_id"]
    response_parser: "parse_product"

  search_products:
    endpoint: "/api/products/search"
    method: "POST"
    description: "Search products with filters"
    required_params: ["query"]
    optional_params: ["category", "price_min", "price_max"]
    response_parser: "parse_products_list"
```

### User Management API
```yaml
mappings:
  get_user:
    endpoint: "/api/users/{user_id}"
    method: "GET"
    description: "Get user profile"
    required_params: ["user_id"]
    optional_params: ["include_permissions"]
    response_parser: "parse_user"

  create_user:
    endpoint: "/api/users"
    method: "POST"
    description: "Create new user"
    required_params: ["username", "email"]
    optional_params: ["first_name", "last_name", "role"]
    response_parser: "parse_user"
```

## Environment Variables

The server will automatically load mappings from:
1. `config/tool_mappings.yaml` (if exists)
2. `config/tool_mappings.json` (if exists)
3. Default hardcoded mappings (fallback)

You can also specify a custom mappings file via environment variable:
```bash
export MAPPINGS_FILE="/path/to/custom_mappings.yaml"
```

## Adding New Tools

1. Add the tool mapping to `tool_mappings.yaml`
2. Define a response parser if needed
3. Restart the MCP server
4. The new tool will be automatically available

## Parameter Substitution

URL parameters are automatically substituted:
- `{id}` → value from `id` parameter
- `{user_id}` → value from `user_id` parameter
- `{category}` → value from `category` parameter

Example:
```yaml
endpoint: "/api/users/{user_id}/orders/{order_id}"
# With params: {"user_id": "123", "order_id": "456"}
# Results in: "/api/users/123/orders/456"
```

## Error Handling

- Missing required parameters will return an error
- Invalid HTTP methods will return an error
- Malformed mapping files will fall back to defaults
- Missing response parsers will use generic parsing

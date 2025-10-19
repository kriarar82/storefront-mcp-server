#!/usr/bin/env python3
"""
Tool Mapping Loader
Loads tool-to-URL mappings from external configuration files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from .config import RequestMapping

logger = logging.getLogger(__name__)

class MappingLoader:
    """Loads tool mappings from external configuration files"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.mappings_file = None
        self.response_parsers = {}
    
    def load_mappings(self, mappings_file: Optional[str] = None) -> Dict[str, RequestMapping]:
        """Load tool mappings from configuration file"""
        if mappings_file:
            self.mappings_file = Path(mappings_file)
        else:
            # Check environment variable first
            env_mappings_file = os.getenv("MAPPINGS_FILE")
            if env_mappings_file:
                self.mappings_file = Path(env_mappings_file)
            else:
                # Try to find mappings file in config directory
                yaml_file = self.config_dir / "tool_mappings.yaml"
                json_file = self.config_dir / "tool_mappings.json"
                properties_file = self.config_dir / "tool_mappings.properties"
                
                if yaml_file.exists():
                    self.mappings_file = yaml_file
                elif json_file.exists():
                    self.mappings_file = json_file
                elif properties_file.exists():
                    self.mappings_file = properties_file
                else:
                    logger.warning("No mappings file found, using default mappings")
                    return self._get_default_mappings()
        
        if not self.mappings_file.exists():
            logger.error(f"Mappings file not found: {self.mappings_file}")
            return self._get_default_mappings()
        
        try:
            if self.mappings_file.suffix.lower() == '.yaml' or self.mappings_file.suffix.lower() == '.yml':
                return self._load_yaml_mappings()
            elif self.mappings_file.suffix.lower() == '.json':
                return self._load_json_mappings()
            elif self.mappings_file.suffix.lower() == '.properties':
                return self._load_properties_mappings()
            else:
                logger.error(f"Unsupported file format: {self.mappings_file.suffix}")
                return self._get_default_mappings()
        except Exception as e:
            logger.error(f"Error loading mappings from {self.mappings_file}: {e}")
            return self._get_default_mappings()
    
    def _load_yaml_mappings(self) -> Dict[str, RequestMapping]:
        """Load mappings from YAML file"""
        with open(self.mappings_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        mappings = {}
        response_parsers = data.get('response_parsers', {})
        
        for tool_name, mapping_data in data.get('mappings', {}).items():
            mappings[tool_name] = RequestMapping(
                endpoint=mapping_data['endpoint'],
                method=mapping_data['method'],
                description=mapping_data['description'],
                required_params=mapping_data.get('required_params', []),
                optional_params=mapping_data.get('optional_params', []),
                response_parser=mapping_data.get('response_parser'),
                param_types=mapping_data.get('param_types')
            )
        
        # Store response parsers for later use
        self.response_parsers = response_parsers
        
        logger.info(f"Loaded {len(mappings)} tool mappings from {self.mappings_file}")
        return mappings
    
    def _load_json_mappings(self) -> Dict[str, RequestMapping]:
        """Load mappings from JSON file"""
        with open(self.mappings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mappings = {}
        response_parsers = data.get('response_parsers', {})
        
        for tool_name, mapping_data in data.get('mappings', {}).items():
            mappings[tool_name] = RequestMapping(
                endpoint=mapping_data['endpoint'],
                method=mapping_data['method'],
                description=mapping_data['description'],
                required_params=mapping_data.get('required_params', []),
                optional_params=mapping_data.get('optional_params', []),
                response_parser=mapping_data.get('response_parser'),
                param_types=mapping_data.get('param_types')
            )
        
        # Store response parsers for later use
        self.response_parsers = response_parsers
        
        logger.info(f"Loaded {len(mappings)} tool mappings from {self.mappings_file}")
        return mappings
    
    def _load_properties_mappings(self) -> Dict[str, RequestMapping]:
        """Load mappings from properties file"""
        mappings = {}
        
        with open(self.mappings_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_tool = None
        tool_data = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Check if this is a new tool
                if '.' in key:
                    tool_name, field = key.split('.', 1)
                    
                    if tool_name != current_tool:
                        # Save previous tool if exists
                        if current_tool and tool_data:
                            mappings[current_tool] = self._create_mapping_from_properties(current_tool, tool_data)
                        
                        # Start new tool
                        current_tool = tool_name
                        tool_data = {}
                    
                    tool_data[field] = value
        
        # Save last tool
        if current_tool and tool_data:
            mappings[current_tool] = self._create_mapping_from_properties(current_tool, tool_data)
        
        logger.info(f"Loaded {len(mappings)} tool mappings from {self.mappings_file}")
        return mappings
    
    def _create_mapping_from_properties(self, tool_name: str, tool_data: Dict[str, str]) -> RequestMapping:
        """Create RequestMapping from properties data"""
        # Parse comma-separated lists
        def parse_list(value: str) -> List[str]:
            if not value:
                return []
            return [item.strip() for item in value.split(',') if item.strip()]
        
        return RequestMapping(
            endpoint=tool_data.get('endpoint', ''),
            method=tool_data.get('method', 'GET'),
            description=tool_data.get('description', f'Tool: {tool_name}'),
            required_params=parse_list(tool_data.get('required_params', '')),
            optional_params=parse_list(tool_data.get('optional_params', '')),
            response_parser=tool_data.get('response_parser') or None
        )
    
    def _get_default_mappings(self) -> Dict[str, RequestMapping]:
        """Get default mappings if no file is found"""
        logger.info("Using default tool mappings")
        return {
            "get_item": RequestMapping(
                endpoint="/api/items/{id}",
                method="GET",
                description="Get a specific item by ID",
                required_params=["id"],
                response_parser="parse_item"
            ),
            "get_categories": RequestMapping(
                endpoint="/api/categories",
                method="GET",
                description="Get all available categories",
                response_parser="parse_categories"
            ),
            "get_items_by_category": RequestMapping(
                endpoint="/api/items/category/{category}",
                method="GET",
                description="Get items by category",
                required_params=["category"],
                optional_params=["limit"],
                response_parser="parse_items_list"
            ),
            "search_items": RequestMapping(
                endpoint="/api/items/search",
                method="POST",
                description="Search items with filters",
                required_params=["query"],
                optional_params=["filter", "top"],
                response_parser="parse_items_list"
            ),
            "generic_request": RequestMapping(
                endpoint="/api/{path}",
                method="POST",
                description="Generic API request passthrough",
                required_params=["path"],
                optional_params=["method", "body", "params", "headers"]
            )
        }
    
    def get_response_parser_config(self, parser_name: str) -> Optional[Dict[str, Any]]:
        """Get response parser configuration by name"""
        return self.response_parsers.get(parser_name)
    
    def list_available_mappings(self) -> List[str]:
        """List all available mapping files in the config directory"""
        mapping_files = []
        for pattern in ["tool_mappings.yaml", "tool_mappings.yml", "tool_mappings.json", "tool_mappings.properties"]:
            mapping_files.extend(self.config_dir.glob(pattern))
        return [str(f) for f in mapping_files]

def load_tool_mappings(mappings_file: Optional[str] = None) -> Dict[str, RequestMapping]:
    """Convenience function to load tool mappings"""
    loader = MappingLoader()
    return loader.load_mappings(mappings_file)

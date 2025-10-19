"""
Generic MCP Server Package

A Model Context Protocol (MCP) server that provides generic microservice integration
through configurable tool mappings.
"""

from .server import GenericMCPServer, main
from .config import ServerConfig, DEFAULT_CONFIG

__version__ = "1.0.0"
__all__ = ["GenericMCPServer", "main", "ServerConfig", "DEFAULT_CONFIG"]

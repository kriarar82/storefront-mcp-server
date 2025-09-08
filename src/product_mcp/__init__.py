"""
Product MCP Server Package

A Model Context Protocol (MCP) server that provides product information
by communicating with a Java microservice.
"""

from .server import ProductMCPServer, main
from .config import ServerConfig, DEFAULT_CONFIG

__version__ = "1.0.0"
__all__ = ["ProductMCPServer", "main", "ServerConfig", "DEFAULT_CONFIG"]

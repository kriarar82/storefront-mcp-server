#!/bin/bash
# Convenience script to activate the virtual environment

echo "🐍 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "📦 Installed packages:"
pip list | grep -E "(mcp|httpx|pydantic|asyncio-mqtt|python-dotenv)"
echo ""
echo "🚀 You can now run:"
echo "  python run_server.py                           # Start the MCP server"
echo "  python -m src.product_mcp.cli server          # Start server via CLI"
echo "  python -m src.product_mcp.cli test             # Run test suite"
echo "  python -m src.product_mcp.test_client          # Run test client directly"
echo ""

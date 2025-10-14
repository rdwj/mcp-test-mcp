"""
Shared FastMCP server instance for mcp-test-mcp.

This module provides the central FastMCP server instance that is imported
and used by all tool modules for decorator-based registration.
"""

from fastmcp import FastMCP

# Create the shared FastMCP server instance
mcp = FastMCP(name="mcp-test-mcp")

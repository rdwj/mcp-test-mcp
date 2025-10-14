"""
mcp-test-mcp: A test MCP server implementation using FastMCP v2

This package provides a simple MCP server for testing and demonstration purposes.
It includes basic tools for echoing messages and performing arithmetic operations.

Example usage:
    From command line:
        mcp-test-mcp
        mcp-test-mcp --transport streamable-http --port 8000

    As a module:
        python -m mcp_test_mcp

    In Python code:
        from mcp_test_mcp import __version__
        print(f"Version: {__version__}")
"""

__version__ = "0.1.2"

__all__ = [
    "__version__",
]

"""
Entry point for running mcp-test-mcp as a module.

This module is executed when running:
    python -m mcp_test_mcp

or when using the installed console script:
    mcp-test-mcp
"""

from mcp_test_mcp.server import mcp


def main() -> None:
    """Main entry point for the MCP server."""
    # Uses stdio transport by default
    mcp.run()


if __name__ == "__main__":
    main()

"""
FastMCP server instance for mcp-test-mcp.

This module provides the main FastMCP server instance and registers
all available MCP tools for Claude Code/Desktop integration.

ARCHITECTURE NOTE - Dual Server/Client Role:
===========================================
This module serves as the MCP SERVER role in mcp-test-mcp's dual-role architecture:

1. **Server Role (This Module)**: Exposes testing tools via MCP protocol that Claude can call
2. **Client Role (ConnectionManager)**: Tools connect to target MCP servers for testing

The dual nature is intentional and by design - this is a testing harness where:
- Claude calls tools on THIS server (server role)
- Tools internally act as MCP clients (client role via ConnectionManager)
- Target MCP servers are tested through these tool calls

Flow: User → Claude → mcp-test-mcp (server) → Target MCP Server (client)

This design enables natural MCP server testing through Claude's existing tool-calling interface.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastmcp import Context, FastMCP

# Load environment variables from .env file
# Look for .env in the project root (parent of src/)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try current directory as fallback
    load_dotenv()
# Note: Don't log here - logging isn't set up yet and would go to stdout


# Configure structured JSON logging
def setup_json_logging() -> None:
    """
    Configure structured JSON logging to stdout.

    Log level is configurable via MCP_TEST_LOG_LEVEL environment variable.
    Defaults to INFO if not set.
    """
    log_level = os.environ.get("MCP_TEST_LOG_LEVEL", "INFO").upper()

    class JsonFormatter(logging.Formatter):
        """Custom formatter that outputs logs as JSON."""

        def format(self, record: logging.LogRecord) -> str:
            log_obj = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            # Add exception info if present
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)

            # Add any extra fields
            if hasattr(record, "extra"):
                log_obj["extra"] = record.extra

            return json.dumps(log_obj)

    # Configure root logger
    # IMPORTANT: Use stderr for logging to avoid interfering with stdio transport
    # which uses stdout for JSON-RPC protocol messages
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))


# Set up logging
setup_json_logging()

logger = logging.getLogger(__name__)

# Import the shared FastMCP server instance
from .mcp_instance import mcp

# Import tool modules to trigger decorator registration
# This MUST happen after mcp instance is imported but before the server runs
from .tools import connection, tools, resources, prompts, llm

# Note: Logging during module import can interfere with stdio transport
# Only log at DEBUG level to avoid corrupting JSON-RPC protocol on stdout
logger.debug("FastMCP server instance created", extra={"server_name": "mcp-test-mcp"})


@mcp.tool()
async def health_check(ctx: Context) -> Dict[str, Any]:
    """
    Health check endpoint that verifies the server is running.

    Returns:
        Dictionary with status and server information
    """
    await ctx.info("Health check requested")

    return {
        "status": "healthy",
        "server": "mcp-test-mcp",
        "version": "0.1.6",
        "transport": "stdio"
    }


@mcp.tool()
async def ping(ctx: Context) -> str:
    """
    Simple ping tool that responds with 'pong'.

    Useful for testing basic connectivity and server responsiveness.

    Returns:
        The string 'pong'
    """
    await ctx.debug("Ping received")
    return "pong"


@mcp.tool()
def echo(message: str) -> str:
    """
    Echo back a message.

    Args:
        message: The message to echo back

    Returns:
        The same message that was provided
    """
    logger.debug(f"Echo tool called with message: {message}")
    return message


@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    logger.debug(f"Add tool called: {a} + {b}")
    return a + b


# Tool registration happens automatically via decorators in imported modules
# No need for manual mcp.tool() calls here

# Note: Logging during module import can interfere with stdio transport
# Only log at DEBUG level to avoid corrupting JSON-RPC protocol on stdout
logger.debug("MCP tools registered", extra={
    "tools": [
        "health_check", "ping", "echo", "add",
        "connect_to_server", "disconnect", "get_connection_status",
        "list_tools", "call_tool",
        "list_resources", "read_resource",
        "list_prompts", "get_prompt",
        "execute_prompt_with_llm"
    ]
})

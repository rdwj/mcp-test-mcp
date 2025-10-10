"""
FastMCP server instance for mcp-test-mcp.

This module provides the main FastMCP server instance and registers
all available MCP tools for Claude Code/Desktop integration.
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
    logging.info(f"Loaded environment variables from {env_path}")
else:
    # Try current directory as fallback
    load_dotenv()
    logging.info("Attempted to load .env from current directory")

# Import tool functions
from .tools.connection import connect_to_server, disconnect, get_connection_status
from .tools.llm import execute_prompt_with_llm
from .tools.prompts import get_prompt, list_prompts
from .tools.resources import list_resources, read_resource
from .tools.tools import call_tool, list_tools


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
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))


# Set up logging
setup_json_logging()

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(name="mcp-test-mcp")

logger.info("FastMCP server instance created", extra={"server_name": "mcp-test-mcp"})


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
        "version": "0.1.0",
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


# Register connection management tools
mcp.tool(connect_to_server)
mcp.tool(disconnect)
mcp.tool(get_connection_status)

# Register tool testing tools
mcp.tool(list_tools)
mcp.tool(call_tool)

# Register resource testing tools
mcp.tool(list_resources)
mcp.tool(read_resource)

# Register prompt testing tools
mcp.tool(list_prompts)
mcp.tool(get_prompt)

# Register LLM integration tools
mcp.tool(execute_prompt_with_llm)

logger.info("MCP tools registered", extra={
    "tools": [
        "health_check", "ping", "echo", "add",
        "connect_to_server", "disconnect", "get_connection_status",
        "list_tools", "call_tool",
        "list_resources", "read_resource",
        "list_prompts", "get_prompt",
        "execute_prompt_with_llm"
    ]
})

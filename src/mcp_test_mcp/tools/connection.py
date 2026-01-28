"""Connection management tools for MCP server testing.

This module provides MCP tools that expose the ConnectionManager functionality
to AI assistants for managing connections to target MCP servers.

ARCHITECTURE NOTE - Client Role Implementation:
==============================================
This module implements the MCP CLIENT functionality for mcp-test-mcp's dual-role design:

1. These tools are exposed by the FastMCP server (server role in server.py)
2. When called, they use ConnectionManager to act as an MCP client
3. The client connects to target MCP servers for testing

Example flow for connect_to_server tool:
- Claude calls connect_to_server (MCP tool call to THIS server)
- Tool uses ConnectionManager.connect() (acts as MCP client)
- Connects to target server via stdio or streamable-http transport
- Returns connection state back to Claude

This bridging of server-exposed tools and client functionality is what enables
natural MCP server testing through Claude's conversation interface.
"""

import logging
import time
from typing import Annotated, Any, Optional

from fastmcp import Context

from ..connection import ConnectionError, ConnectionManager
from ..mcp_instance import mcp
from ..models import ConnectionState

logger = logging.getLogger(__name__)


@mcp.tool
async def connect_to_server(
    url: Annotated[str, "Server URL (http://..., https://...) or file path for stdio transport"],
    ctx: Context,
    headers: Annotated[
        Optional[dict[str, str]],
        "Optional HTTP headers for authenticated connections. Ignored for stdio.",
    ] = None,
) -> dict[str, Any]:
    """Connect to an MCP server for testing.

    Establishes a connection to a target MCP server using the appropriate
    transport protocol (stdio for file paths, streamable-http for URLs).
    Only one connection can be active at a time.

    Returns:
        Dictionary with connection details including:
        - success: Always True on successful connection
        - connection: Full ConnectionState with server info and statistics
        - message: Human-readable success message
        - metadata: Request timing information

    Raises:
        Returns error dict on failure with:
        - success: False
        - error: Error details (type, message, suggestion)
        - metadata: Request timing information
    """
    start_time = time.perf_counter()

    try:
        # User-facing progress update with safe header info
        if headers:
            header_names = list(headers.keys())
            await ctx.info(f"Connecting to MCP server at {url} with headers: {header_names}")
            logger.info(
                "Connecting to MCP server with custom headers",
                extra={"url": url, "header_names": header_names},
            )
        else:
            await ctx.info(f"Connecting to MCP server at {url}")
            logger.info(f"Connecting to MCP server at: {url}")

        state: ConnectionState = await ConnectionManager.connect(url, headers=headers)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing success update
        await ctx.info(f"Successfully connected to {url}")
        # Detailed technical log
        logger.info(
            f"Successfully connected to {url}",
            extra={
                "url": url,
                "transport": state.transport,
                "duration_ms": elapsed_ms,
            },
        )

        return {
            "success": True,
            "connection": state.model_dump(mode="json"),
            "message": f"Successfully connected to {url}",
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
                "transport": state.transport,
                "server_url": state.server_url,
                "headers_provided": state.headers_provided,
            },
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Failed to connect to {url}: {str(e)}")
        # Detailed technical log
        logger.error(
            f"Failed to connect to {url}: {str(e)}",
            extra={"url": url, "error": str(e), "duration_ms": elapsed_ms},
        )

        # Determine appropriate suggestion based on error
        suggestion = "Check that the server URL is correct and the server is running"
        if "timed out" in str(e).lower():
            suggestion = (
                "The connection timed out. "
                "Check server availability and network connectivity"
            )
        elif "file" in url.lower() or not url.startswith("http"):
            suggestion = (
                "For file paths, ensure the path is valid and "
                "the server executable has correct permissions"
            )

        return {
            "success": False,
            "error": {
                "error_type": "connection_failed",
                "message": str(e),
                "details": {"url": url},
                "suggestion": suggestion,
            },
            "connection": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
                "attempted_url": url,
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Unexpected error connecting to {url}: {str(e)}")
        # Detailed technical log
        logger.exception(
            f"Unexpected error connecting to {url}",
            extra={"url": url, "duration_ms": elapsed_ms},
        )

        return {
            "success": False,
            "error": {
                "error_type": "connection_failed",
                "message": f"Unexpected error: {str(e)}",
                "details": {"url": url, "exception_type": type(e).__name__},
                "suggestion": "This is an unexpected error. Check server logs for more details",
            },
            "connection": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
                "attempted_url": url,
            },
        }


@mcp.tool
async def disconnect(ctx: Context) -> dict[str, Any]:
    """Close the current MCP server connection.

    Safely disconnects from the active MCP server and clears all connection
    state and statistics. This method is safe to call even if no connection
    exists.

    Returns:
        Dictionary with disconnection details including:
        - success: Always True
        - message: Human-readable status message
        - was_connected: Whether a connection existed before disconnect
        - metadata: Request timing information and previous connection info
    """
    start_time = time.perf_counter()

    # Get current state before disconnecting
    previous_state = ConnectionManager.get_status()
    was_connected = previous_state is not None

    try:
        # User-facing progress update
        await ctx.info("Disconnecting from MCP server")
        # Detailed technical log
        logger.info("Disconnecting from MCP server")
        await ConnectionManager.disconnect()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        message = (
            "Successfully disconnected from MCP server"
            if was_connected
            else "No active connection to disconnect"
        )

        metadata: dict[str, Any] = {
            "request_time_ms": round(elapsed_ms, 2),
            "was_connected": was_connected,
        }

        # Include previous connection info if it existed
        if previous_state:
            metadata["previous_connection"] = {
                "server_url": previous_state.server_url,
                "transport": previous_state.transport,
                "duration_seconds": round(
                    (time.perf_counter() - previous_state.connected_at.timestamp())
                    if previous_state.connected_at
                    else 0,
                    2,
                ),
                "statistics": previous_state.statistics,
            }

        # User-facing completion update
        await ctx.info(message)
        # Detailed technical log
        logger.info(message, extra=metadata)

        return {
            "success": True,
            "message": message,
            "was_connected": was_connected,
            "metadata": metadata,
        }

    except Exception as e:
        # Disconnect should never fail, but handle gracefully
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Unexpected error during disconnect: {str(e)}")
        # Detailed technical log
        logger.exception("Unexpected error during disconnect")

        return {
            "success": True,  # Still return success since state is cleared
            "message": f"Disconnected with cleanup warning: {str(e)}",
            "was_connected": was_connected,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
                "cleanup_warning": str(e),
            },
        }


@mcp.tool
async def get_connection_status(ctx: Context) -> dict[str, Any]:
    """Check the current MCP server connection state.

    Returns detailed information about the active connection including
    server information, transport type, connection duration, and usage
    statistics.

    Returns:
        Dictionary with connection status including:
        - success: Always True
        - connected: Boolean indicating if currently connected
        - connection: Full ConnectionState if connected, None otherwise
        - message: Human-readable status message
        - metadata: Request timing and connection duration info
    """
    start_time = time.perf_counter()

    try:
        state = ConnectionManager.get_status()
        connected = state is not None

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        metadata: dict[str, Any] = {
            "request_time_ms": round(elapsed_ms, 2),
        }

        if connected and state:
            # Calculate connection duration
            if state.connected_at:
                duration_seconds = (
                    time.perf_counter() - state.connected_at.timestamp()
                )
                metadata["connection_duration_seconds"] = round(duration_seconds, 2)

            message = f"Connected to {state.server_url}"
            connection_data = state.model_dump(mode="json")

            # User-facing debug update
            await ctx.debug(f"Connection status: connected to {state.server_url}")
            # Detailed technical log
            logger.debug(
                "Connection status checked",
                extra={
                    "connected": True,
                    "server_url": state.server_url,
                    "statistics": state.statistics,
                },
            )
        else:
            message = "Not connected to any MCP server"
            connection_data = None

            # User-facing debug update
            await ctx.debug("Connection status: not connected")
            # Detailed technical log
            logger.debug("Connection status checked", extra={"connected": False})

        return {
            "success": True,
            "connected": connected,
            "connection": connection_data,
            "message": message,
            "metadata": metadata,
        }

    except Exception as e:
        # Status check should never fail, but handle gracefully
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Unexpected error checking connection status: {str(e)}")
        # Detailed technical log
        logger.exception("Unexpected error checking connection status")

        return {
            "success": True,  # Still return success with disconnected state
            "connected": False,
            "connection": None,
            "message": f"Unable to determine connection status: {str(e)}",
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
                "error": str(e),
            },
        }

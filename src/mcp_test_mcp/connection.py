"""Connection manager for MCP server connections.

This module provides the ConnectionManager class for managing a single active
connection to a target MCP server, tracking connection state and statistics.

ARCHITECTURE NOTE - MCP Client Role:
====================================
This is the MCP CLIENT component in mcp-test-mcp's dual-role architecture:

- **Role**: Acts as an MCP client to connect to target MCP servers
- **Used By**: Tool implementations in tools/ that are exposed as MCP server tools
- **Purpose**: Enables testing of target MCP servers by providing client connectivity

Flow:
1. User calls a tool via Claude (e.g., connect_to_server)
2. Tool in tools/connection.py calls ConnectionManager.connect()
3. ConnectionManager creates a FastMCP Client and connects to target server
4. Tool returns results back to Claude through the MCP server interface

This singleton manager ensures only one target server connection is active at a time,
simplifying state management for testing workflows.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Optional, Union

from fastmcp import Client
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
from mcp.types import ServerCapabilities

from .models import ConnectionState, ErrorDetail

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Exception raised when connection operations fail."""

    pass


class _GlobalConnectionState:
    """Internal singleton to store global connection state."""

    def __init__(self) -> None:
        self.client: Optional[Client] = None
        self.state: Optional[ConnectionState] = None
        self.lock = asyncio.Lock()


# Global connection state singleton
_connection: _GlobalConnectionState = _GlobalConnectionState()


class ConnectionManager:
    """Manages a single active connection to an MCP server.

    This class provides methods to connect to, disconnect from, and query
    the status of an MCP server connection. Only one connection can be
    active at a time (global state).

    The connection manager tracks usage statistics including tool calls,
    resource accesses, prompt executions, and errors.
    """

    @staticmethod
    def _get_timeout(env_var: str, default: float) -> float:
        """Get timeout value from environment variable with fallback to default.

        Args:
            env_var: Environment variable name
            default: Default timeout in seconds

        Returns:
            Timeout value in seconds
        """
        value = os.environ.get(env_var)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    @staticmethod
    def _infer_transport(url: str) -> str:
        """Infer transport type from URL.

        Args:
            url: Server URL or file path

        Returns:
            Transport type: "stdio", "sse", or "streamable-http"
        """
        url_lower = url.lower()
        if url_lower.startswith(("http://", "https://")):
            # Check for legacy SSE endpoints
            if url_lower.endswith("/sse"):
                return "sse"
            return "streamable-http"
        # File paths use stdio transport
        return "stdio"

    @classmethod
    async def connect(
        cls, url: str, headers: Optional[dict[str, str]] = None
    ) -> ConnectionState:
        """Connect to an MCP server.

        Creates a FastMCP Client instance, establishes connection, and stores
        the connection state globally. If a connection already exists, it will
        be closed before establishing the new connection.

        Args:
            url: Server URL or file path
                - HTTP/HTTPS URLs use streamable-http transport
                - File paths use stdio transport
            headers: Optional HTTP headers for authenticated connections.
                     Only used for HTTP-based transports. Ignored for stdio.
                     Header values are not logged or stored for security.

        Returns:
            ConnectionState with connection details and initial statistics

        Raises:
            ConnectionError: If connection fails
        """
        async with _connection.lock:
            # Close existing connection if any
            if _connection.client is not None:
                await cls._disconnect_internal()

            # Get timeout configuration
            connect_timeout = cls._get_timeout("MCP_TEST_CONNECT_TIMEOUT", 30.0)

            # Normalize empty headers to None
            if headers is not None and len(headers) == 0:
                headers = None

            try:
                # Infer transport type
                transport_type = cls._infer_transport(url)

                # Track whether headers were actually used (not just provided)
                headers_provided = False

                # Create client with explicit transport if headers provided for HTTP
                client: Client  # type: ignore[type-arg]
                if headers and transport_type in ("streamable-http", "sse"):
                    transport_obj: Union[SSETransport, StreamableHttpTransport]
                    if transport_type == "sse":
                        transport_obj = SSETransport(url=url, headers=headers)
                    else:
                        transport_obj = StreamableHttpTransport(url=url, headers=headers)
                    client = Client(transport_obj, timeout=connect_timeout)
                    headers_provided = True
                else:
                    if headers and transport_type == "stdio":
                        logger.debug(
                            "Headers ignored for stdio transport",
                            extra={"header_names": list(headers.keys())},
                        )
                    # Let FastMCP auto-detect transport
                    client = Client(url, timeout=connect_timeout)

                # Establish connection
                await asyncio.wait_for(client.__aenter__(), timeout=connect_timeout)

                # Use inferred transport type
                transport = transport_type

                # Get server information
                server_info: dict[str, Any] = {}
                try:
                    # Try to get server info via initialization result
                    if hasattr(client, "_session") and client._session:
                        session = client._session
                        if hasattr(session, "server_info"):
                            info = session.server_info
                            server_info = {
                                "name": getattr(info, "name", None),
                                "version": getattr(info, "version", None),
                            }
                            # Add capabilities if available
                            if hasattr(session, "server_capabilities"):
                                caps: ServerCapabilities = session.server_capabilities
                                server_info["capabilities"] = {
                                    "tools": bool(getattr(caps, "tools", None)),
                                    "resources": bool(getattr(caps, "resources", None)),
                                    "prompts": bool(getattr(caps, "prompts", None)),
                                }
                except Exception:
                    # If we can't get server info, continue without it
                    pass

                # Create connection state
                state = ConnectionState(
                    server_url=url,
                    transport=transport,  # type: ignore
                    connected_at=datetime.now(),
                    server_info=server_info if server_info else None,
                    statistics={
                        "tools_called": 0,
                        "resources_accessed": 0,
                        "prompts_executed": 0,
                        "errors": 0,
                    },
                    headers_provided=headers_provided,
                )

                # Store globally
                _connection.client = client
                _connection.state = state

                return state

            except asyncio.TimeoutError as e:
                raise ConnectionError(
                    f"Connection to {url} timed out after {connect_timeout}s"
                ) from e
            except Exception as e:
                raise ConnectionError(f"Failed to connect to {url}: {str(e)}") from e

    @classmethod
    async def _disconnect_internal(cls) -> None:
        """Internal disconnect that doesn't acquire the lock."""
        if _connection.client is not None:
            try:
                await _connection.client.__aexit__(None, None, None)
            except Exception:
                # Ignore errors during disconnect
                pass
            finally:
                _connection.client = None
                _connection.state = None

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from the current MCP server.

        Closes the active client connection and clears all connection state.
        This method is safe to call even if no connection exists.
        """
        async with _connection.lock:
            await cls._disconnect_internal()

    @classmethod
    def get_status(cls) -> Optional[ConnectionState]:
        """Get current connection status.

        Returns:
            ConnectionState if connected, None if not connected
        """
        return _connection.state

    @classmethod
    def require_connection(cls) -> tuple[Client, ConnectionState]:
        """Validate that a connection exists and return client and state.

        This method should be called before any operation that requires
        an active connection.

        Returns:
            Tuple of (Client, ConnectionState)

        Raises:
            ConnectionError: If no active connection exists
        """
        if _connection.client is None or _connection.state is None:
            raise ConnectionError("Not connected to any MCP server. Use connect() first.")

        # Verify connection is still active
        if not _connection.client.is_connected():
            # Clear stale state
            _connection.client = None
            _connection.state = None
            raise ConnectionError("Connection to MCP server was lost. Please reconnect.")

        return _connection.client, _connection.state

    @classmethod
    def increment_stat(cls, stat_name: str) -> None:
        """Increment a connection statistic.

        Args:
            stat_name: Name of the statistic to increment
                       (tools_called, resources_accessed, prompts_executed, errors)
        """
        if _connection.state is not None:
            if stat_name in _connection.state.statistics:
                _connection.state.statistics[stat_name] += 1

    @classmethod
    def create_error_detail(
        cls,
        error_type: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ) -> ErrorDetail:
        """Create an ErrorDetail instance with proper type checking.

        Args:
            error_type: Type of error
            message: Error message
            details: Additional error details
            suggestion: Suggested resolution

        Returns:
            ErrorDetail instance
        """
        return ErrorDetail(
            error_type=error_type,  # type: ignore
            message=message,
            details=details,
            suggestion=suggestion,
        )

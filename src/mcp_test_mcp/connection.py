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
from fastmcp.client.auth import BearerAuth, OAuth
from fastmcp.client.transports import (
    SSETransport,
    StdioTransport,
    StreamableHttpTransport,
)
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

    @staticmethod
    def _build_auth(auth: Optional[Union[str, dict]]) -> Any:
        """Convert auth parameter to FastMCP auth object.

        Args:
            auth: Authentication config. Accepts:
                - None: No authentication
                - str "oauth": Trigger OAuth flow
                - str (other): Bearer token
                - dict {"type": "bearer", "token": "..."}: Bearer token
                - dict {"type": "oauth", ...}: OAuth with optional scopes/client_id/client_secret

        Returns:
            FastMCP auth object (BearerAuth, OAuth) or None.
            Credential values are never logged.

        Raises:
            ValueError: If auth config is invalid
        """
        if auth is None:
            return None
        if isinstance(auth, str):
            if auth == "oauth":
                return OAuth()
            return BearerAuth(token=auth)
        if isinstance(auth, dict):
            auth_type = auth.get("type")
            if auth_type == "bearer":
                token = auth.get("token")
                if not token:
                    raise ValueError("Auth dict with type 'bearer' requires 'token' key")
                return BearerAuth(token=token)
            if auth_type == "oauth":
                return OAuth(
                    scopes=auth.get("scopes"),
                    client_id=auth.get("client_id"),
                    client_secret=auth.get("client_secret"),
                )
            raise ValueError(f"Unknown auth type: {auth_type!r}. Expected 'bearer' or 'oauth'")
        raise ValueError(f"auth must be a string or dict, got {type(auth).__name__}")

    @staticmethod
    def _build_stdio_transport(
        command: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> StdioTransport:
        """Build an explicit StdioTransport from command parameters.

        Args:
            command: The command to run (e.g. 'python', 'node', 'npx')
            args: Arguments for the command
            env: Environment variables for the subprocess
            cwd: Working directory for the subprocess

        Returns:
            Configured StdioTransport instance
        """
        return StdioTransport(command=command, args=args or [], env=env, cwd=cwd)

    @classmethod
    async def connect(
        cls,
        url: str,
        headers: Optional[dict[str, str]] = None,
        auth: Optional[Union[str, dict]] = None,
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[str] = None,
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
            auth: Authentication config. Accepts:
                - None: No authentication
                - str "oauth": Trigger OAuth flow
                - str (other): Bearer token
                - dict {"type": "bearer", "token": "..."}: Bearer token
                - dict {"type": "oauth", ...}: OAuth with optional params
                Credential values are never logged or stored.
            command: Explicit stdio command (e.g. 'python', 'node', 'npx').
                     When provided, connects via StdioTransport.
            args: Arguments for the stdio command.
            env: Environment variables for the stdio subprocess.
            cwd: Working directory for the stdio subprocess.

        Returns:
            ConnectionState with connection details and initial statistics

        Raises:
            ConnectionError: If connection fails
            ValueError: If auth config is invalid
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

            # Build auth object if provided
            auth_obj = cls._build_auth(auth)

            try:
                # Track whether headers were actually used
                headers_provided = False

                # Branch 1: Explicit stdio via command parameter
                if command is not None:
                    transport_type = "stdio"
                    if auth_obj is not None:
                        logger.debug("Auth ignored for explicit stdio command transport")
                    transport_obj = cls._build_stdio_transport(command, args, env, cwd)
                    client = Client(transport_obj, timeout=connect_timeout)
                else:
                    # Infer transport type from URL
                    transport_type = cls._infer_transport(url)

                    # Branch 2: HTTP with custom headers (need explicit transport)
                    if headers and transport_type in ("streamable-http", "sse"):
                        transport_obj: Union[SSETransport, StreamableHttpTransport]
                        if transport_type == "sse":
                            transport_obj = SSETransport(url=url, headers=headers, auth=auth_obj)
                        else:
                            transport_obj = StreamableHttpTransport(url=url, headers=headers, auth=auth_obj)
                        client = Client(transport_obj, timeout=connect_timeout)
                        headers_provided = True
                    # Branch 3: Auto-detect transport (with optional auth)
                    else:
                        if headers and transport_type == "stdio":
                            logger.debug(
                                "Headers ignored for stdio transport",
                                extra={"header_names": list(headers.keys())},
                            )
                        if auth_obj is not None and transport_type == "stdio":
                            logger.debug("Auth ignored for stdio transport")
                        # Client handles auth directly for non-header cases
                        client = Client(url, auth=auth_obj, timeout=connect_timeout)

                # Establish connection
                await asyncio.wait_for(client.__aenter__(), timeout=connect_timeout)

                # Use inferred/explicit transport type
                transport = transport_type

                # Determine auth type for state tracking
                auth_type_value = None
                if auth_obj is not None:
                    auth_type_value = "oauth" if isinstance(auth_obj, OAuth) else "bearer"

                # Get server information
                server_info: dict[str, Any] = {}
                try:
                    # Get server info via public initialize_result API
                    init_result = client.initialize_result
                    if init_result is not None:
                        info = init_result.serverInfo
                        server_info = {
                            "name": getattr(info, "name", None),
                            "version": getattr(info, "version", None),
                        }
                        # Add capabilities if available
                        caps: ServerCapabilities = init_result.capabilities
                        if caps is not None:
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
                    auth_type=auth_type_value,
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

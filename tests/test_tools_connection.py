"""Tests for connection management tools.

This module contains unit and integration tests for the connection tools:
connect_to_server, disconnect, and get_connection_status.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_test_mcp.connection import ConnectionError, ConnectionManager
from mcp_test_mcp.models import ConnectionState
from mcp_test_mcp.tools.connection import (
    connect_to_server,
    disconnect,
    get_connection_status,
)


@pytest.fixture
def mock_connection_state():
    """Create a mock ConnectionState for testing."""
    return ConnectionState(
        server_url="http://test.example.com/mcp",
        transport="streamable-http",
        connected_at=datetime.now(),
        server_info={"name": "test-server", "version": "1.0.0"},
        statistics={
            "tools_called": 0,
            "resources_accessed": 0,
            "prompts_executed": 0,
            "errors": 0,
        },
    )


class TestConnectToServer:
    """Tests for connect_to_server tool."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_connection_state, mock_ctx):
        """Test successful connection to MCP server."""
        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_connection_state

            result = await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # Verify the call
            mock_connect.assert_called_once_with(
                "http://test.example.com/mcp",
                headers=None,
                auth=None,
                command=None,
                args=None,
                env=None,
                cwd=None,
            )

            # Verify response structure
            assert result["success"] is True
            assert "connection" in result
            assert result["connection"]["server_url"] == "http://test.example.com/mcp"
            assert result["connection"]["transport"] == "streamable-http"
            assert "message" in result
            assert "Successfully connected" in result["message"]

            # Verify metadata
            assert "metadata" in result
            assert "request_time_ms" in result["metadata"]
            assert result["metadata"]["transport"] == "streamable-http"
            assert result["metadata"]["server_url"] == "http://test.example.com/mcp"

    @pytest.mark.asyncio
    async def test_connect_timeout(self, mock_ctx):
        """Test connection timeout error handling."""
        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.side_effect = ConnectionError(
                "Connection to http://test.example.com/mcp timed out after 30.0s"
            )

            result = await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # Verify error response
            assert result["success"] is False
            assert "error" in result
            assert result["error"]["error_type"] == "connection_failed"
            assert "timed out" in result["error"]["message"]
            assert "timed out" in result["error"]["suggestion"].lower()

            # Verify metadata
            assert "metadata" in result
            assert "request_time_ms" in result["metadata"]
            assert result["connection"] is None

    @pytest.mark.asyncio
    async def test_connect_invalid_server(self, mock_ctx):
        """Test connection to invalid server."""
        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.side_effect = ConnectionError(
                "Failed to connect to http://invalid.example.com/mcp: Connection refused"
            )

            result = await connect_to_server("http://invalid.example.com/mcp", ctx=mock_ctx)

            # Verify error response
            assert result["success"] is False
            assert "error" in result
            assert result["error"]["error_type"] == "connection_failed"
            assert "Connection refused" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_connect_stdio_path(self, mock_connection_state, mock_ctx):
        """Test connection using stdio transport (file path)."""
        stdio_state = ConnectionState(
            server_url="/path/to/server",
            transport="stdio",
            connected_at=datetime.now(),
            server_info=None,
            statistics={
                "tools_called": 0,
                "resources_accessed": 0,
                "prompts_executed": 0,
                "errors": 0,
            },
        )

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = stdio_state

            result = await connect_to_server("/path/to/server", ctx=mock_ctx)

            # Verify the call
            mock_connect.assert_called_once_with(
                "/path/to/server",
                headers=None,
                auth=None,
                command=None,
                args=None,
                env=None,
                cwd=None,
            )

            # Verify transport is stdio
            assert result["success"] is True
            assert result["connection"]["transport"] == "stdio"

    @pytest.mark.asyncio
    async def test_connect_unexpected_error(self, mock_ctx):
        """Test handling of unexpected errors during connection."""
        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.side_effect = RuntimeError("Unexpected error")

            result = await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # Verify error response
            assert result["success"] is False
            assert "error" in result
            assert result["error"]["error_type"] == "connection_failed"
            assert "Unexpected error" in result["error"]["message"]
            assert "unexpected" in result["error"]["suggestion"].lower()


class TestDisconnect:
    """Tests for disconnect tool."""

    @pytest.mark.asyncio
    async def test_disconnect_when_connected(self, mock_connection_state, mock_ctx):
        """Test disconnecting when a connection exists."""
        with patch.object(
            ConnectionManager, "get_status"
        ) as mock_status, patch.object(
            ConnectionManager, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect:
            mock_status.return_value = mock_connection_state

            result = await disconnect(ctx=mock_ctx)

            # Verify the call
            mock_disconnect.assert_called_once()

            # Verify response
            assert result["success"] is True
            assert result["was_connected"] is True
            assert "Successfully disconnected" in result["message"]

            # Verify metadata includes previous connection info
            assert "metadata" in result
            assert "request_time_ms" in result["metadata"]
            assert "previous_connection" in result["metadata"]
            assert (
                result["metadata"]["previous_connection"]["server_url"]
                == "http://test.example.com/mcp"
            )

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, mock_ctx):
        """Test disconnecting when no connection exists."""
        with patch.object(ConnectionManager, "get_status") as mock_status, patch.object(
            ConnectionManager, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect:
            mock_status.return_value = None

            result = await disconnect(ctx=mock_ctx)

            # Verify the call
            mock_disconnect.assert_called_once()

            # Verify response
            assert result["success"] is True
            assert result["was_connected"] is False
            assert "No active connection" in result["message"]

            # Verify metadata does not include previous connection
            assert "metadata" in result
            assert "previous_connection" not in result["metadata"]

    @pytest.mark.asyncio
    async def test_disconnect_with_cleanup_error(self, mock_connection_state, mock_ctx):
        """Test disconnect handles cleanup errors gracefully."""
        with patch.object(
            ConnectionManager, "get_status"
        ) as mock_status, patch.object(
            ConnectionManager, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect:
            mock_status.return_value = mock_connection_state
            mock_disconnect.side_effect = Exception("Cleanup error")

            result = await disconnect(ctx=mock_ctx)

            # Should still return success since state is cleared
            assert result["success"] is True
            assert "cleanup_warning" in result["metadata"]


class TestGetConnectionStatus:
    """Tests for get_connection_status tool."""

    @pytest.mark.asyncio
    async def test_status_when_connected(self, mock_connection_state, mock_ctx):
        """Test getting status when connected."""
        with patch.object(ConnectionManager, "get_status") as mock_status:
            mock_status.return_value = mock_connection_state

            result = await get_connection_status(ctx=mock_ctx)

            # Verify response
            assert result["success"] is True
            assert result["connected"] is True
            assert result["connection"] is not None
            assert (
                result["connection"]["server_url"] == "http://test.example.com/mcp"
            )
            assert "Connected to" in result["message"]

            # Verify metadata
            assert "metadata" in result
            assert "request_time_ms" in result["metadata"]
            assert "connection_duration_seconds" in result["metadata"]

    @pytest.mark.asyncio
    async def test_status_when_not_connected(self, mock_ctx):
        """Test getting status when not connected."""
        with patch.object(ConnectionManager, "get_status") as mock_status:
            mock_status.return_value = None

            result = await get_connection_status(ctx=mock_ctx)

            # Verify response
            assert result["success"] is True
            assert result["connected"] is False
            assert result["connection"] is None
            assert "Not connected" in result["message"]

            # Verify metadata
            assert "metadata" in result
            assert "request_time_ms" in result["metadata"]
            assert "connection_duration_seconds" not in result["metadata"]

    @pytest.mark.asyncio
    async def test_status_unexpected_error(self, mock_ctx):
        """Test status check handles unexpected errors gracefully."""
        with patch.object(ConnectionManager, "get_status") as mock_status:
            mock_status.side_effect = Exception("Unexpected error")

            result = await get_connection_status(ctx=mock_ctx)

            # Should still return success with disconnected state
            assert result["success"] is True
            assert result["connected"] is False
            assert result["connection"] is None
            assert "Unable to determine" in result["message"]


class TestConnectionLifecycle:
    """Integration tests for full connection lifecycle."""

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self, mock_connection_state, mock_ctx):
        """Test complete connect -> status -> disconnect workflow."""
        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect, patch.object(
            ConnectionManager, "get_status"
        ) as mock_status, patch.object(
            ConnectionManager, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect:

            # Setup mocks
            mock_connect.return_value = mock_connection_state
            mock_status.side_effect = [
                mock_connection_state,  # First status check (connected)
                mock_connection_state,  # Second status check (still connected)
                mock_connection_state,  # Third status check (before disconnect)
                None,  # Final status check (disconnected)
            ]

            # Step 1: Connect
            connect_result = await connect_to_server(
                "http://test.example.com/mcp", ctx=mock_ctx
            )
            assert connect_result["success"] is True

            # Step 2: Check status (should be connected)
            status_result = await get_connection_status(ctx=mock_ctx)
            assert status_result["connected"] is True

            # Step 3: Verify still connected
            status_result2 = await get_connection_status(ctx=mock_ctx)
            assert status_result2["connected"] is True

            # Step 4: Disconnect
            disconnect_result = await disconnect(ctx=mock_ctx)
            assert disconnect_result["success"] is True
            assert disconnect_result["was_connected"] is True

            # Step 5: Check status (should be disconnected)
            final_status = await get_connection_status(ctx=mock_ctx)
            assert final_status["connected"] is False

    @pytest.mark.asyncio
    async def test_reconnect_closes_existing_connection(self, mock_connection_state, mock_ctx):
        """Test that connecting when already connected closes the old connection."""
        new_state = ConnectionState(
            server_url="http://new-server.example.com/mcp",
            transport="streamable-http",
            connected_at=datetime.now(),
            server_info={"name": "new-server", "version": "2.0.0"},
            statistics={
                "tools_called": 0,
                "resources_accessed": 0,
                "prompts_executed": 0,
                "errors": 0,
            },
        )

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            # First connection
            mock_connect.return_value = mock_connection_state
            result1 = await connect_to_server(
                "http://test.example.com/mcp", ctx=mock_ctx
            )
            assert result1["success"] is True

            # Second connection (should close first)
            mock_connect.return_value = new_state
            result2 = await connect_to_server(
                "http://new-server.example.com/mcp", ctx=mock_ctx
            )
            assert result2["success"] is True
            assert (
                result2["connection"]["server_url"]
                == "http://new-server.example.com/mcp"
            )


class TestConnectToServerAuth:
    """Tests for connect_to_server auth parameters."""

    @pytest.mark.asyncio
    async def test_connect_with_bearer_token(self, mock_connection_state, mock_ctx):
        """Verify auth='my-token' is passed through to ConnectionManager.connect."""
        mock_connection_state.auth_type = "bearer"

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_connection_state

            result = await connect_to_server(
                "https://example.com/mcp", ctx=mock_ctx, auth="my-token"
            )

            mock_connect.assert_called_once_with(
                "https://example.com/mcp",
                headers=None,
                auth="my-token",
                command=None,
                args=None,
                env=None,
                cwd=None,
            )
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_connect_with_oauth(self, mock_connection_state, mock_ctx):
        """Verify auth='oauth' is passed through to ConnectionManager.connect."""
        mock_connection_state.auth_type = "oauth"

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_connection_state

            result = await connect_to_server(
                "https://example.com/mcp", ctx=mock_ctx, auth="oauth"
            )

            mock_connect.assert_called_once_with(
                "https://example.com/mcp",
                headers=None,
                auth="oauth",
                command=None,
                args=None,
                env=None,
                cwd=None,
            )
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_connect_with_invalid_auth(self, mock_ctx):
        """Verify ValueError from bad auth config produces error response."""
        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.side_effect = ValueError("Unknown auth type: 'bad'")

            result = await connect_to_server(
                "https://example.com/mcp", ctx=mock_ctx, auth={"type": "bad"}
            )

            assert result["success"] is False
            assert result["error"]["error_type"] == "invalid_arguments"
            assert "Unknown auth type" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_connect_auth_type_in_metadata(self, mock_connection_state, mock_ctx):
        """Verify auth_type appears in success metadata."""
        mock_connection_state.auth_type = "bearer"

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_connection_state

            result = await connect_to_server(
                "https://example.com/mcp", ctx=mock_ctx, auth="my-token"
            )

            assert result["metadata"]["auth_type"] == "bearer"


class TestConnectToServerStdio:
    """Tests for connect_to_server explicit stdio parameters."""

    @pytest.mark.asyncio
    async def test_connect_with_command(self, mock_connection_state, mock_ctx):
        """Verify command/args/env/cwd are passed through to ConnectionManager.connect."""
        mock_connection_state.transport = "stdio"
        mock_connection_state.auth_type = None

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_connection_state

            result = await connect_to_server(
                "unused-url",
                ctx=mock_ctx,
                command="npx",
                args=["-y", "some-package"],
                env={"NODE_ENV": "test"},
                cwd="/tmp/project",
            )

            mock_connect.assert_called_once_with(
                "unused-url",
                headers=None,
                auth=None,
                command="npx",
                args=["-y", "some-package"],
                env={"NODE_ENV": "test"},
                cwd="/tmp/project",
            )
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_connect_command_progress_message(self, mock_connection_state, mock_ctx):
        """Verify ctx.info is called with command info in the message."""
        mock_connection_state.transport = "stdio"
        mock_connection_state.auth_type = None

        with patch.object(
            ConnectionManager, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_connection_state

            await connect_to_server(
                "unused-url",
                ctx=mock_ctx,
                command="python",
                args=["-m", "my_server"],
            )

            # Find the first ctx.info call (the progress message)
            first_info_call = mock_ctx.info.call_args_list[0]
            msg = first_info_call[0][0]
            assert "python -m my_server" in msg
            assert "Connecting via stdio command" in msg

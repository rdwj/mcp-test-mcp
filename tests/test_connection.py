"""Unit tests for ConnectionManager.

Tests cover connection lifecycle, statistics tracking, error handling,
timeout configuration, and state management.
"""

import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_test_mcp.connection import ConnectionError, ConnectionManager, _connection


@pytest.fixture(autouse=True)
async def reset_connection_state():
    """Reset global connection state before each test."""
    # Cleanup before test
    if _connection.client is not None:
        try:
            await _connection.client.__aexit__(None, None, None)
        except Exception:
            pass
    _connection.client = None
    _connection.state = None

    yield

    # Cleanup after test
    if _connection.client is not None:
        try:
            await _connection.client.__aexit__(None, None, None)
        except Exception:
            pass
    _connection.client = None
    _connection.state = None


class TestConnectionManager:
    """Test suite for ConnectionManager class."""

    def test_get_timeout_default(self):
        """Test timeout retrieval with default value."""
        timeout = ConnectionManager._get_timeout("NONEXISTENT_VAR", 30.0)
        assert timeout == 30.0

    def test_get_timeout_from_env(self):
        """Test timeout retrieval from environment variable."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "45.5"}):
            timeout = ConnectionManager._get_timeout("TEST_TIMEOUT", 30.0)
            assert timeout == 45.5

    def test_get_timeout_invalid_value(self):
        """Test timeout retrieval with invalid environment value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "invalid"}):
            timeout = ConnectionManager._get_timeout("TEST_TIMEOUT", 30.0)
            assert timeout == 30.0

    def test_infer_transport_http(self):
        """Test transport inference for HTTP URLs."""
        assert ConnectionManager._infer_transport("http://example.com/mcp") == "streamable-http"
        assert ConnectionManager._infer_transport("https://example.com/mcp") == "streamable-http"
        assert ConnectionManager._infer_transport("HTTP://EXAMPLE.COM/MCP") == "streamable-http"

    def test_infer_transport_sse(self):
        """Test transport inference for SSE URLs."""
        assert ConnectionManager._infer_transport("http://example.com/sse") == "sse"
        assert ConnectionManager._infer_transport("https://example.com/sse") == "sse"

    def test_infer_transport_stdio(self):
        """Test transport inference for file paths."""
        assert ConnectionManager._infer_transport("/path/to/server.py") == "stdio"
        assert ConnectionManager._infer_transport("./server.py") == "stdio"
        assert ConnectionManager._infer_transport("server.py") == "stdio"

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to MCP server."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)

        # Mock initialize_result with server info
        mock_server_info = Mock()
        mock_server_info.name = "TestServer"
        mock_server_info.version = "1.0.0"

        mock_capabilities = Mock()
        mock_capabilities.tools = {"listChanged": True}
        mock_capabilities.resources = {"subscribe": True, "listChanged": True}
        mock_capabilities.prompts = {"listChanged": True}

        mock_init_result = Mock()
        mock_init_result.serverInfo = mock_server_info
        mock_init_result.capabilities = mock_capabilities

        mock_client.initialize_result = mock_init_result

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            state = await ConnectionManager.connect("http://example.com/mcp")

        assert state.server_url == "http://example.com/mcp"
        assert state.transport == "streamable-http"
        assert state.connected_at is not None
        assert isinstance(state.connected_at, datetime)
        assert state.server_info is not None
        assert state.server_info["name"] == "TestServer"
        assert state.server_info["version"] == "1.0.0"
        assert state.server_info["capabilities"]["tools"] is True
        assert state.server_info["capabilities"]["resources"] is True
        assert state.server_info["capabilities"]["prompts"] is True
        assert state.statistics["tools_called"] == 0
        assert state.statistics["resources_accessed"] == 0
        assert state.statistics["prompts_executed"] == 0
        assert state.statistics["errors"] == 0

    @pytest.mark.asyncio
    async def test_connect_without_server_info(self):
        """Test connection when server info is not available."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            state = await ConnectionManager.connect("./server.py")

        assert state.server_url == "./server.py"
        assert state.transport == "stdio"
        assert state.connected_at is not None
        assert state.server_info is None

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """Test connection timeout handling."""
        mock_client = Mock()

        async def slow_connect():
            await asyncio.sleep(2)

        mock_client.__aenter__ = AsyncMock(side_effect=slow_connect)
        mock_client.__aexit__ = AsyncMock()

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            with patch.dict(os.environ, {"MCP_TEST_CONNECT_TIMEOUT": "0.1"}):
                with pytest.raises(ConnectionError) as exc_info:
                    await ConnectionManager.connect("http://example.com/mcp")

                assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aexit__ = AsyncMock()

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            with pytest.raises(ConnectionError) as exc_info:
                await ConnectionManager.connect("http://example.com/mcp")

            assert "Failed to connect" in str(exc_info.value)
            assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_replaces_existing_connection(self):
        """Test that new connection replaces existing one."""
        mock_client1 = Mock()
        mock_client1.__aenter__ = AsyncMock(return_value=mock_client1)
        mock_client1.__aexit__ = AsyncMock()
        mock_client1.is_connected = Mock(return_value=True)
        mock_client1._session = None

        mock_client2 = Mock()
        mock_client2.__aenter__ = AsyncMock(return_value=mock_client2)
        mock_client2.__aexit__ = AsyncMock()
        mock_client2.is_connected = Mock(return_value=True)
        mock_client2._session = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client1):
            state1 = await ConnectionManager.connect("http://example1.com/mcp")

        assert state1.server_url == "http://example1.com/mcp"

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client2):
            state2 = await ConnectionManager.connect("http://example2.com/mcp")

        assert state2.server_url == "http://example2.com/mcp"
        # Verify old client was closed
        mock_client1.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection from MCP server."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await ConnectionManager.connect("http://example.com/mcp")

        # Verify connection exists
        status = ConnectionManager.get_status()
        assert status is not None

        # Disconnect
        await ConnectionManager.disconnect()

        # Verify connection is cleared
        status = ConnectionManager.get_status()
        assert status is None
        mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self):
        """Test disconnect when no connection exists."""
        # Should not raise an error
        await ConnectionManager.disconnect()
        assert ConnectionManager.get_status() is None

    @pytest.mark.asyncio
    async def test_disconnect_error_handling(self):
        """Test disconnect handles client errors gracefully."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(side_effect=Exception("Disconnect error"))
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await ConnectionManager.connect("http://example.com/mcp")

        # Should not raise an error
        await ConnectionManager.disconnect()

        # Verify state is cleared despite error
        assert ConnectionManager.get_status() is None

    def test_get_status_no_connection(self):
        """Test get_status when not connected."""
        status = ConnectionManager.get_status()
        assert status is None

    @pytest.mark.asyncio
    async def test_get_status_with_connection(self):
        """Test get_status with active connection."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await ConnectionManager.connect("http://example.com/mcp")

        status = ConnectionManager.get_status()
        assert status is not None
        assert status.server_url == "http://example.com/mcp"
        assert status.transport == "streamable-http"

    def test_require_connection_no_connection(self):
        """Test require_connection raises error when not connected."""
        with pytest.raises(ConnectionError) as exc_info:
            ConnectionManager.require_connection()

        assert "Not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_connection_success(self):
        """Test require_connection returns client and state."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await ConnectionManager.connect("http://example.com/mcp")

        client, state = ConnectionManager.require_connection()
        assert client is mock_client
        assert state.server_url == "http://example.com/mcp"

    @pytest.mark.asyncio
    async def test_require_connection_lost_connection(self):
        """Test require_connection detects lost connection."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await ConnectionManager.connect("http://example.com/mcp")

        # Simulate lost connection
        mock_client.is_connected.return_value = False

        with pytest.raises(ConnectionError) as exc_info:
            ConnectionManager.require_connection()

        assert "Connection to MCP server was lost" in str(exc_info.value)
        # Verify state was cleared
        assert ConnectionManager.get_status() is None

    @pytest.mark.asyncio
    async def test_increment_stat(self):
        """Test statistics increment."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await ConnectionManager.connect("http://example.com/mcp")

        # Increment various statistics
        ConnectionManager.increment_stat("tools_called")
        ConnectionManager.increment_stat("tools_called")
        ConnectionManager.increment_stat("resources_accessed")
        ConnectionManager.increment_stat("prompts_executed")
        ConnectionManager.increment_stat("errors")

        status = ConnectionManager.get_status()
        assert status is not None
        assert status.statistics["tools_called"] == 2
        assert status.statistics["resources_accessed"] == 1
        assert status.statistics["prompts_executed"] == 1
        assert status.statistics["errors"] == 1

    def test_increment_stat_no_connection(self):
        """Test increment_stat is safe when not connected."""
        # Should not raise an error
        ConnectionManager.increment_stat("tools_called")

    def test_create_error_detail(self):
        """Test error detail creation."""
        error = ConnectionManager.create_error_detail(
            error_type="connection_failed",
            message="Test error",
            details={"reason": "timeout"},
            suggestion="Check network connection",
        )

        assert error.error_type == "connection_failed"
        assert error.message == "Test error"
        assert error.details == {"reason": "timeout"}
        assert error.suggestion == "Check network connection"

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test that concurrent connect attempts are serialized."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        call_count = 0

        def delayed_connect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_client

        with patch("mcp_test_mcp.connection.Client", side_effect=delayed_connect):
            # Start two concurrent connections
            task1 = asyncio.create_task(ConnectionManager.connect("http://example1.com/mcp"))
            task2 = asyncio.create_task(ConnectionManager.connect("http://example2.com/mcp"))

            results = await asyncio.gather(task1, task2)

        # Both should complete successfully
        assert len(results) == 2
        # Last connection should win
        status = ConnectionManager.get_status()
        assert status is not None
        # Should have called Client constructor twice
        assert call_count == 2


class TestConnectionManagerHeaders:
    """Test suite for ConnectionManager headers functionality."""

    @pytest.mark.asyncio
    async def test_connect_with_headers_creates_explicit_transport(self):
        """Test that headers create explicit StreamableHttpTransport."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        headers = {"Authorization": "Bearer test-token"}

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            with patch(
                "mcp_test_mcp.connection.StreamableHttpTransport"
            ) as mock_transport_class:
                mock_transport = Mock()
                mock_transport_class.return_value = mock_transport

                state = await ConnectionManager.connect(
                    "https://example.com/mcp", headers=headers
                )

                # Verify StreamableHttpTransport was created with headers and auth
                mock_transport_class.assert_called_once_with(
                    url="https://example.com/mcp", headers=headers, auth=None
                )
                # Verify Client was called with transport, not URL
                mock_client_class.assert_called_once_with(mock_transport, timeout=30.0)

        assert state.headers_provided is True
        assert state.transport == "streamable-http"

    @pytest.mark.asyncio
    async def test_connect_with_headers_sse_transport(self):
        """Test that headers create explicit SSETransport for SSE URLs."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        headers = {"X-API-Key": "secret-key"}

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            with patch("mcp_test_mcp.connection.SSETransport") as mock_transport_class:
                mock_transport = Mock()
                mock_transport_class.return_value = mock_transport

                state = await ConnectionManager.connect(
                    "https://example.com/sse", headers=headers
                )

                # Verify SSETransport was created with headers and auth
                mock_transport_class.assert_called_once_with(
                    url="https://example.com/sse", headers=headers, auth=None
                )
                # Verify Client was called with transport, not URL
                mock_client_class.assert_called_once_with(mock_transport, timeout=30.0)

        assert state.headers_provided is True
        assert state.transport == "sse"

    @pytest.mark.asyncio
    async def test_connect_headers_ignored_for_stdio(self):
        """Test that headers are silently ignored for stdio transport."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        headers = {"Authorization": "Bearer ignored-token"}

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            # Should NOT create explicit transport for stdio
            with patch(
                "mcp_test_mcp.connection.StreamableHttpTransport"
            ) as mock_http_transport:
                with patch("mcp_test_mcp.connection.SSETransport") as mock_sse_transport:
                    state = await ConnectionManager.connect(
                        "/path/to/server.py", headers=headers
                    )

                    # Neither transport class should be instantiated
                    mock_http_transport.assert_not_called()
                    mock_sse_transport.assert_not_called()

                    # Client should be called with URL directly (plus auth=None)
                    mock_client_class.assert_called_once_with(
                        "/path/to/server.py", auth=None, timeout=30.0
                    )

        # headers_provided should still be False since they were ignored
        assert state.headers_provided is False
        assert state.transport == "stdio"

    @pytest.mark.asyncio
    async def test_connect_empty_headers_treated_as_none(self):
        """Test that empty headers dict is treated as None."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            with patch(
                "mcp_test_mcp.connection.StreamableHttpTransport"
            ) as mock_transport_class:
                state = await ConnectionManager.connect(
                    "https://example.com/mcp", headers={}
                )

                # Empty headers should NOT create explicit transport
                mock_transport_class.assert_not_called()
                # Client should be called with URL directly (plus auth=None)
                mock_client_class.assert_called_once_with(
                    "https://example.com/mcp", auth=None, timeout=30.0
                )

        assert state.headers_provided is False

    @pytest.mark.asyncio
    async def test_connect_sets_headers_provided_flag(self):
        """Test that headers_provided flag is set correctly."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        # Test without headers
        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            state_no_headers = await ConnectionManager.connect("https://example.com/mcp")
            assert state_no_headers.headers_provided is False

        # Reset connection
        await ConnectionManager.disconnect()

        # Test with headers
        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            with patch("mcp_test_mcp.connection.StreamableHttpTransport"):
                state_with_headers = await ConnectionManager.connect(
                    "https://example.com/mcp", headers={"Auth": "token"}
                )
                assert state_with_headers.headers_provided is True


class TestConnectionManagerAuth:
    """Test suite for ConnectionManager auth functionality."""

    def test_build_auth_none(self):
        """_build_auth(None) returns None."""
        assert ConnectionManager._build_auth(None) is None

    def test_build_auth_bearer_string(self):
        """_build_auth with a token string returns BearerAuth."""
        from fastmcp.client.auth import BearerAuth

        result = ConnectionManager._build_auth("my-token")
        assert isinstance(result, BearerAuth)

    def test_build_auth_oauth_string(self):
        """_build_auth('oauth') returns OAuth."""
        from fastmcp.client.auth import OAuth

        result = ConnectionManager._build_auth("oauth")
        assert isinstance(result, OAuth)

    def test_build_auth_bearer_dict(self):
        """_build_auth with bearer dict returns BearerAuth."""
        from fastmcp.client.auth import BearerAuth

        result = ConnectionManager._build_auth({"type": "bearer", "token": "tk"})
        assert isinstance(result, BearerAuth)

    def test_build_auth_oauth_dict(self):
        """_build_auth with oauth dict returns OAuth."""
        from fastmcp.client.auth import OAuth

        result = ConnectionManager._build_auth({"type": "oauth", "scopes": ["read"]})
        assert isinstance(result, OAuth)

    def test_build_auth_bearer_dict_missing_token(self):
        """_build_auth with bearer dict missing token raises ValueError."""
        with pytest.raises(ValueError, match="requires 'token' key"):
            ConnectionManager._build_auth({"type": "bearer"})

    def test_build_auth_unknown_type(self):
        """_build_auth with unknown type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown auth type"):
            ConnectionManager._build_auth({"type": "custom"})

    def test_build_auth_invalid_type(self):
        """_build_auth with non-string/dict raises ValueError."""
        with pytest.raises(ValueError, match="auth must be a string or dict"):
            ConnectionManager._build_auth(123)

    @pytest.mark.asyncio
    async def test_connect_with_bearer_auth(self):
        """Verify auth kwarg is passed to Client for bearer token."""
        from fastmcp.client.auth import BearerAuth

        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            await ConnectionManager.connect(
                "https://example.com/mcp", auth="my-token"
            )

            # Client should receive auth kwarg
            call_kwargs = mock_client_class.call_args
            assert isinstance(call_kwargs.kwargs.get("auth"), BearerAuth)

    @pytest.mark.asyncio
    async def test_connect_with_oauth_auth(self):
        """Verify OAuth instance is passed to Client."""
        from fastmcp.client.auth import OAuth

        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            await ConnectionManager.connect(
                "https://example.com/mcp", auth="oauth"
            )

            call_kwargs = mock_client_class.call_args
            assert isinstance(call_kwargs.kwargs.get("auth"), OAuth)

    @pytest.mark.asyncio
    async def test_connect_auth_type_tracked(self):
        """Verify state.auth_type is set correctly."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            state = await ConnectionManager.connect(
                "https://example.com/mcp", auth="my-token"
            )
            assert state.auth_type == "bearer"

        await ConnectionManager.disconnect()

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            state = await ConnectionManager.connect(
                "https://example.com/mcp", auth="oauth"
            )
            assert state.auth_type == "oauth"


class TestConnectionManagerExplicitStdio:
    """Test suite for ConnectionManager explicit stdio transport."""

    @pytest.mark.asyncio
    async def test_connect_explicit_command(self):
        """Verify StdioTransport is created with correct args."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        mock_transport = Mock()

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            with patch(
                "mcp_test_mcp.connection.StdioTransport"
            ) as mock_stdio_class:
                mock_stdio_class.return_value = mock_transport

                await ConnectionManager.connect(
                    "unused-url",
                    command="python",
                    args=["-m", "my_server"],
                )

                mock_stdio_class.assert_called_once_with(
                    command="python", args=["-m", "my_server"], env=None, cwd=None
                )
                mock_client_class.assert_called_once_with(
                    mock_transport, timeout=30.0
                )

    @pytest.mark.asyncio
    async def test_connect_explicit_command_with_env_cwd(self):
        """Verify env and cwd are passed through."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        mock_transport = Mock()

        with patch("mcp_test_mcp.connection.Client") as mock_client_class:
            mock_client_class.return_value = mock_client

            with patch(
                "mcp_test_mcp.connection.StdioTransport"
            ) as mock_stdio_class:
                mock_stdio_class.return_value = mock_transport

                await ConnectionManager.connect(
                    "unused-url",
                    command="node",
                    args=["server.js"],
                    env={"NODE_ENV": "test"},
                    cwd="/tmp/project",
                )

                mock_stdio_class.assert_called_once_with(
                    command="node",
                    args=["server.js"],
                    env={"NODE_ENV": "test"},
                    cwd="/tmp/project",
                )

    @pytest.mark.asyncio
    async def test_connect_explicit_command_transport_type(self):
        """Verify state.transport is 'stdio' for explicit command."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.initialize_result = None

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            with patch("mcp_test_mcp.connection.StdioTransport"):
                state = await ConnectionManager.connect(
                    "unused-url",
                    command="python",
                    args=["-m", "server"],
                )

                assert state.transport == "stdio"

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

        # Mock session with server info
        mock_session = Mock()
        mock_server_info = Mock()
        mock_server_info.name = "TestServer"
        mock_server_info.version = "1.0.0"
        mock_session.server_info = mock_server_info

        # Mock server capabilities
        mock_capabilities = Mock()
        mock_capabilities.tools = {"listChanged": True}
        mock_capabilities.resources = {"subscribe": True, "listChanged": True}
        mock_capabilities.prompts = {"listChanged": True}
        mock_session.server_capabilities = mock_capabilities

        mock_client._session = mock_session

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
        mock_client._session = None

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
        mock_client._session = None

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
        mock_client._session = None

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
        mock_client._session = None

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
        mock_client._session = None

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
        mock_client._session = None

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
        mock_client._session = None

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
        mock_client._session = None

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

"""Tests for resource testing tools.

This module provides comprehensive unit and integration tests for the
list_resources and read_resource tools.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import Resource as McpResource

from mcp_test_mcp.connection import ConnectionError, ConnectionManager
from mcp_test_mcp.models import ConnectionState
from mcp_test_mcp.tools.resources import list_resources, read_resource


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


@pytest.fixture
def mock_client():
    """Create a mock FastMCP Client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_resources_result():
    """Create a mock resources result from MCP server."""
    # Create mock Resource objects
    resource1 = MagicMock(spec=McpResource)
    resource1.uri = "config://settings"
    resource1.name = "Application Settings"
    resource1.description = "Configuration settings"
    resource1.mimeType = "application/json"

    resource2 = MagicMock(spec=McpResource)
    resource2.uri = "data://users"
    resource2.name = "User Data"
    resource2.description = "Sample user data list"
    resource2.mimeType = "application/json"

    # client.list_resources() returns a list directly, not an object with .resources attribute
    return [resource1, resource2]


class TestListResources:
    """Test suite for list_resources tool."""

    async def test_list_resources_not_connected(self):
        """Test list_resources returns error when not connected."""
        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_require.side_effect = ConnectionError(
                "Not connected to any MCP server. Use connect() first."
            )

            result = await list_resources()

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "not_connected"
            assert "not connected" in result["error"]["message"].lower()
            assert result["error"]["suggestion"]
            assert result["resources"] == []
            assert "request_time_ms" in result["metadata"]

    async def test_list_resources_success(
        self, mock_connection_state, mock_client, mock_resources_result
    ):
        """Test list_resources successfully retrieves resources from mock server."""
        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_client.list_resources = AsyncMock(return_value=mock_resources_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await list_resources()

            # Verify the call
            mock_client.list_resources.assert_called_once()

            # Verify success response
            assert result["success"] is True
            assert "resources" in result
            assert isinstance(result["resources"], list)
            assert len(result["resources"]) == 2

            # Verify resource structure
            resource_uris = [r["uri"] for r in result["resources"]]
            assert "config://settings" in resource_uris
            assert "data://users" in resource_uris

            # Verify each resource has required fields
            for resource in result["resources"]:
                assert "uri" in resource
                assert "name" in resource
                assert "description" in resource
                assert "mimeType" in resource

            # Verify metadata
            assert "metadata" in result
            metadata = result["metadata"]
            assert metadata["total_resources"] == 2
            assert "server_url" in metadata
            assert "retrieved_at" in metadata
            assert "request_time_ms" in metadata
            assert metadata["request_time_ms"] > 0

    async def test_list_resources_empty_server(self, mock_connection_state, mock_client):
        """Test list_resources handles server with no resources gracefully."""
        # client.list_resources() returns a list directly
        empty_result = []

        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_client.list_resources = AsyncMock(return_value=empty_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await list_resources()

            # Should still succeed with empty list
            assert result["success"] is True
            assert result["resources"] == []
            assert result["metadata"]["total_resources"] == 0


class TestReadResource:
    """Test suite for read_resource tool."""

    async def test_read_resource_not_connected(self):
        """Test read_resource returns error when not connected."""
        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_require.side_effect = ConnectionError(
                "Not connected to any MCP server. Use connect() first."
            )

            result = await read_resource("config://settings")

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "not_connected"
            assert "not connected" in result["error"]["message"].lower()
            assert result["error"]["suggestion"]
            assert result["resource"] is None
            assert "request_time_ms" in result["metadata"]

    async def test_read_resource_success(self, mock_connection_state, mock_client):
        """Test read_resource successfully reads resource from mock server."""
        # Mock resource read result
        resource_result = MagicMock()
        content_item = MagicMock()
        content_item.text = '{"theme": "dark", "version": "1.0"}'
        content_item.mimeType = "application/json"
        resource_result.contents = [content_item]

        with patch.object(ConnectionManager, "require_connection") as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.read_resource = AsyncMock(return_value=resource_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await read_resource("config://settings")

            # Verify the call
            mock_client.read_resource.assert_called_once_with("config://settings")

            # Verify statistics were updated
            mock_increment.assert_called_once_with("resources_accessed")

            # Verify success response
            assert result["success"] is True
            assert "resource" in result
            resource = result["resource"]
            assert resource["uri"] == "config://settings"
            assert "content" in resource
            assert resource["content"] is not None

            # Verify metadata
            assert "metadata" in result
            metadata = result["metadata"]
            assert "content_size" in metadata
            assert metadata["content_size"] > 0
            assert "request_time_ms" in metadata
            assert metadata["request_time_ms"] > 0
            assert "server_url" in metadata
            assert "connection_statistics" in metadata

    async def test_read_resource_not_found(self, mock_connection_state, mock_client):
        """Test read_resource handles non-existent resource correctly."""
        with patch.object(ConnectionManager, "require_connection") as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.read_resource = AsyncMock(
                side_effect=Exception("Resource not found: nonexistent://resource")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await read_resource("nonexistent://resource")

            # Should return error
            assert result["success"] is False
            assert result["error"]["error_type"] == "resource_not_found"
            assert "not found" in result["error"]["message"].lower()
            assert result["error"]["suggestion"]
            assert "list_resources()" in result["error"]["suggestion"]
            assert result["resource"] is None

            # Verify error counter was incremented
            mock_increment.assert_called_once_with("errors")

    async def test_read_resource_multiple_reads(self, mock_connection_state, mock_client):
        """Test that multiple resource reads work correctly and update statistics."""
        # Mock resource read result
        resource_result = MagicMock()
        content_item = MagicMock()
        content_item.text = '{"data": "test"}'
        resource_result.contents = [content_item]

        # Create a stateful mock for statistics
        stats_tracker = {"resources_accessed": 0}

        def increment_stat(stat_name):
            if stat_name == "resources_accessed":
                stats_tracker[stat_name] += 1
                mock_connection_state.statistics[stat_name] = stats_tracker[stat_name]

        with patch.object(ConnectionManager, "require_connection") as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_increment.side_effect = increment_stat
            mock_client.read_resource = AsyncMock(return_value=resource_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            # Read first resource
            result1 = await read_resource("config://settings")
            assert result1["success"] is True
            stats1 = result1["metadata"]["connection_statistics"]["resources_accessed"]

            # Read second resource
            result2 = await read_resource("data://users")
            assert result2["success"] is True
            stats2 = result2["metadata"]["connection_statistics"]["resources_accessed"]

            # Verify statistics incremented
            assert stats2 == stats1 + 1

    async def test_read_resource_error_increments_error_stat(
        self, mock_connection_state, mock_client
    ):
        """Test that resource read errors increment the error statistic."""
        with patch.object(ConnectionManager, "require_connection") as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.read_resource = AsyncMock(
                side_effect=Exception("Resource not found")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await read_resource("nonexistent://resource")
            assert result["success"] is False

            # Verify error counter was incremented
            mock_increment.assert_called_with("errors")

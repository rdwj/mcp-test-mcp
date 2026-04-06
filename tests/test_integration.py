"""Integration tests for complete mcp-test-mcp workflows.

This module tests end-to-end workflows through the mcp-test-mcp tools,
verifying that connections, tools, resources, and prompts work together
correctly from connection to disconnection.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import Tool as McpTool

from mcp_test_mcp.connection import ConnectionManager
from mcp_test_mcp.models import ConnectionState
from mcp_test_mcp.tools.connection import (
    connect_to_server,
    disconnect,
    get_connection_status,
)
from mcp_test_mcp.tools.prompts import get_prompt, list_prompts
from mcp_test_mcp.tools.resources import list_resources, read_resource
from mcp_test_mcp.tools.tools import call_tool, list_tools


@pytest.fixture(autouse=True)
async def cleanup_connection():
    """Ensure connection is cleaned up before and after each test."""
    # Cleanup before test
    await ConnectionManager.disconnect()
    yield
    # Cleanup after test
    await ConnectionManager.disconnect()


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


def _make_mock_client_with_init_result():
    """Create a mock client with initialize_result for server info."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)

    # Mock initialize_result (public API in FastMCP 3.x)
    mock_server_info = MagicMock()
    mock_server_info.name = "test-server"
    mock_server_info.version = "1.0.0"

    mock_capabilities = MagicMock()
    mock_capabilities.tools = {"listChanged": True}
    mock_capabilities.resources = {"subscribe": True}
    mock_capabilities.prompts = {"listChanged": True}

    mock_init_result = MagicMock()
    mock_init_result.serverInfo = mock_server_info
    mock_init_result.capabilities = mock_capabilities

    mock_client.initialize_result = mock_init_result
    return mock_client


class TestToolWorkflows:
    """Integration tests for complete tool workflows."""

    @pytest.mark.asyncio
    async def test_full_tool_workflow(self, mock_connection_state, mock_ctx):
        """Test complete connect -> list_tools -> call_tool -> disconnect workflow."""
        mock_client = _make_mock_client_with_init_result()

        # Mock list_tools response -- client.list_tools() returns a list directly
        tool1 = MagicMock(spec=McpTool)
        tool1.name = "add"
        tool1.description = "Add two numbers"
        tool1.inputSchema = {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        }

        mock_client.list_tools = AsyncMock(return_value=[tool1])

        # Mock call_tool response
        tool_result = MagicMock()
        content_item = MagicMock()
        content_item.text = "8"
        tool_result.content = [content_item]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # Step 1: Connect
            connect_result = await connect_to_server(
                "http://test.example.com/mcp", ctx=mock_ctx
            )
            assert connect_result["success"] is True
            assert connect_result["connection"]["server_url"] == "http://test.example.com/mcp"

            # Step 2: List tools
            tools_result = await list_tools(ctx=mock_ctx)
            assert tools_result["success"] is True
            assert len(tools_result["tools"]) == 1
            assert tools_result["tools"][0]["name"] == "add"
            assert "input_schema" in tools_result["tools"][0]

            # Step 3: Call tool
            call_result = await call_tool("add", {"a": 5, "b": 3}, ctx=mock_ctx)
            assert call_result["success"] is True
            assert call_result["tool_call"]["tool_name"] == "add"
            assert call_result["tool_call"]["result"] == "8"
            assert "execution" in call_result["tool_call"]
            assert "duration_ms" in call_result["tool_call"]["execution"]

            # Step 4: Verify connection status
            status_result = await get_connection_status(ctx=mock_ctx)
            assert status_result["connected"] is True
            # Only call_tool increments tools_called, not list_tools
            assert status_result["connection"]["statistics"]["tools_called"] == 1

            # Step 5: Disconnect
            disconnect_result = await disconnect(ctx=mock_ctx)
            assert disconnect_result["success"] is True

            # Step 6: Verify disconnected
            final_status = await get_connection_status(ctx=mock_ctx)
            assert final_status["connected"] is False

    @pytest.mark.asyncio
    async def test_tool_error_recovery(self, mock_ctx):
        """Test error recovery when calling tools."""
        mock_client = _make_mock_client_with_init_result()

        # First call fails, second succeeds
        mock_client.call_tool = AsyncMock(side_effect=[
            Exception("Cannot divide by zero"),
            MagicMock(content=[MagicMock(text="3")]),
        ])

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # Call that fails
            error_result = await call_tool("divide", {"a": 10, "b": 0}, ctx=mock_ctx)
            assert error_result["success"] is False
            assert error_result["error"]["error_type"] in ["execution_error", "tool_execution_failed"]

            # Verify error was counted
            status = await get_connection_status(ctx=mock_ctx)
            assert status["connection"]["statistics"]["errors"] == 1

            # Call that succeeds
            success_result = await call_tool("add", {"a": 1, "b": 2}, ctx=mock_ctx)
            assert success_result["success"] is True

            await disconnect(ctx=mock_ctx)


class TestResourceWorkflows:
    """Integration tests for complete resource workflows."""

    @pytest.mark.asyncio
    async def test_full_resource_workflow(self, mock_ctx):
        """Test complete connect -> list_resources -> read_resource -> disconnect workflow."""
        mock_client = _make_mock_client_with_init_result()

        # Mock list_resources -- returns list directly
        resource1 = MagicMock()
        resource1.uri = "config://settings"
        resource1.name = "Settings"
        resource1.mimeType = "application/json"
        resource1.description = "App settings"

        mock_client.list_resources = AsyncMock(return_value=[resource1])

        # Mock read_resource -- returns list directly
        content_item = MagicMock()
        content_item.text = '{"theme": "dark"}'
        content_item.mimeType = "application/json"

        mock_client.read_resource = AsyncMock(return_value=[content_item])

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # Connect
            await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # List resources
            list_result = await list_resources(ctx=mock_ctx)
            assert list_result["success"] is True
            assert len(list_result["resources"]) == 1
            assert list_result["resources"][0]["uri"] == "config://settings"

            # Read resource
            read_result = await read_resource("config://settings", ctx=mock_ctx)
            assert read_result["success"] is True
            assert read_result["resource"]["uri"] == "config://settings"
            assert read_result["resource"]["content"] is not None

            # Verify statistics
            status = await get_connection_status(ctx=mock_ctx)
            # Only read_resource increments counter, not list_resources
            assert status["connection"]["statistics"]["resources_accessed"] == 1

            await disconnect(ctx=mock_ctx)

    @pytest.mark.asyncio
    async def test_resource_multiple_reads(self, mock_ctx):
        """Test reading multiple resources in sequence."""
        mock_client = _make_mock_client_with_init_result()

        # Mock read_resource -- returns list directly
        content_item = MagicMock()
        content_item.text = '{"data": "test"}'
        content_item.mimeType = "application/json"

        mock_client.read_resource = AsyncMock(return_value=[content_item])

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # Read multiple resources
            result1 = await read_resource("config://settings", ctx=mock_ctx)
            assert result1["success"] is True

            result2 = await read_resource("data://users", ctx=mock_ctx)
            assert result2["success"] is True

            # Verify statistics accumulated
            status = await get_connection_status(ctx=mock_ctx)
            assert status["connection"]["statistics"]["resources_accessed"] == 2

            await disconnect(ctx=mock_ctx)


class TestPromptWorkflows:
    """Integration tests for complete prompt workflows."""

    @pytest.mark.asyncio
    async def test_full_prompt_workflow(self, mock_ctx):
        """Test complete connect -> list_prompts -> get_prompt -> disconnect workflow."""
        mock_client = _make_mock_client_with_init_result()

        # Mock list_prompts -- returns list directly
        prompt1 = MagicMock()
        prompt1.name = "greeting"
        prompt1.description = "Generate a greeting"
        prompt1.arguments = []

        mock_client.list_prompts = AsyncMock(return_value=[prompt1])

        # Mock get_prompt
        message = MagicMock()
        message.role = "user"
        message.content.text = "Hello, Alice!"

        get_result = MagicMock()
        get_result.messages = [message]
        mock_client.get_prompt = AsyncMock(return_value=get_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # List prompts
            list_result = await list_prompts(ctx=mock_ctx)
            assert list_result["success"] is True
            assert len(list_result["prompts"]) == 1
            assert list_result["prompts"][0]["name"] == "greeting"

            # Get prompt
            get_result = await get_prompt("greeting", {"name": "Alice"}, ctx=mock_ctx)
            assert get_result["success"] is True
            assert get_result["prompt"]["name"] == "greeting"

            # Verify statistics
            status = await get_connection_status(ctx=mock_ctx)
            # Only get_prompt increments counter, not list_prompts
            assert status["connection"]["statistics"]["prompts_executed"] == 1

            await disconnect(ctx=mock_ctx)


class TestMixedWorkflows:
    """Integration tests for workflows using multiple capabilities."""

    @pytest.mark.asyncio
    async def test_mixed_operations_workflow(self, mock_ctx):
        """Test workflow using tools, resources, and prompts together."""
        mock_client = _make_mock_client_with_init_result()

        # Setup all mocks -- all return lists directly
        mock_client.list_tools = AsyncMock(return_value=[])

        tool_result = MagicMock()
        tool_result.content = [MagicMock(text="20")]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        mock_client.list_resources = AsyncMock(return_value=[])

        content_item = MagicMock()
        content_item.text = '{}'
        content_item.mimeType = "application/json"
        mock_client.read_resource = AsyncMock(return_value=[content_item])

        mock_client.list_prompts = AsyncMock(return_value=[])

        get_prompt_result = MagicMock()
        get_prompt_result.messages = [MagicMock(role="user", content=MagicMock(text="Hi"))]
        mock_client.get_prompt = AsyncMock(return_value=get_prompt_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp", ctx=mock_ctx)

            # Use tools
            await list_tools(ctx=mock_ctx)
            await call_tool("multiply", {"a": 4, "b": 5}, ctx=mock_ctx)

            # Use resources
            await list_resources(ctx=mock_ctx)
            await read_resource("config://settings", ctx=mock_ctx)

            # Use prompts
            await list_prompts(ctx=mock_ctx)
            await get_prompt("greeting", {"name": "Bob"}, ctx=mock_ctx)

            # Verify all statistics accumulated
            final_status = await get_connection_status(ctx=mock_ctx)
            # Only actual operations increment counters, not list operations
            assert final_status["connection"]["statistics"]["tools_called"] == 1
            assert final_status["connection"]["statistics"]["resources_accessed"] == 1
            assert final_status["connection"]["statistics"]["prompts_executed"] == 1

            await disconnect(ctx=mock_ctx)

    @pytest.mark.asyncio
    async def test_state_consistency_across_operations(self, mock_ctx):
        """Test that connection state remains consistent throughout operations."""
        mock_client = _make_mock_client_with_init_result()

        tool_result = MagicMock()
        tool_result.content = [MagicMock(text="result")]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # Connect
            connect_result = await connect_to_server(
                "http://test.example.com/mcp", ctx=mock_ctx
            )
            initial_url = connect_result["connection"]["server_url"]

            # Perform multiple operations
            for i in range(5):
                result = await call_tool("add", {"a": i, "b": i}, ctx=mock_ctx)
                assert result["success"] is True

            # Final status check
            final_status = await get_connection_status(ctx=mock_ctx)
            assert final_status["connection"]["server_url"] == initial_url
            assert final_status["connection"]["statistics"]["tools_called"] == 5

            await disconnect(ctx=mock_ctx)


class TestConnectionErrors:
    """Integration tests for connection error scenarios."""

    @pytest.mark.asyncio
    async def test_operations_without_connection(self, mock_ctx):
        """Test that operations fail gracefully when not connected."""
        # Ensure no connection
        await disconnect(ctx=mock_ctx)

        # Try various operations
        result = await list_tools(ctx=mock_ctx)
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await call_tool("add", {"a": 1, "b": 2}, ctx=mock_ctx)
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await list_resources(ctx=mock_ctx)
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await read_resource("config://settings", ctx=mock_ctx)
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await list_prompts(ctx=mock_ctx)
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await get_prompt("greeting", {"name": "Test"}, ctx=mock_ctx)
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

    @pytest.mark.asyncio
    async def test_reconnect_workflow(self, mock_ctx):
        """Test connecting, disconnecting, and reconnecting."""
        mock_client = _make_mock_client_with_init_result()

        tool_result = MagicMock()
        tool_result.content = [MagicMock(text="2")]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # First connection
            result1 = await connect_to_server(
                "http://server1.example.com/mcp", ctx=mock_ctx
            )
            assert result1["success"] is True

            # Do some work
            await call_tool("add", {"a": 1, "b": 1}, ctx=mock_ctx)

            # Disconnect
            await disconnect(ctx=mock_ctx)

            # Verify disconnected
            status = await get_connection_status(ctx=mock_ctx)
            assert status["connected"] is False

            # Reconnect to different server
            result2 = await connect_to_server(
                "http://server2.example.com/mcp", ctx=mock_ctx
            )
            assert result2["success"] is True
            assert result2["connection"]["server_url"] == "http://server2.example.com/mcp"

            # Verify statistics reset
            assert result2["connection"]["statistics"]["tools_called"] == 0

            await disconnect(ctx=mock_ctx)

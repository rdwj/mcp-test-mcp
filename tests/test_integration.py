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


class TestToolWorkflows:
    """Integration tests for complete tool workflows."""

    @pytest.mark.asyncio
    async def test_full_tool_workflow(self, mock_connection_state):
        """Test complete connect → list_tools → call_tool → disconnect workflow."""
        # Create mock client
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        # Mock session with server info
        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        # Mock list_tools response
        tool1 = MagicMock(spec=McpTool)
        tool1.name = "add"
        tool1.description = "Add two numbers"
        tool1.inputSchema = MagicMock()
        tool1.inputSchema.model_dump.return_value = {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        }

        tools_result = MagicMock()
        tools_result.tools = [tool1]
        mock_client.list_tools = AsyncMock(return_value=tools_result)

        # Mock call_tool response
        tool_result = MagicMock()
        content_item = MagicMock()
        content_item.text = "8"
        tool_result.content = [content_item]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # Step 1: Connect
            connect_result = await connect_to_server("http://test.example.com/mcp")
            assert connect_result["success"] is True
            assert connect_result["connection"]["server_url"] == "http://test.example.com/mcp"

            # Step 2: List tools
            tools_result = await list_tools()
            assert tools_result["success"] is True
            assert len(tools_result["tools"]) == 1
            assert tools_result["tools"][0]["name"] == "add"
            assert "input_schema" in tools_result["tools"][0]

            # Step 3: Call tool
            call_result = await call_tool("add", {"a": 5, "b": 3})
            assert call_result["success"] is True
            assert call_result["tool_call"]["tool_name"] == "add"
            assert call_result["tool_call"]["result"] == "8"
            assert "execution" in call_result["tool_call"]
            assert "duration_ms" in call_result["tool_call"]["execution"]

            # Step 4: Verify connection status
            status_result = await get_connection_status()
            assert status_result["connected"] is True
            # Only call_tool increments tools_called, not list_tools
            assert status_result["connection"]["statistics"]["tools_called"] == 1

            # Step 5: Disconnect
            disconnect_result = await disconnect()
            assert disconnect_result["success"] is True

            # Step 6: Verify disconnected
            final_status = await get_connection_status()
            assert final_status["connected"] is False

    @pytest.mark.asyncio
    async def test_tool_error_recovery(self):
        """Test error recovery when calling tools."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        # First call fails, second succeeds
        error_result = MagicMock()
        mock_client.call_tool = AsyncMock(side_effect=[
            Exception("Cannot divide by zero"),
            MagicMock(content=[MagicMock(text="3")]),
        ])

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp")

            # Call that fails
            error_result = await call_tool("divide", {"a": 10, "b": 0})
            assert error_result["success"] is False
            assert error_result["error"]["error_type"] in ["execution_error", "tool_execution_failed"]

            # Verify error was counted
            status = await get_connection_status()
            assert status["connection"]["statistics"]["errors"] == 1

            # Call that succeeds
            success_result = await call_tool("add", {"a": 1, "b": 2})
            assert success_result["success"] is True

            await disconnect()


class TestResourceWorkflows:
    """Integration tests for complete resource workflows."""

    @pytest.mark.asyncio
    async def test_full_resource_workflow(self):
        """Test complete connect → list_resources → read_resource → disconnect workflow."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        # Mock list_resources
        resource1 = MagicMock()
        resource1.uri = "config://settings"
        resource1.name = "Settings"
        resource1.mimeType = "application/json"
        resource1.description = "App settings"

        resources_result = MagicMock()
        resources_result.resources = [resource1]
        mock_client.list_resources = AsyncMock(return_value=resources_result)

        # Mock read_resource
        content_item = MagicMock()
        content_item.text = '{"theme": "dark"}'
        content_item.mimeType = "application/json"

        read_result = MagicMock()
        read_result.contents = [content_item]
        mock_client.read_resource = AsyncMock(return_value=read_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # Connect
            await connect_to_server("http://test.example.com/mcp")

            # List resources
            list_result = await list_resources()
            assert list_result["success"] is True
            assert len(list_result["resources"]) == 1
            assert list_result["resources"][0]["uri"] == "config://settings"

            # Read resource
            read_result = await read_resource("config://settings")
            assert read_result["success"] is True
            assert read_result["resource"]["uri"] == "config://settings"
            assert read_result["resource"]["content"] is not None

            # Verify statistics
            status = await get_connection_status()
            # Only read_resource increments counter, not list_resources
            assert status["connection"]["statistics"]["resources_accessed"] == 1

            await disconnect()

    @pytest.mark.asyncio
    async def test_resource_multiple_reads(self):
        """Test reading multiple resources in sequence."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        # Mock read_resource
        content_item = MagicMock()
        content_item.text = '{"data": "test"}'
        content_item.mimeType = "application/json"

        read_result = MagicMock()
        read_result.contents = [content_item]
        mock_client.read_resource = AsyncMock(return_value=read_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp")

            # Read multiple resources
            result1 = await read_resource("config://settings")
            assert result1["success"] is True

            result2 = await read_resource("data://users")
            assert result2["success"] is True

            # Verify statistics accumulated
            status = await get_connection_status()
            assert status["connection"]["statistics"]["resources_accessed"] == 2

            await disconnect()


class TestPromptWorkflows:
    """Integration tests for complete prompt workflows."""

    @pytest.mark.asyncio
    async def test_full_prompt_workflow(self):
        """Test complete connect → list_prompts → get_prompt → disconnect workflow."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        # Mock list_prompts
        prompt1 = MagicMock()
        prompt1.name = "greeting"
        prompt1.description = "Generate a greeting"
        prompt1.arguments = []

        prompts_result = MagicMock()
        prompts_result.prompts = [prompt1]
        mock_client.list_prompts = AsyncMock(return_value=prompts_result)

        # Mock get_prompt
        message = MagicMock()
        message.role = "user"
        message.content.text = "Hello, Alice!"

        get_result = MagicMock()
        get_result.messages = [message]
        mock_client.get_prompt = AsyncMock(return_value=get_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp")

            # List prompts
            list_result = await list_prompts()
            assert list_result["success"] is True
            assert len(list_result["prompts"]) == 1
            assert list_result["prompts"][0]["name"] == "greeting"

            # Get prompt
            get_result = await get_prompt("greeting", {"name": "Alice"})
            assert get_result["success"] is True
            assert get_result["prompt"]["name"] == "greeting"

            # Verify statistics
            status = await get_connection_status()
            # Only get_prompt increments counter, not list_prompts
            assert status["connection"]["statistics"]["prompts_executed"] == 1

            await disconnect()


class TestMixedWorkflows:
    """Integration tests for workflows using multiple capabilities."""

    @pytest.mark.asyncio
    async def test_mixed_operations_workflow(self):
        """Test workflow using tools, resources, and prompts together."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        # Setup all mocks
        tools_result = MagicMock()
        tools_result.tools = []
        mock_client.list_tools = AsyncMock(return_value=tools_result)

        tool_result = MagicMock()
        tool_result.content = [MagicMock(text="20")]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        resources_result = MagicMock()
        resources_result.resources = []
        mock_client.list_resources = AsyncMock(return_value=resources_result)

        read_result = MagicMock()
        read_result.contents = [MagicMock(text='{}', mimeType="application/json")]
        mock_client.read_resource = AsyncMock(return_value=read_result)

        prompts_result = MagicMock()
        prompts_result.prompts = []
        mock_client.list_prompts = AsyncMock(return_value=prompts_result)

        get_prompt_result = MagicMock()
        get_prompt_result.messages = [MagicMock(role="user", content=MagicMock(text="Hi"))]
        mock_client.get_prompt = AsyncMock(return_value=get_prompt_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            await connect_to_server("http://test.example.com/mcp")

            # Use tools
            await list_tools()
            await call_tool("multiply", {"a": 4, "b": 5})

            # Use resources
            await list_resources()
            await read_resource("config://settings")

            # Use prompts
            await list_prompts()
            await get_prompt("greeting", {"name": "Bob"})

            # Verify all statistics accumulated
            final_status = await get_connection_status()
            # Only actual operations increment counters, not list operations
            assert final_status["connection"]["statistics"]["tools_called"] == 1  # call_tool only
            assert final_status["connection"]["statistics"]["resources_accessed"] == 1  # read_resource only
            assert final_status["connection"]["statistics"]["prompts_executed"] == 1  # get_prompt only

            await disconnect()

    @pytest.mark.asyncio
    async def test_state_consistency_across_operations(self):
        """Test that connection state remains consistent throughout operations."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        tool_result = MagicMock()
        tool_result.content = [MagicMock(text="result")]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # Connect
            connect_result = await connect_to_server("http://test.example.com/mcp")
            initial_url = connect_result["connection"]["server_url"]

            # Perform multiple operations
            for i in range(5):
                result = await call_tool("add", {"a": i, "b": i})
                assert result["success"] is True

            # Final status check
            final_status = await get_connection_status()
            assert final_status["connection"]["server_url"] == initial_url
            assert final_status["connection"]["statistics"]["tools_called"] == 5

            await disconnect()


class TestConnectionErrors:
    """Integration tests for connection error scenarios."""

    @pytest.mark.asyncio
    async def test_operations_without_connection(self):
        """Test that operations fail gracefully when not connected."""
        # Ensure no connection
        await disconnect()

        # Try various operations
        result = await list_tools()
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await call_tool("add", {"a": 1, "b": 2})
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await list_resources()
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await read_resource("config://settings")
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await list_prompts()
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

        result = await get_prompt("greeting", {"name": "Test"})
        assert result["success"] is False
        assert result["error"]["error_type"] == "not_connected"

    @pytest.mark.asyncio
    async def test_reconnect_workflow(self):
        """Test connecting, disconnecting, and reconnecting."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)

        mock_session = MagicMock()
        mock_session.server_info.name = "test-server"
        mock_session.server_info.version = "1.0.0"
        mock_session.server_capabilities.tools = {"listChanged": True}
        mock_session.server_capabilities.resources = {"subscribe": True}
        mock_session.server_capabilities.prompts = {"listChanged": True}
        mock_client._session = mock_session

        tool_result = MagicMock()
        tool_result.content = [MagicMock(text="2")]
        mock_client.call_tool = AsyncMock(return_value=tool_result)

        with patch("mcp_test_mcp.connection.Client", return_value=mock_client):
            # First connection
            result1 = await connect_to_server("http://server1.example.com/mcp")
            assert result1["success"] is True

            # Do some work
            await call_tool("add", {"a": 1, "b": 1})

            # Disconnect
            await disconnect()

            # Verify disconnected
            status = await get_connection_status()
            assert status["connected"] is False

            # Reconnect to different server
            result2 = await connect_to_server("http://server2.example.com/mcp")
            assert result2["success"] is True
            assert result2["connection"]["server_url"] == "http://server2.example.com/mcp"

            # Verify statistics reset
            assert result2["connection"]["statistics"]["tools_called"] == 0

            await disconnect()

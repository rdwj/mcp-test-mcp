"""Tests for tool testing tools.

This module contains unit and integration tests for the tool testing tools:
list_tools and call_tool.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import Tool as McpTool

from mcp_test_mcp.connection import ConnectionError, ConnectionManager
from mcp_test_mcp.models import ConnectionState
from mcp_test_mcp.tools.tools import call_tool, list_tools


@pytest.fixture
def mock_connection_state():
    """Create a mock ConnectionState for testing."""
    return ConnectionState(
        server_url="http://test.example.com/mcp",
        transport="streamable-http",
        connected_at=datetime.now(),
        server_info={"name": "test-server", "version": "1.0.0"},
        statistics={
            "tools_called": 5,
            "resources_accessed": 2,
            "prompts_executed": 1,
            "errors": 0,
        },
    )


@pytest.fixture
def mock_client():
    """Create a mock FastMCP Client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_tools_result():
    """Create a mock tools result from MCP server."""
    # Create mock Tool objects
    tool1 = MagicMock(spec=McpTool)
    tool1.name = "add"
    tool1.description = "Adds two numbers"
    tool1.inputSchema = MagicMock()
    tool1.inputSchema.model_dump.return_value = {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"},
        },
        "required": ["a", "b"],
    }

    tool2 = MagicMock(spec=McpTool)
    tool2.name = "echo"
    tool2.description = "Echoes a message"
    tool2.inputSchema = MagicMock()
    tool2.inputSchema.model_dump.return_value = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message to echo"},
        },
        "required": ["message"],
    }

    # client.list_tools() returns a list directly, not an object with .tools attribute
    return [tool1, tool2]


class TestListTools:
    """Tests for list_tools tool."""

    @pytest.mark.asyncio
    async def test_list_tools_success(
        self, mock_connection_state, mock_client, mock_tools_result
    ):
        """Test successful tool listing."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require:
            mock_client.list_tools = AsyncMock(return_value=mock_tools_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await list_tools()

            # Verify the call
            mock_client.list_tools.assert_called_once()

            # Verify response structure
            assert result["success"] is True
            assert "tools" in result
            assert len(result["tools"]) == 2

            # Verify first tool
            assert result["tools"][0]["name"] == "add"
            assert result["tools"][0]["description"] == "Adds two numbers"
            assert "input_schema" in result["tools"][0]
            assert result["tools"][0]["input_schema"]["type"] == "object"
            assert "a" in result["tools"][0]["input_schema"]["properties"]

            # Verify second tool
            assert result["tools"][1]["name"] == "echo"
            assert result["tools"][1]["description"] == "Echoes a message"

            # Verify metadata
            assert "metadata" in result
            assert result["metadata"]["total_tools"] == 2
            assert result["metadata"]["server_url"] == "http://test.example.com/mcp"
            assert "request_time_ms" in result["metadata"]
            assert "retrieved_at" in result["metadata"]
            assert result["metadata"]["server_name"] == "test-server"

    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self):
        """Test listing tools when not connected."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require:
            mock_require.side_effect = ConnectionError(
                "Not connected to any MCP server. Use connect() first."
            )

            result = await list_tools()

            # Verify error response
            assert result["success"] is False
            assert "error" in result
            assert result["error"]["error_type"] == "not_connected"
            assert "Not connected" in result["error"]["message"]
            assert "connect_to_server()" in result["error"]["suggestion"]
            assert result["tools"] == []

    @pytest.mark.asyncio
    async def test_list_tools_execution_error(
        self, mock_connection_state, mock_client
    ):
        """Test handling of execution errors when listing tools."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.list_tools = AsyncMock(
                side_effect=Exception("Server error")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await list_tools()

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "execution_error"
            assert "Failed to list tools" in result["error"]["message"]
            assert "Server error" in result["error"]["message"]

            # Verify error counter was incremented
            mock_increment.assert_called_once_with("errors")

    @pytest.mark.asyncio
    async def test_list_tools_empty_result(
        self, mock_connection_state, mock_client
    ):
        """Test listing tools when server has no tools."""
        # client.list_tools() returns a list directly
        empty_result = []

        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require:
            mock_client.list_tools = AsyncMock(return_value=empty_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await list_tools()

            # Verify response
            assert result["success"] is True
            assert result["tools"] == []
            assert result["metadata"]["total_tools"] == 0


class TestCallTool:
    """Tests for call_tool tool."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_connection_state, mock_client):
        """Test successful tool execution."""
        # Mock tool result
        tool_result = MagicMock()
        content_item = MagicMock()
        content_item.text = "8"
        tool_result.content = [content_item]

        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.call_tool = AsyncMock(return_value=tool_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await call_tool("add", {"a": 5, "b": 3})

            # Verify the call
            mock_client.call_tool.assert_called_once_with("add", {"a": 5, "b": 3})

            # Verify statistics were updated
            mock_increment.assert_called_once_with("tools_called")

            # Verify response structure
            assert result["success"] is True
            assert "tool_call" in result
            assert result["tool_call"]["tool_name"] == "add"
            assert result["tool_call"]["arguments"] == {"a": 5, "b": 3}
            assert result["tool_call"]["result"] == "8"

            # Verify execution metadata
            assert "execution" in result["tool_call"]
            assert result["tool_call"]["execution"]["success"] is True
            assert "duration_ms" in result["tool_call"]["execution"]

            # Verify overall metadata
            assert "metadata" in result
            assert "request_time_ms" in result["metadata"]
            assert result["metadata"]["server_url"] == "http://test.example.com/mcp"
            assert "connection_statistics" in result["metadata"]

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        """Test calling a tool when not connected."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require:
            mock_require.side_effect = ConnectionError(
                "Not connected to any MCP server. Use connect() first."
            )

            result = await call_tool("add", {"a": 5, "b": 3})

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "not_connected"
            assert "Not connected" in result["error"]["message"]
            assert "connect_to_server()" in result["error"]["suggestion"]
            assert result["tool_call"] is None

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, mock_connection_state, mock_client):
        """Test calling a tool that doesn't exist."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.call_tool = AsyncMock(
                side_effect=Exception("Tool not found: invalid_tool")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await call_tool("invalid_tool", {})

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "tool_not_found"
            assert "invalid_tool" in result["error"]["message"]
            assert "list_tools()" in result["error"]["suggestion"]

            # Verify error counter was incremented
            mock_increment.assert_called_once_with("errors")

    @pytest.mark.asyncio
    async def test_call_tool_invalid_arguments(
        self, mock_connection_state, mock_client
    ):
        """Test calling a tool with invalid arguments."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.call_tool = AsyncMock(
                side_effect=Exception("Invalid argument: expected number, got string")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await call_tool("add", {"a": "invalid", "b": 3})

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "invalid_arguments"
            assert "Invalid argument" in result["error"]["message"]
            assert "schema" in result["error"]["suggestion"].lower()

            # Verify error counter was incremented
            mock_increment.assert_called_once_with("errors")

    @pytest.mark.asyncio
    async def test_call_tool_execution_error(
        self, mock_connection_state, mock_client
    ):
        """Test handling of tool execution errors."""
        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.call_tool = AsyncMock(
                side_effect=Exception("Division by zero")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await call_tool("divide", {"a": 10, "b": 0})

            # Verify error response
            assert result["success"] is False
            assert result["error"]["error_type"] == "execution_error"
            assert "Division by zero" in result["error"]["message"]

            # Verify error counter was incremented
            mock_increment.assert_called_once_with("errors")

    @pytest.mark.asyncio
    async def test_call_tool_with_data_content(
        self, mock_connection_state, mock_client
    ):
        """Test tool execution with data content instead of text."""
        # Mock tool result with data content
        tool_result = MagicMock()
        content_item = MagicMock()
        content_item.text = None
        content_item.data = {"result": 42}
        del content_item.text  # Remove text attribute
        tool_result.content = [content_item]

        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ):
            mock_client.call_tool = AsyncMock(return_value=tool_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await call_tool("get_data", {})

            # Verify response
            assert result["success"] is True
            assert result["tool_call"]["result"] == {"result": 42}


class TestToolsIntegration:
    """Integration tests for tool testing workflow."""

    @pytest.mark.asyncio
    async def test_list_then_call_workflow(
        self, mock_connection_state, mock_client, mock_tools_result
    ):
        """Test workflow of listing tools then calling one."""
        # Mock tool result for call_tool
        tool_result = MagicMock()
        content_item = MagicMock()
        content_item.text = "8"
        tool_result.content = [content_item]

        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ):
            mock_client.list_tools = AsyncMock(return_value=mock_tools_result)
            mock_client.call_tool = AsyncMock(return_value=tool_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            # Step 1: List tools
            list_result = await list_tools()
            assert list_result["success"] is True
            assert len(list_result["tools"]) == 2
            tool_names = [t["name"] for t in list_result["tools"]]
            assert "add" in tool_names

            # Step 2: Find the add tool and get its schema
            add_tool = next(t for t in list_result["tools"] if t["name"] == "add")
            assert "a" in add_tool["input_schema"]["properties"]
            assert "b" in add_tool["input_schema"]["properties"]

            # Step 3: Call the add tool with proper arguments
            call_result = await call_tool("add", {"a": 5, "b": 3})
            assert call_result["success"] is True
            assert call_result["tool_call"]["result"] == "8"

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mock_connection_state, mock_client):
        """Test workflow with error and recovery."""
        # Mock results for multiple calls
        tool_result = MagicMock()
        content_item = MagicMock()
        content_item.text = "10"
        tool_result.content = [content_item]

        with patch.object(
            ConnectionManager, "require_connection"
        ) as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_require.return_value = (mock_client, mock_connection_state)

            # First call fails
            mock_client.call_tool = AsyncMock(
                side_effect=Exception("Invalid argument: expected number")
            )
            result1 = await call_tool("add", {"a": "invalid", "b": 3})
            assert result1["success"] is False
            assert result1["error"]["error_type"] == "invalid_arguments"

            # Second call succeeds
            mock_client.call_tool = AsyncMock(return_value=tool_result)
            result2 = await call_tool("add", {"a": 7, "b": 3})
            assert result2["success"] is True
            assert result2["tool_call"]["result"] == "10"

            # Verify statistics
            assert mock_increment.call_count >= 2  # At least 1 error + 1 tool call

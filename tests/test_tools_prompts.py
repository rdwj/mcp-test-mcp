"""Tests for prompt testing tools.

This module provides comprehensive unit and integration tests for the
list_prompts and get_prompt tools.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import Prompt as McpPrompt, PromptArgument

from mcp_test_mcp.connection import ConnectionError, ConnectionManager
from mcp_test_mcp.models import ConnectionState
from mcp_test_mcp.tools.prompts import get_prompt, list_prompts


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
def mock_prompts_result():
    """Create a mock prompts result from MCP server."""
    # Create mock Prompt objects
    arg1 = MagicMock(spec=PromptArgument)
    arg1.name = "name"
    arg1.description = "Person's name"
    arg1.required = True

    prompt1 = MagicMock(spec=McpPrompt)
    prompt1.name = "greeting"
    prompt1.description = "Generate a greeting"
    prompt1.arguments = [arg1]

    # client.list_prompts() returns a list directly, not an object with .prompts attribute
    return [prompt1]


class TestListPrompts:
    """Test suite for list_prompts tool."""

    async def test_list_prompts_not_connected(self):
        """Test list_prompts returns error when not connected."""
        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_require.side_effect = ConnectionError(
                "Not connected to any MCP server. Use connect() first."
            )

            result = await list_prompts()

            assert result["success"] is False
            assert result["error"]["error_type"] == "not_connected"
            assert "not connected" in result["error"]["message"].lower()
            assert result["prompts"] == []

    async def test_list_prompts_success(
        self, mock_connection_state, mock_client, mock_prompts_result
    ):
        """Test list_prompts successfully retrieves prompts from mock server."""
        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_client.list_prompts = AsyncMock(return_value=mock_prompts_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await list_prompts()

            mock_client.list_prompts.assert_called_once()
            assert result["success"] is True
            assert len(result["prompts"]) == 1
            assert result["prompts"][0]["name"] == "greeting"
            assert len(result["prompts"][0]["arguments"]) == 1
            assert result["prompts"][0]["arguments"][0]["name"] == "name"


class TestGetPrompt:
    """Test suite for get_prompt tool."""

    async def test_get_prompt_not_connected(self):
        """Test get_prompt returns error when not connected."""
        with patch.object(ConnectionManager, "require_connection") as mock_require:
            mock_require.side_effect = ConnectionError(
                "Not connected to any MCP server. Use connect() first."
            )

            result = await get_prompt("greeting", {"name": "Alice"})

            assert result["success"] is False
            assert result["error"]["error_type"] == "not_connected"
            assert result["prompt"] is None

    async def test_get_prompt_success(self, mock_connection_state, mock_client):
        """Test get_prompt successfully retrieves rendered prompt from mock server."""
        prompt_result = MagicMock()
        prompt_result.description = "Generate a greeting"
        
        message = MagicMock()
        message.role = "user"
        message_content = MagicMock()
        message_content.type = "text"
        message_content.text = "Hello, Alice!"
        message.content = message_content
        prompt_result.messages = [message]

        with patch.object(ConnectionManager, "require_connection") as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.get_prompt = AsyncMock(return_value=prompt_result)
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await get_prompt("greeting", {"name": "Alice"})

            mock_client.get_prompt.assert_called_once_with("greeting", {"name": "Alice"})
            mock_increment.assert_called_once_with("prompts_executed")
            assert result["success"] is True
            assert result["prompt"]["name"] == "greeting"
            assert len(result["prompt"]["messages"]) == 1

    async def test_get_prompt_not_found(self, mock_connection_state, mock_client):
        """Test get_prompt handles non-existent prompt correctly."""
        with patch.object(ConnectionManager, "require_connection") as mock_require, patch.object(
            ConnectionManager, "increment_stat"
        ) as mock_increment:
            mock_client.get_prompt = AsyncMock(
                side_effect=Exception("Prompt not found: nonexistent_prompt")
            )
            mock_require.return_value = (mock_client, mock_connection_state)

            result = await get_prompt("nonexistent_prompt", {})

            assert result["success"] is False
            assert result["error"]["error_type"] == "prompt_not_found"
            assert "list_prompts()" in result["error"]["suggestion"]
            mock_increment.assert_called_once_with("errors")

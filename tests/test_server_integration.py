"""
Integration tests for the FastMCP server.

These tests verify that the server starts correctly and responds to basic
tool calls using in-memory transport.
"""

import pytest
from fastmcp import Client


@pytest.mark.asyncio
async def test_server_starts_and_responds():
    """Test that the server instance can be imported and started."""
    from mcp_test_mcp.server import mcp

    # Verify the server instance exists and has the correct name
    assert mcp is not None
    assert mcp.name == "mcp-test-mcp"


@pytest.mark.asyncio
async def test_health_check_tool():
    """Test the health_check tool returns expected status."""
    from mcp_test_mcp.server import mcp

    # Use in-memory transport for testing
    async with Client(mcp) as client:
        # Call the health_check tool
        result = await client.call_tool("health_check", {})

        # Verify the response
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert result.data["status"] == "healthy"
        assert result.data["server"] == "mcp-test-mcp"
        assert "version" in result.data
        assert "transport" in result.data


@pytest.mark.asyncio
async def test_ping_tool():
    """Test the ping tool returns 'pong'."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        result = await client.call_tool("ping", {})

        assert result.data == "pong"


@pytest.mark.asyncio
async def test_echo_tool():
    """Test the echo tool returns the input message."""
    from mcp_test_mcp.server import mcp

    test_message = "Hello, FastMCP!"

    async with Client(mcp) as client:
        result = await client.call_tool("echo", {"message": test_message})

        assert result.data == test_message


@pytest.mark.asyncio
async def test_add_tool():
    """Test the add tool correctly adds two numbers."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 5, "b": 3})

        assert result.data == 8


@pytest.mark.asyncio
async def test_list_tools():
    """Test that all expected tools are registered."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        tools = await client.list_tools()

        # Get tool names
        tool_names = [tool.name for tool in tools]

        # Verify all expected tools are present
        expected_tools = ["health_check", "ping", "echo", "add"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool '{expected_tool}' not found"


@pytest.mark.asyncio
async def test_server_ping():
    """Test basic server connectivity using the ping method."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        # Test basic server ping
        result = await client.ping()

        assert result is True


@pytest.mark.asyncio
async def test_tool_descriptions():
    """Test that tools have proper descriptions."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        tools = await client.list_tools()

        # Verify each tool has a description
        for tool in tools:
            assert tool.description is not None, f"Tool '{tool.name}' missing description"
            assert len(tool.description) > 0, f"Tool '{tool.name}' has empty description"


@pytest.mark.asyncio
async def test_error_handling_with_invalid_parameters():
    """Test that the server handles invalid parameters gracefully."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        # Try to call add with wrong parameter types (should be caught by FastMCP validation)
        with pytest.raises(Exception):  # FastMCP will raise validation errors
            await client.call_tool("add", {"a": "not_a_number", "b": 3})


@pytest.mark.asyncio
async def test_multiple_sequential_calls():
    """Test that the server can handle multiple sequential tool calls."""
    from mcp_test_mcp.server import mcp

    async with Client(mcp) as client:
        # Make multiple calls in sequence
        result1 = await client.call_tool("ping", {})
        result2 = await client.call_tool("echo", {"message": "test1"})
        result3 = await client.call_tool("add", {"a": 10, "b": 20})

        assert result1.data == "pong"
        assert result2.data == "test1"
        assert result3.data == 30

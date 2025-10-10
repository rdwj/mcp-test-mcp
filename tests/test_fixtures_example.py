"""Example integration tests demonstrating fixture usage.

This module provides example tests showing how to use the pytest fixtures
defined in conftest.py for testing MCP server functionality.
"""

import pytest
from fastmcp import Client

from mcp_test_mcp.connection import ConnectionManager


async def test_mock_server_tools(mock_mcp_server):
    """Test that mock server tools work correctly.

    This example demonstrates how to use the mock_mcp_server fixture
    to test tool functionality without requiring a real external server.
    """
    # Verify the mock server has the expected tools defined
    from fastmcp import FastMCP
    assert isinstance(mock_mcp_server, FastMCP)

    # Connect a client directly to the mock server (in-memory transport)
    async with Client(mock_mcp_server) as client:
        # List available tools
        tools_list = await client.list_tools()
        tool_names = [tool.name for tool in tools_list]

        # Verify expected tools are present
        assert "add" in tool_names
        assert "multiply" in tool_names
        assert "divide" in tool_names


async def test_mock_server_resources(mock_mcp_server):
    """Test that mock server resources work correctly.

    This example demonstrates how to test resource functionality
    using the mock_mcp_server fixture.
    """
    # Verify the mock server has resources defined
    from fastmcp import FastMCP
    assert isinstance(mock_mcp_server, FastMCP)

    async with Client(mock_mcp_server) as client:
        # List available resources
        resources_list = await client.list_resources()
        resource_uris = [str(resource.uri) for resource in resources_list]

        # Verify expected resources are present
        assert "config://settings" in resource_uris
        assert "data://users" in resource_uris


async def test_mock_server_prompts(mock_mcp_server):
    """Test that mock server prompts work correctly.

    This example demonstrates how to test prompt functionality
    using the mock_mcp_server fixture.
    """
    # Verify the mock server has prompts defined
    from fastmcp import FastMCP
    assert isinstance(mock_mcp_server, FastMCP)

    async with Client(mock_mcp_server) as client:
        # List available prompts
        prompts_list = await client.list_prompts()
        prompt_names = [prompt.name for prompt in prompts_list]

        # Verify expected prompts are present
        assert "greeting" in prompt_names


async def test_connection_cleanup_isolation(isolated_connection_manager):
    """Test that connection cleanup ensures test isolation.

    This example demonstrates how the connection_cleanup fixture
    ensures that connection state doesn't leak between tests.
    """
    # Initially, no connection should exist
    status = isolated_connection_manager.get_status()
    assert status is None

    # This test doesn't create a connection, but the cleanup fixture
    # will still run after the test to ensure any connections are cleaned up

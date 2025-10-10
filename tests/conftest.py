"""Pytest fixtures for mcp-test-mcp testing.

This module provides reusable fixtures for testing MCP server functionality,
including a mock MCP server with sample tools, resources, and prompts.
"""

import asyncio
import json
from typing import Any

import pytest
from fastmcp import Context, FastMCP

from mcp_test_mcp.connection import ConnectionManager


@pytest.fixture
async def mock_mcp_server():
    """Create a mock MCP server for testing.

    This fixture provides a FastMCP server instance with sample tools, resources,
    and prompts for comprehensive integration testing. The server includes:

    Tools:
    - add(a: int, b: int) -> int: Add two numbers
    - multiply(a: int, b: int) -> int: Multiply two numbers
    - divide(a: int, b: int) -> float: Divide two numbers

    Resources:
    - config://settings: Application settings (JSON)
    - data://users: User data list (JSON)

    Prompts:
    - greeting(name: str): Generate a greeting message

    Returns:
        FastMCP server instance configured with sample components

    Example:
        async def test_example(mock_mcp_server):
            # Use in-memory transport by passing server directly to Client
            async with Client(mock_mcp_server) as client:
                result = await client.call_tool("add", {"a": 2, "b": 3})
                # result.content[0].text contains the string representation
    """
    mcp = FastMCP(name="test-server")

    # Sample tools
    @mcp.tool()
    async def add(a: int, b: int) -> int:
        """Add two integer numbers together.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        return a + b

    @mcp.tool()
    async def multiply(a: int, b: int) -> int:
        """Multiply two integer numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b
        """
        return a * b

    @mcp.tool()
    async def divide(a: int, b: int) -> float:
        """Divide two numbers.

        Args:
            a: Numerator
            b: Denominator

        Returns:
            Quotient of a divided by b

        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    # Sample resources
    @mcp.resource(
        "config://settings",
        name="Application Settings",
        description="Configuration settings for the test application",
        mime_type="application/json",
    )
    def get_settings() -> dict[str, Any]:
        """Provide application configuration settings."""
        return {
            "theme": "dark",
            "version": "1.2.0",
            "features": ["tools", "resources", "prompts"],
            "debug": False,
        }

    @mcp.resource(
        "data://users",
        name="User Data",
        description="Sample user data list",
        mime_type="application/json",
    )
    def get_users() -> list[dict[str, Any]]:
        """Provide sample user data."""
        return [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]

    # Sample prompts
    @mcp.prompt(
        name="greeting",
        description="Generate a personalized greeting message",
    )
    def greeting_prompt(name: str) -> str:
        """Generate a greeting for the specified person.

        Args:
            name: Name of the person to greet

        Returns:
            Greeting message string
        """
        return f"Hello, {name}! Welcome to the test server."

    return mcp


@pytest.fixture
async def connection_cleanup():
    """Fixture to ensure ConnectionManager is cleaned up after tests.

    This fixture runs after each test to disconnect any active connections
    and reset the global connection state, ensuring test isolation.

    Example:
        async def test_connection(connection_cleanup):
            # Test code here
            # Connection will be cleaned up automatically after test
    """
    yield
    # Cleanup after test
    await ConnectionManager.disconnect()


@pytest.fixture
async def isolated_connection_manager(connection_cleanup):
    """Fixture providing ConnectionManager with automatic cleanup.

    Combines ConnectionManager access with automatic cleanup after the test,
    ensuring no connection state leaks between tests.

    Returns:
        ConnectionManager class for use in tests

    Example:
        async def test_status(isolated_connection_manager):
            status = isolated_connection_manager.get_status()
            assert status is None  # No connection initially
    """
    return ConnectionManager

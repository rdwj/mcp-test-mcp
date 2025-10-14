"""Tool testing tools for MCP server testing.

This module provides MCP tools for discovering and executing tools on connected
target MCP servers, enabling comprehensive tool testing workflows.
"""

import logging
import time
from typing import Annotated, Any

from fastmcp import Context

from ..connection import ConnectionError, ConnectionManager
from ..mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool
async def list_tools(ctx: Context) -> dict[str, Any]:
    """List all tools available on the connected MCP server.

    Retrieves comprehensive information about all tools exposed by the target
    server, including full input schemas to enable accurate tool invocation.

    Returns:
        Dictionary with tool listing including:
        - success: True on successful retrieval
        - tools: List of tool objects with name, description, and full input_schema
        - metadata: Total count, server info, timing information

    Raises:
        Returns error dict if not connected or retrieval fails
    """
    start_time = time.perf_counter()

    try:
        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        # User-facing progress update
        await ctx.info("Listing tools from connected MCP server")
        # Detailed technical log
        logger.info("Listing tools from connected MCP server")

        # Get tools from the server
        tools_result = await client.list_tools()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Convert tools to dictionary format with full schemas
        # Note: client.list_tools() returns a list directly, not an object with .tools
        tools_list = []
        for tool in tools_result:
            # inputSchema is already a dict, not a Pydantic model
            input_schema = tool.inputSchema if hasattr(tool, "inputSchema") and tool.inputSchema else {}

            tool_dict = {
                "name": tool.name,
                "description": tool.description if tool.description else "",
                "input_schema": input_schema,
            }
            tools_list.append(tool_dict)

        metadata = {
            "total_tools": len(tools_list),
            "server_url": state.server_url,
            "retrieved_at": time.time(),
            "request_time_ms": round(elapsed_ms, 2),
        }

        # Add server info if available
        if state.server_info:
            metadata["server_name"] = state.server_info.get("name", "unknown")
            metadata["server_version"] = state.server_info.get("version")

        # User-facing success update
        await ctx.info(f"Retrieved {len(tools_list)} tools from server")
        # Detailed technical log
        logger.info(
            f"Retrieved {len(tools_list)} tools from server",
            extra={
                "tool_count": len(tools_list),
                "server_url": state.server_url,
                "duration_ms": elapsed_ms,
            },
        )

        return {
            "success": True,
            "tools": tools_list,
            "metadata": metadata,
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Not connected: {str(e)}")
        # Detailed technical log
        logger.error(f"Not connected: {str(e)}", extra={"duration_ms": elapsed_ms})

        return {
            "success": False,
            "error": {
                "error_type": "not_connected",
                "message": str(e),
                "details": {},
                "suggestion": "Use connect_to_server() to establish a connection first",
            },
            "tools": [],
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Failed to list tools: {str(e)}")
        # Detailed technical log
        logger.exception("Failed to list tools", extra={"duration_ms": elapsed_ms})

        # Increment error counter
        ConnectionManager.increment_stat("errors")

        return {
            "success": False,
            "error": {
                "error_type": "execution_error",
                "message": f"Failed to list tools: {str(e)}",
                "details": {"exception_type": type(e).__name__},
                "suggestion": "Check that the server supports the tools capability and is responding correctly",
            },
            "tools": [],
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }


@mcp.tool
async def call_tool(
    name: Annotated[str, "Name of the tool to execute on the target MCP server"],
    arguments: Annotated[dict[str, Any], "Dictionary of arguments to pass to the tool"],
    ctx: Context
) -> dict[str, Any]:
    """Execute a tool on the connected MCP server.

    Calls a tool by name with the provided arguments and returns the result
    along with execution timing and metadata.

    Returns:
        Dictionary with tool execution results including:
        - success: True if tool executed successfully
        - tool_call: Object with tool_name, arguments, result, and execution metadata
        - metadata: Request timing and server information

    Raises:
        Returns error dict for various failure scenarios:
        - not_connected: No active connection
        - tool_not_found: Tool doesn't exist on server
        - invalid_arguments: Arguments don't match tool schema
        - execution_error: Tool execution failed
    """
    start_time = time.perf_counter()

    try:
        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        # User-facing progress update
        await ctx.info(f"Calling tool '{name}' on target server")
        # Detailed technical log
        logger.info(
            f"Calling tool '{name}' with arguments",
            extra={"tool_name": name, "arguments": arguments},
        )

        # Execute the tool
        tool_start = time.perf_counter()
        result = await client.call_tool(name, arguments)
        tool_elapsed_ms = (time.perf_counter() - tool_start) * 1000

        # Increment statistics
        ConnectionManager.increment_stat("tools_called")

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Extract result content
        result_content = None
        if hasattr(result, "content") and result.content:
            # Handle list of content items
            if isinstance(result.content, list) and len(result.content) > 0:
                content_item = result.content[0]
                if hasattr(content_item, "text"):
                    result_content = content_item.text
                elif hasattr(content_item, "data"):
                    result_content = content_item.data
                else:
                    result_content = str(content_item)
            else:
                result_content = result.content
        elif hasattr(result, "result"):
            result_content = result.result
        else:
            result_content = str(result)

        # User-facing success update
        await ctx.info(f"Tool '{name}' executed successfully")
        # Detailed technical log
        logger.info(
            f"Tool '{name}' executed successfully",
            extra={
                "tool_name": name,
                "execution_ms": tool_elapsed_ms,
                "total_ms": total_elapsed_ms,
            },
        )

        return {
            "success": True,
            "tool_call": {
                "tool_name": name,
                "arguments": arguments,
                "result": result_content,
                "execution": {
                    "duration_ms": round(tool_elapsed_ms, 2),
                    "success": True,
                },
            },
            "metadata": {
                "request_time_ms": round(total_elapsed_ms, 2),
                "server_url": state.server_url,
                "connection_statistics": state.statistics,
            },
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Not connected when calling tool '{name}': {str(e)}")
        # Detailed technical log
        logger.error(
            f"Not connected when calling tool '{name}': {str(e)}",
            extra={"tool_name": name, "duration_ms": elapsed_ms},
        )

        return {
            "success": False,
            "error": {
                "error_type": "not_connected",
                "message": str(e),
                "details": {"tool_name": name},
                "suggestion": "Use connect_to_server() to establish a connection first",
            },
            "tool_call": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine error type based on exception message
        error_type = "execution_error"
        suggestion = "Check the tool name and arguments, then retry"

        error_msg = str(e).lower()
        if "not found" in error_msg or "unknown tool" in error_msg:
            error_type = "tool_not_found"
            suggestion = f"Tool '{name}' does not exist on the server. Use list_tools() to see available tools"
        elif "argument" in error_msg or "parameter" in error_msg or "validation" in error_msg:
            error_type = "invalid_arguments"
            suggestion = f"Arguments do not match the tool schema. Use list_tools() to see the correct schema for '{name}'"

        # User-facing error update
        await ctx.error(f"Failed to call tool '{name}': {str(e)}")
        # Detailed technical log
        logger.error(
            f"Failed to call tool '{name}': {str(e)}",
            extra={
                "tool_name": name,
                "arguments": arguments,
                "error_type": error_type,
                "duration_ms": elapsed_ms,
            },
        )

        # Increment error counter
        ConnectionManager.increment_stat("errors")

        return {
            "success": False,
            "error": {
                "error_type": error_type,
                "message": f"Failed to call tool '{name}': {str(e)}",
                "details": {
                    "tool_name": name,
                    "arguments": arguments,
                    "exception_type": type(e).__name__,
                },
                "suggestion": suggestion,
            },
            "tool_call": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

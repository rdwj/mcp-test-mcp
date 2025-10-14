"""Resource testing tools for MCP server testing.

This module provides MCP tools for discovering and reading resources from
connected target MCP servers, enabling comprehensive resource testing workflows.
"""

import logging
import time
from typing import Annotated, Any

from fastmcp import Context

from ..connection import ConnectionError, ConnectionManager
from ..mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool
async def list_resources(ctx: Context) -> dict[str, Any]:
    """List all resources available on the connected MCP server.

    Retrieves comprehensive information about all resources exposed by the target
    server, including URIs, names, descriptions, and MIME types to enable
    accurate resource access.

    Returns:
        Dictionary with resource listing including:
        - success: True on successful retrieval
        - resources: List of resource objects with uri, name, description, mimeType
        - metadata: Total count, server info, timing information

    Raises:
        Returns error dict if not connected or retrieval fails
    """
    start_time = time.perf_counter()

    try:
        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        # User-facing progress update
        await ctx.info("Listing resources from connected MCP server")
        # Detailed technical log
        logger.info("Listing resources from connected MCP server")

        # Get resources from the server
        resources_result = await client.list_resources()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Convert resources to dictionary format with full metadata
        # Note: client.list_resources() returns a list directly, not an object with .resources
        resources_list = []
        for resource in resources_result:
            resource_dict = {
                "uri": resource.uri,
                "name": resource.name if resource.name else "",
                "description": resource.description if resource.description else "",
                "mimeType": resource.mimeType if hasattr(resource, "mimeType") and resource.mimeType else None,
            }
            resources_list.append(resource_dict)

        metadata = {
            "total_resources": len(resources_list),
            "server_url": state.server_url,
            "retrieved_at": time.time(),
            "request_time_ms": round(elapsed_ms, 2),
        }

        # Add server info if available
        if state.server_info:
            metadata["server_name"] = state.server_info.get("name", "unknown")
            metadata["server_version"] = state.server_info.get("version")

        # User-facing success update
        await ctx.info(f"Retrieved {len(resources_list)} resources from server")
        # Detailed technical log
        logger.info(
            f"Retrieved {len(resources_list)} resources from server",
            extra={
                "resource_count": len(resources_list),
                "server_url": state.server_url,
                "duration_ms": elapsed_ms,
            },
        )

        return {
            "success": True,
            "resources": resources_list,
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
            "resources": [],
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Failed to list resources: {str(e)}")
        # Detailed technical log
        logger.exception("Failed to list resources", extra={"duration_ms": elapsed_ms})

        # Increment error counter
        ConnectionManager.increment_stat("errors")

        return {
            "success": False,
            "error": {
                "error_type": "execution_error",
                "message": f"Failed to list resources: {str(e)}",
                "details": {"exception_type": type(e).__name__},
                "suggestion": "Check that the server supports the resources capability and is responding correctly",
            },
            "resources": [],
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }


@mcp.tool
async def read_resource(
    uri: Annotated[str, "URI of the resource to read (e.g., 'config://settings')"],
    ctx: Context
) -> dict[str, Any]:
    """Read a specific resource from the connected MCP server.

    Reads a resource by URI and returns its content along with metadata.

    Returns:
        Dictionary with resource content including:
        - success: True if resource was read successfully
        - resource: Object with uri, mimeType, and content
        - metadata: Content size and request timing

    Raises:
        Returns error dict for various failure scenarios:
        - not_connected: No active connection
        - resource_not_found: Resource doesn't exist on server
        - execution_error: Resource read failed
    """
    start_time = time.perf_counter()

    try:
        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        # User-facing progress update
        await ctx.info(f"Reading resource '{uri}' from server")
        # Detailed technical log
        logger.info(
            f"Reading resource '{uri}' from server",
            extra={"resource_uri": uri},
        )

        # Read the resource
        # Note: FastMCP Client's read_resource() returns a list directly, not a ReadResourceResult
        resource_start = time.perf_counter()
        contents_list = await client.read_resource(uri)
        resource_elapsed_ms = (time.perf_counter() - resource_start) * 1000

        # Increment statistics
        ConnectionManager.increment_stat("resources_accessed")

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Extract resource content
        # FastMCP returns list[TextResourceContents | BlobResourceContents] directly
        content = None
        mime_type = None
        content_size = 0

        if isinstance(contents_list, list) and len(contents_list) > 0:
            content_item = contents_list[0]
            # Check for different content types
            if hasattr(content_item, "text"):
                content = content_item.text
                content_size = len(content) if content else 0
                mime_type = getattr(content_item, "mimeType", "text/plain")
            elif hasattr(content_item, "blob"):
                # For binary content, we'll encode as base64 string
                import base64
                content = base64.b64encode(content_item.blob).decode("utf-8")
                content_size = len(content_item.blob)
                mime_type = getattr(content_item, "mimeType", "application/octet-stream")
            else:
                content = str(content_item)
                content_size = len(content)

        # User-facing success update
        await ctx.info(f"Resource '{uri}' read successfully ({content_size} bytes)")
        # Detailed technical log
        logger.info(
            f"Resource '{uri}' read successfully",
            extra={
                "resource_uri": uri,
                "content_size": content_size,
                "duration_ms": resource_elapsed_ms,
            },
        )

        return {
            "success": True,
            "resource": {
                "uri": uri,
                "mimeType": mime_type,
                "content": content,
            },
            "metadata": {
                "content_size": content_size,
                "request_time_ms": round(total_elapsed_ms, 2),
                "server_url": state.server_url,
                "connection_statistics": state.statistics,
            },
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # User-facing error update
        await ctx.error(f"Not connected when reading resource '{uri}': {str(e)}")
        # Detailed technical log
        logger.error(
            f"Not connected when reading resource '{uri}': {str(e)}",
            extra={"resource_uri": uri, "duration_ms": elapsed_ms},
        )

        return {
            "success": False,
            "error": {
                "error_type": "not_connected",
                "message": str(e),
                "details": {"resource_uri": uri},
                "suggestion": "Use connect_to_server() to establish a connection first",
            },
            "resource": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine error type based on exception message
        error_type = "execution_error"
        suggestion = "Check the resource URI and retry"

        error_msg = str(e).lower()
        if "not found" in error_msg or "unknown resource" in error_msg or "no resource" in error_msg:
            error_type = "resource_not_found"
            suggestion = f"Resource '{uri}' does not exist on the server. Use list_resources() to see available resources"

        # User-facing error update
        await ctx.error(f"Failed to read resource '{uri}': {str(e)}")
        # Detailed technical log
        logger.error(
            f"Failed to read resource '{uri}': {str(e)}",
            extra={
                "resource_uri": uri,
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
                "message": f"Failed to read resource '{uri}': {str(e)}",
                "details": {
                    "resource_uri": uri,
                    "exception_type": type(e).__name__,
                },
                "suggestion": suggestion,
            },
            "resource": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

"""Prompt testing tools for MCP server testing.

This module provides MCP tools for discovering and retrieving prompts from
connected target MCP servers, enabling comprehensive prompt testing workflows.
"""

import logging
import time
from typing import Any

from ..connection import ConnectionError, ConnectionManager

logger = logging.getLogger(__name__)


async def list_prompts() -> dict[str, Any]:
    """List all prompts available on the connected MCP server.

    Retrieves comprehensive information about all prompts exposed by the target
    server, including names, descriptions, and complete argument schemas to enable
    accurate prompt invocation.

    Returns:
        Dictionary with prompt listing including:
        - success: True on successful retrieval
        - prompts: List of prompt objects with name, description, and arguments schema
        - metadata: Total count, server info, timing information

    Raises:
        Returns error dict if not connected or retrieval fails
    """
    start_time = time.perf_counter()

    try:
        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        logger.info("Listing prompts from connected MCP server")

        # Get prompts from the server
        prompts_result = await client.list_prompts()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Convert prompts to dictionary format with full argument schemas
        # Note: client.list_prompts() returns a list directly, not an object with .prompts
        prompts_list = []
        for prompt in prompts_result:
            # Extract arguments schema
            arguments = []
            if hasattr(prompt, "arguments") and prompt.arguments:
                for arg in prompt.arguments:
                    arg_dict = {
                        "name": arg.name,
                        "description": arg.description if arg.description else "",
                        "required": arg.required if hasattr(arg, "required") else False,
                    }
                    arguments.append(arg_dict)

            prompt_dict = {
                "name": prompt.name,
                "description": prompt.description if prompt.description else "",
                "arguments": arguments,
            }
            prompts_list.append(prompt_dict)

        metadata = {
            "total_prompts": len(prompts_list),
            "server_url": state.server_url,
            "retrieved_at": time.time(),
            "request_time_ms": round(elapsed_ms, 2),
        }

        # Add server info if available
        if state.server_info:
            metadata["server_name"] = state.server_info.get("name", "unknown")
            metadata["server_version"] = state.server_info.get("version")

        logger.info(
            f"Retrieved {len(prompts_list)} prompts from server",
            extra={
                "prompt_count": len(prompts_list),
                "server_url": state.server_url,
                "duration_ms": elapsed_ms,
            },
        )

        return {
            "success": True,
            "prompts": prompts_list,
            "metadata": metadata,
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.error(f"Not connected: {str(e)}", extra={"duration_ms": elapsed_ms})

        return {
            "success": False,
            "error": {
                "error_type": "not_connected",
                "message": str(e),
                "details": {},
                "suggestion": "Use connect_to_server() to establish a connection first",
            },
            "prompts": [],
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.exception("Failed to list prompts", extra={"duration_ms": elapsed_ms})

        # Increment error counter
        ConnectionManager.increment_stat("errors")

        return {
            "success": False,
            "error": {
                "error_type": "execution_error",
                "message": f"Failed to list prompts: {str(e)}",
                "details": {"exception_type": type(e).__name__},
                "suggestion": "Check that the server supports the prompts capability and is responding correctly",
            },
            "prompts": [],
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }


async def get_prompt(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Get a rendered prompt from the connected MCP server.

    Retrieves a prompt by name with the provided arguments and returns the
    rendered prompt messages.

    Args:
        name: Name of the prompt to retrieve
        arguments: Dictionary of arguments to pass to the prompt

    Returns:
        Dictionary with rendered prompt including:
        - success: True if prompt was retrieved successfully
        - prompt: Object with name, description, and rendered messages
        - metadata: Request timing and server information

    Raises:
        Returns error dict for various failure scenarios:
        - not_connected: No active connection
        - prompt_not_found: Prompt doesn't exist on server
        - invalid_arguments: Arguments don't match prompt schema
        - execution_error: Prompt retrieval failed
    """
    start_time = time.perf_counter()

    try:
        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        logger.info(
            f"Getting prompt '{name}' with arguments",
            extra={"prompt_name": name, "arguments": arguments},
        )

        # Get the prompt
        prompt_start = time.perf_counter()
        result = await client.get_prompt(name, arguments)
        prompt_elapsed_ms = (time.perf_counter() - prompt_start) * 1000

        # Increment statistics
        ConnectionManager.increment_stat("prompts_executed")

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Extract prompt messages
        messages = []
        if hasattr(result, "messages") and result.messages:
            for message in result.messages:
                message_dict: dict[str, Any] = {
                    "role": message.role,
                }
                # Handle different content types
                # Content can be: TextContent, ImageContent, AudioContent, ResourceLink, EmbeddedResource
                if hasattr(message, "content"):
                    content = message.content
                    if hasattr(content, "type"):
                        # Structured content with type discriminator
                        content_dict: dict[str, Any] = {
                            "type": content.type,
                        }
                        # Handle type-specific fields
                        if content.type == "text" and hasattr(content, "text"):
                            content_dict["text"] = content.text
                        elif content.type == "image" and hasattr(content, "data"):
                            content_dict["data"] = content.data
                            if hasattr(content, "mimeType"):
                                content_dict["mimeType"] = content.mimeType
                        elif content.type == "audio" and hasattr(content, "data"):
                            content_dict["data"] = content.data
                            if hasattr(content, "mimeType"):
                                content_dict["mimeType"] = content.mimeType
                        elif content.type == "resource":
                            # ResourceLink or EmbeddedResource
                            if hasattr(content, "uri"):
                                content_dict["uri"] = content.uri
                            if hasattr(content, "resource"):
                                content_dict["resource"] = content.resource
                        message_dict["content"] = content_dict
                    else:
                        # Fallback for simple/unknown content types
                        message_dict["content"] = {"type": "text", "text": str(content)}
                messages.append(message_dict)

        prompt_info = {
            "name": name,
            "description": result.description if hasattr(result, "description") and result.description else "",
            "messages": messages,
        }

        logger.info(
            f"Prompt '{name}' retrieved successfully",
            extra={
                "prompt_name": name,
                "message_count": len(messages),
                "duration_ms": prompt_elapsed_ms,
            },
        )

        return {
            "success": True,
            "prompt": prompt_info,
            "metadata": {
                "request_time_ms": round(total_elapsed_ms, 2),
                "server_url": state.server_url,
                "connection_statistics": state.statistics,
            },
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.error(
            f"Not connected when getting prompt '{name}': {str(e)}",
            extra={"prompt_name": name, "duration_ms": elapsed_ms},
        )

        return {
            "success": False,
            "error": {
                "error_type": "not_connected",
                "message": str(e),
                "details": {"prompt_name": name},
                "suggestion": "Use connect_to_server() to establish a connection first",
            },
            "prompt": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine error type based on exception message
        error_type = "execution_error"
        suggestion = "Check the prompt name and arguments, then retry"

        error_msg = str(e).lower()
        if "not found" in error_msg or "unknown prompt" in error_msg or "no prompt" in error_msg:
            error_type = "prompt_not_found"
            suggestion = f"Prompt '{name}' does not exist on the server. Use list_prompts() to see available prompts"
        elif "argument" in error_msg or "parameter" in error_msg or "validation" in error_msg or "required" in error_msg:
            error_type = "invalid_arguments"
            suggestion = f"Arguments do not match the prompt schema. Use list_prompts() to see the correct schema for '{name}'"

        logger.error(
            f"Failed to get prompt '{name}': {str(e)}",
            extra={
                "prompt_name": name,
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
                "message": f"Failed to get prompt '{name}': {str(e)}",
                "details": {
                    "prompt_name": name,
                    "arguments": arguments,
                    "exception_type": type(e).__name__,
                },
                "suggestion": suggestion,
            },
            "prompt": None,
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

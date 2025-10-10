"""Pydantic data models for MCP test server responses.

This module defines all data structures used for structured responses
from MCP server operations, including connection state, tool execution,
resource operations, and error handling.
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Error type definitions
ErrorType = Literal[
    "not_connected",
    "connection_failed",
    "tool_not_found",
    "resource_not_found",
    "prompt_not_found",
    "invalid_arguments",
    "execution_error",
    "timeout",
    "transport_error",
]


class ConnectionState(BaseModel):
    """Current state of an MCP server connection.

    This model captures all relevant information about an active
    or attempted connection to an MCP server.
    """

    server_url: str = Field(description="The URL or identifier of the MCP server")
    transport: Literal["stdio", "sse", "streamable-http"] = Field(
        description="The transport protocol used for communication"
    )
    connected_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when connection was established, None if not connected",
    )
    server_info: Optional[dict[str, Any]] = Field(
        default=None,
        description="Server metadata returned during initialization (name, version, capabilities)",
    )
    statistics: dict[str, int] = Field(
        default_factory=lambda: {
            "tools_called": 0,
            "resources_accessed": 0,
            "prompts_executed": 0,
            "errors": 0,
        },
        description="Usage statistics for this connection",
    )


class ToolResponse(BaseModel):
    """Response from listing or discovering MCP server tools.

    Returned when successfully querying available tools from
    a connected MCP server.
    """

    success: bool = Field(
        default=True,
        description="Indicates successful tool discovery",
    )
    connection: ConnectionState = Field(description="Current connection state")
    tools: list[dict[str, Any]] = Field(description="List of available tools with their schemas")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the tool discovery operation",
    )


class ToolCallResponse(BaseModel):
    """Response from executing a tool on an MCP server.

    Contains execution results, timing information, and updated
    connection state.
    """

    success: bool = Field(description="Indicates whether tool execution succeeded")
    connection: ConnectionState = Field(description="Updated connection state after tool execution")
    tool_name: str = Field(description="Name of the tool that was executed")
    result: Any = Field(description="Return value from the tool execution")
    execution_time_ms: float = Field(description="Time taken to execute the tool in milliseconds")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata (logs, warnings, etc.)",
    )


class ResourceResponse(BaseModel):
    """Response from MCP server resource operations.

    Used for listing available resources or reading resource content.
    """

    success: bool = Field(
        default=True,
        description="Indicates successful resource operation",
    )
    connection: ConnectionState = Field(description="Current connection state")
    resources: list[dict[str, Any]] = Field(description="List of resources or resource content")
    operation: Literal["list", "read"] = Field(
        description="The type of resource operation performed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the resource operation",
    )


class PromptResponse(BaseModel):
    """Response from MCP server prompt operations.

    Used for listing available prompts or executing prompts with arguments.
    """

    success: bool = Field(
        default=True,
        description="Indicates successful prompt operation",
    )
    connection: ConnectionState = Field(description="Current connection state")
    prompts: list[dict[str, Any]] = Field(description="List of prompts or prompt execution results")
    operation: Literal["list", "execute"] = Field(
        description="The type of prompt operation performed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the prompt operation",
    )


class ErrorDetail(BaseModel):
    """Detailed error information for failed operations.

    Provides structured error data including error type,
    messages, and suggestions for resolution.
    """

    error_type: ErrorType = Field(description="Categorized error type for programmatic handling")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error context (stack traces, validation errors, etc.)",
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggested action to resolve the error",
    )


class ErrorResponse(BaseModel):
    """Response for failed MCP operations.

    Returned when any MCP operation encounters an error,
    providing detailed error information and current connection state.
    """

    success: bool = Field(
        default=False,
        description="Always False for error responses",
    )
    error: ErrorDetail = Field(description="Detailed error information")
    connection: Optional[ConnectionState] = Field(
        default=None,
        description="Connection state if available, None if connection never established",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context about when/where the error occurred",
    )

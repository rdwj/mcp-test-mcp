"""Tests for Pydantic data models.

This module tests model instantiation, validation, field requirements,
and error handling for all MCP response models.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mcp_test_mcp.models import (
    ConnectionState,
    ErrorDetail,
    ErrorResponse,
    PromptResponse,
    ResourceResponse,
    ToolCallResponse,
    ToolResponse,
)


class TestConnectionState:
    """Tests for ConnectionState model."""

    def test_valid_connection_state_minimal(self) -> None:
        """Test creating connection state with minimal required fields."""
        state = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        assert state.server_url == "stdio://test-server"
        assert state.transport == "stdio"
        assert state.connected_at is None
        assert state.server_info is None
        assert state.statistics == {
            "tools_called": 0,
            "resources_accessed": 0,
            "prompts_executed": 0,
            "errors": 0,
        }

    def test_valid_connection_state_full(self) -> None:
        """Test creating connection state with all fields populated."""
        now = datetime.now(timezone.utc)
        state = ConnectionState(
            server_url="http://localhost:8000",
            transport="streamable-http",
            connected_at=now,
            server_info={
                "name": "test-server",
                "version": "1.0.0",
                "capabilities": ["tools", "resources"],
            },
            statistics={
                "tools_called": 5,
                "resources_accessed": 3,
                "prompts_executed": 2,
                "errors": 1,
            },
        )
        assert state.server_url == "http://localhost:8000"
        assert state.transport == "streamable-http"
        assert state.connected_at == now
        assert state.server_info is not None
        assert state.server_info["name"] == "test-server"
        assert state.statistics["tools_called"] == 5

    def test_invalid_transport_type(self) -> None:
        """Test that invalid transport types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionState(
                server_url="test://server",
                transport="invalid-transport",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "literal_error"
        assert "transport" in errors[0]["loc"]

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionState()  # type: ignore
        errors = exc_info.value.errors()
        assert len(errors) == 2  # server_url and transport
        field_names = {error["loc"][0] for error in errors}
        assert field_names == {"server_url", "transport"}


class TestToolResponse:
    """Tests for ToolResponse model."""

    def test_valid_tool_response(self) -> None:
        """Test creating a valid tool response."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        response = ToolResponse(
            connection=connection,
            tools=[
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "inputSchema": {"type": "object", "properties": {}},
                }
            ],
        )
        assert response.success is True
        assert len(response.tools) == 1
        assert response.tools[0]["name"] == "test_tool"
        assert response.metadata == {}

    def test_tool_response_with_metadata(self) -> None:
        """Test tool response with custom metadata."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        response = ToolResponse(
            connection=connection,
            tools=[],
            metadata={"query_time_ms": 50, "source": "cache"},
        )
        assert response.metadata["query_time_ms"] == 50
        assert response.metadata["source"] == "cache"

    def test_missing_connection(self) -> None:
        """Test that missing connection raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ToolResponse(tools=[])  # type: ignore
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"][0] == "connection"


class TestToolCallResponse:
    """Tests for ToolCallResponse model."""

    def test_valid_tool_call_response(self) -> None:
        """Test creating a valid tool call response."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        response = ToolCallResponse(
            success=True,
            connection=connection,
            tool_name="calculate",
            result={"answer": 42},
            execution_time_ms=125.5,
        )
        assert response.success is True
        assert response.tool_name == "calculate"
        assert response.result == {"answer": 42}
        assert response.execution_time_ms == 125.5

    def test_tool_call_response_with_failure(self) -> None:
        """Test tool call response for failed execution."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        response = ToolCallResponse(
            success=False,
            connection=connection,
            tool_name="failing_tool",
            result=None,
            execution_time_ms=10.2,
            metadata={"error": "Tool execution failed"},
        )
        assert response.success is False
        assert response.result is None
        assert response.metadata["error"] == "Tool execution failed"


class TestResourceResponse:
    """Tests for ResourceResponse model."""

    def test_valid_resource_list_response(self) -> None:
        """Test creating a resource list response."""
        connection = ConnectionState(
            server_url="http://localhost:8000",
            transport="streamable-http",
        )
        response = ResourceResponse(
            connection=connection,
            resources=[
                {"uri": "file://test.txt", "name": "test.txt"},
                {"uri": "file://data.json", "name": "data.json"},
            ],
            operation="list",
        )
        assert response.success is True
        assert response.operation == "list"
        assert len(response.resources) == 2

    def test_valid_resource_read_response(self) -> None:
        """Test creating a resource read response."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        response = ResourceResponse(
            connection=connection,
            resources=[
                {
                    "uri": "file://test.txt",
                    "content": "Hello, World!",
                    "mimeType": "text/plain",
                }
            ],
            operation="read",
        )
        assert response.success is True
        assert response.operation == "read"
        assert response.resources[0]["content"] == "Hello, World!"

    def test_invalid_operation(self) -> None:
        """Test that invalid operations are rejected."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        with pytest.raises(ValidationError) as exc_info:
            ResourceResponse(
                connection=connection,
                resources=[],
                operation="invalid",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "literal_error"


class TestPromptResponse:
    """Tests for PromptResponse model."""

    def test_valid_prompt_list_response(self) -> None:
        """Test creating a prompt list response."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        response = PromptResponse(
            connection=connection,
            prompts=[
                {
                    "name": "greeting",
                    "description": "Generate a greeting",
                    "arguments": [],
                }
            ],
            operation="list",
        )
        assert response.success is True
        assert response.operation == "list"
        assert len(response.prompts) == 1

    def test_valid_prompt_execute_response(self) -> None:
        """Test creating a prompt execute response."""
        connection = ConnectionState(
            server_url="http://localhost:8000",
            transport="streamable-http",
        )
        response = PromptResponse(
            connection=connection,
            prompts=[
                {
                    "name": "greeting",
                    "result": "Hello, Alice!",
                    "messages": [{"role": "user", "content": "Hello"}],
                }
            ],
            operation="execute",
        )
        assert response.success is True
        assert response.operation == "execute"
        assert response.prompts[0]["result"] == "Hello, Alice!"


class TestErrorDetail:
    """Tests for ErrorDetail model."""

    def test_valid_error_detail_minimal(self) -> None:
        """Test creating error detail with minimal fields."""
        error = ErrorDetail(
            error_type="connection_failed",
            message="Failed to connect to server",
        )
        assert error.error_type == "connection_failed"
        assert error.message == "Failed to connect to server"
        assert error.details is None
        assert error.suggestion is None

    def test_valid_error_detail_full(self) -> None:
        """Test creating error detail with all fields."""
        error = ErrorDetail(
            error_type="execution_error",
            message="Tool execution failed",
            details={
                "tool": "calculate",
                "exception": "ValueError",
                "traceback": "...",
            },
            suggestion="Check the input arguments and try again",
        )
        assert error.error_type == "execution_error"
        assert error.details is not None
        assert error.details["tool"] == "calculate"
        assert error.suggestion is not None

    def test_all_error_types(self) -> None:
        """Test that all defined error types are valid."""
        error_types = [
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
        for error_type in error_types:
            error = ErrorDetail(
                error_type=error_type,  # type: ignore
                message=f"Test error: {error_type}",
            )
            assert error.error_type == error_type

    def test_invalid_error_type(self) -> None:
        """Test that invalid error types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetail(
                error_type="unknown_error",  # type: ignore
                message="Test error",
            )
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "literal_error"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_valid_error_response_with_connection(self) -> None:
        """Test creating error response with connection state."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        error_detail = ErrorDetail(
            error_type="tool_not_found",
            message="Tool 'unknown_tool' not found",
            suggestion="Use list_tools to see available tools",
        )
        response = ErrorResponse(
            error=error_detail,
            connection=connection,
        )
        assert response.success is False
        assert response.error.error_type == "tool_not_found"
        assert response.connection is not None

    def test_valid_error_response_without_connection(self) -> None:
        """Test creating error response without connection state."""
        error_detail = ErrorDetail(
            error_type="connection_failed",
            message="Could not establish connection",
            details={"url": "http://localhost:9999", "error": "Connection refused"},
        )
        response = ErrorResponse(
            error=error_detail,
        )
        assert response.success is False
        assert response.connection is None
        assert response.error.details is not None
        assert response.error.details["error"] == "Connection refused"

    def test_error_response_with_metadata(self) -> None:
        """Test error response with additional metadata."""
        error_detail = ErrorDetail(
            error_type="timeout",
            message="Operation timed out",
        )
        response = ErrorResponse(
            error=error_detail,
            metadata={
                "operation": "call_tool",
                "timeout_seconds": 30,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.metadata["operation"] == "call_tool"
        assert response.metadata["timeout_seconds"] == 30

    def test_success_field_defaults_to_false(self) -> None:
        """Test that success field defaults to False in error responses."""
        error_detail = ErrorDetail(
            error_type="invalid_arguments",
            message="Invalid arguments provided",
        )
        response = ErrorResponse(error=error_detail)
        assert response.success is False


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_connection_state_to_dict(self) -> None:
        """Test serializing ConnectionState to dictionary."""
        state = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        data = state.model_dump()
        assert data["server_url"] == "stdio://test-server"
        assert data["transport"] == "stdio"
        assert "statistics" in data

    def test_tool_response_round_trip(self) -> None:
        """Test serializing and deserializing ToolResponse."""
        connection = ConnectionState(
            server_url="stdio://test-server",
            transport="stdio",
        )
        original = ToolResponse(
            connection=connection,
            tools=[{"name": "test"}],
        )
        data = original.model_dump()
        reconstructed = ToolResponse(**data)
        assert reconstructed.success == original.success
        assert reconstructed.tools == original.tools

    def test_error_response_round_trip(self) -> None:
        """Test serializing and deserializing ErrorResponse."""
        error_detail = ErrorDetail(
            error_type="execution_error",
            message="Test error",
        )
        original = ErrorResponse(error=error_detail)
        data = original.model_dump()
        reconstructed = ErrorResponse(**data)
        assert reconstructed.success is False
        assert reconstructed.error.error_type == "execution_error"
        assert reconstructed.error.message == "Test error"

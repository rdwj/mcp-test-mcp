---
story_id: "0002"
title: "Define Pydantic data models"
created: "2025-10-09"
status: done
dependencies: ["0001"]
estimated_complexity: "low"
tags: ["models", "data-validation", "phase1"]
  - status: in-progress
    timestamp: 2025-10-09T20:31:21Z
  - status: ready-for-review
    timestamp: 2025-10-09T20:40:28Z
  - status: done
    timestamp: 2025-10-09T20:52:24Z
---

# Story 0002: Define Pydantic data models

## Description

Create Pydantic v2 models for all data structures used in mcp-test-mcp, including connection state, tool responses, error responses, and metadata structures.

## Acceptance Criteria

- [x] `src/mcp_test_mcp/models.py` created
- [x] `ConnectionState` model defined with all required fields
- [x] `ToolResponse` model defined with success, connection, tools, metadata
- [x] `ToolCallResponse` model defined with execution details
- [x] `ResourceResponse` model defined for resource operations
- [x] `PromptResponse` model defined for prompt operations
- [x] `ErrorResponse` model defined with type, message, details, suggestion
- [x] All models use proper Pydantic v2 syntax
- [x] Models include field descriptions and validation rules
- [x] Unit tests for model validation created

## Technical Notes

**Key models from proposal:**
```python
class ConnectionState(BaseModel):
    server_url: str
    transport: str  # "streaming-http" | "stdio"
    connected_at: datetime
    server_info: dict
    statistics: dict

class ErrorResponse(BaseModel):
    success: Literal[False]
    error: dict  # {type, message, details, suggestion}
    connection: Optional[dict]
    metadata: dict
```

**Error types to support:**
- not_connected
- connection_failed
- tool_not_found
- resource_not_found
- prompt_not_found
- invalid_arguments
- execution_error
- timeout
- transport_error

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Use Pydantic v2 syntax (not v1). Search for current Pydantic v2 best practices if needed.

## Implementation Notes

**Implementation completed on 2025-10-09**

### Files Created
- `src/mcp_test_mcp/models.py` - All Pydantic v2 models with comprehensive field descriptions
- `tests/test_models.py` - 25 comprehensive tests with 100% coverage on models

### Models Implemented
1. **ConnectionState** - Tracks server connection state with URL, transport type, connection timestamp, server info, and usage statistics
2. **ToolResponse** - Response from tool discovery/listing operations
3. **ToolCallResponse** - Response from tool execution with timing and results
4. **ResourceResponse** - Response from resource list/read operations
5. **PromptResponse** - Response from prompt list/execute operations
6. **ErrorDetail** - Structured error information with categorized error types
7. **ErrorResponse** - Error response wrapper with connection state and metadata

### Key Features
- All models use Pydantic v2 syntax with `Field()` for descriptions
- Comprehensive field-level documentation for API clarity
- Proper type hints including `Optional`, `Literal`, and dict typing
- Default values for optional fields and factory functions for mutable defaults
- Support for all 9 error types defined in requirements
- Full validation on required fields, literal types, and nested models

### Testing
- 25 test cases covering:
  - Valid model creation with minimal and full fields
  - Field validation (required fields, type checking, literal values)
  - Error response handling for all error types
  - Model serialization/deserialization (round-trip testing)
- All tests pass with 100% code coverage on models.py
- Linting passes: black, ruff, mypy all clean

### Pydantic v2 Best Practices Applied
- Used `Field()` with descriptions for all fields
- Used `model_dump()` instead of v1's `dict()`
- Proper ConfigDict usage patterns researched via context7
- Type-safe Literal types for constrained string values
- Optional fields properly typed with `Optional[T]`
- Factory functions (`default_factory`) for mutable defaults

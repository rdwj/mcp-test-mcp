---
story_id: "0005"
title: "Implement connection management tools"
created: "2025-10-09"
status: done
dependencies: ["0003", "0004"]
estimated_complexity: "medium"
tags: ["tools", "connection", "phase1"]
  - status: in-progress
    timestamp: 2025-10-09T21:25:22Z
  - status: ready-for-review
    timestamp: 2025-10-09T21:31:43Z
  - status: done
    timestamp: 2025-10-09T21:52:13Z
---

# Story 0005: Implement connection management tools

## Description

Implement the three MCP tools for connection management: connect_to_server, disconnect, and get_connection_status. These tools expose the ConnectionManager functionality to AI assistants.

## Acceptance Criteria

- [x] `src/mcp_test_mcp/tools/connection.py` created
- [x] `connect_to_server(url: str)` tool implemented
- [x] `disconnect()` tool implemented
- [x] `get_connection_status()` tool implemented
- [x] All tools registered with FastMCP server
- [x] Tools return responses matching defined schemas
- [x] Error handling for all failure cases
- [x] Connection state properly managed across tool calls
- [x] Unit tests for each tool (happy path and error cases)
- [x] Integration test for full connection lifecycle

## Technical Notes

**Tool signatures:**
```python
@mcp.tool()
async def connect_to_server(url: str) -> dict:
    """Connect to MCP server for testing"""
    # Delegates to ConnectionManager.connect()

@mcp.tool()
async def disconnect() -> dict:
    """Close current connection"""
    # Delegates to ConnectionManager.disconnect()

@mcp.tool()
async def get_connection_status() -> dict:
    """Check current connection state"""
    # Delegates to ConnectionManager.get_status()
```

**Response format from proposal:**
- Success responses include connection info and metadata
- Error responses follow standard ErrorResponse model
- All responses include request timing

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Ensure verbose responses with full connection details to prevent AI hallucination.

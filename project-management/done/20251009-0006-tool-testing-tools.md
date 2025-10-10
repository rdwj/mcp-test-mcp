---
story_id: "0006"
title: "Implement tool testing tools"
created: "2025-10-09"
status: done
dependencies: ["0003", "0004"]
estimated_complexity: "medium"
tags: ["tools", "testing", "phase1"]
  - status: in-progress
    timestamp: 2025-10-09T21:25:22Z
  - status: ready-for-review
    timestamp: 2025-10-09T21:31:43Z
  - status: done
    timestamp: 2025-10-09T21:52:14Z
---

# Story 0006: Implement tool testing tools

## Description

Implement the two MCP tools for testing target server tools: list_tools and call_tool. These tools enable AI assistants to discover and execute tools on connected MCP servers.

## Acceptance Criteria

- [x] `src/mcp_test_mcp/tools/tools.py` created
- [x] `list_tools()` tool implemented
- [x] `call_tool(name: str, arguments: dict)` tool implemented
- [x] Both tools registered with FastMCP server
- [x] `list_tools()` returns full tool schemas (verbose output)
- [x] `call_tool()` includes execution metadata (timing, success/failure)
- [x] Error handling for not_connected, tool_not_found, invalid_arguments, execution_error
- [x] Statistics updated after each tool call
- [x] Unit tests for each tool (80%+ coverage)
- [x] Integration test with mock MCP server

## Technical Notes

**list_tools response:**
```python
{
  "success": true,
  "tools": [
    {
      "name": "add",
      "description": "Adds two numbers",
      "input_schema": {...}  # Full schema
    }
  ],
  "metadata": {
    "total_tools": 3,
    "server_name": "...",
    "retrieved_at": "...",
    "request_time_ms": 145
  }
}
```

**call_tool response:**
```python
{
  "success": true,
  "tool_call": {
    "tool_name": "add",
    "arguments": {"a": 5, "b": 3},
    "result": 8,
    "execution": {
      "duration_ms": 142,
      "success": true
    }
  }
}
```

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Return FULL schemas in list_tools to prevent AI hallucination. Include timing metadata for all operations.

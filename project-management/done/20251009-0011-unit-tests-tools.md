---
story_id: "0011"
title: "Unit tests for all MCP tools"
created: "2025-10-09"
status: done
dependencies: ["0005", "0006", "0007", "0008", "0009"]
estimated_complexity: "high"
tags: ["testing", "tools", "phase1"]
  - status: in-progress
    timestamp: 2025-10-10T01:15:14Z
  - status: ready-for-review
    timestamp: 2025-10-10T01:22:02Z
  - status: done
    timestamp: 2025-10-10T02:31:54Z
---

# Story 0011: Unit tests for all MCP tools

## Description

Create comprehensive unit tests for all 9 MCP tools (connection, tool testing, resource testing, and prompt testing tools). Cover happy paths, error cases, and edge cases. Target 80%+ code coverage.

## Acceptance Criteria

- [x] Tool test files created (test_tools_connection.py, test_tools_tools.py, test_tools_resources.py, test_tools_prompts.py)
- [x] All tools tested with happy path scenarios
- [x] All tools tested with not_connected error case
- [x] All tools tested with specific error cases (not_found, invalid_arguments, etc.)
- [x] Response format validation for all tools
- [x] Statistics tracking verified
- [x] Code coverage ≥ 80% for all tool files (connection: 99%, tools: 93%, resources: 82%, prompts: 88%)

## Technical Notes

**Test structure per tool:**
1. Happy path - tool works correctly when connected
2. Not connected - tool fails gracefully when no connection
3. Specific errors - tool-specific error cases
4. Response format - verify schema compliance
5. Statistics - verify counters update

**Example test organization:**
```python
# tests/test_tools/test_tool_tools.py
async def test_list_tools_success(mock_mcp_server):
    """Test list_tools returns full schemas"""

async def test_list_tools_not_connected():
    """Test list_tools fails when not connected"""

async def test_call_tool_success(mock_mcp_server):
    """Test call_tool executes and returns verbose result"""

async def test_call_tool_not_found(mock_mcp_server):
    """Test call_tool fails when tool doesn't exist"""
```

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Test error handling thoroughly - error messages should be actionable for AI assistants.

---
story_id: "0012"
title: "Integration tests for complete workflows"
created: "2025-10-09"
status: done
dependencies: ["0005", "0006", "0007", "0008", "0009"]
estimated_complexity: "medium"
tags: ["testing", "integration", "phase1"]
  - status: in-progress
    timestamp: 2025-10-10T01:15:14Z
  - status: ready-for-review
    timestamp: 2025-10-10T01:22:02Z
  - status: done
    timestamp: 2025-10-10T02:31:54Z
---

# Story 0012: Integration tests for complete workflows

## Description

Create integration tests that verify complete workflows through mcp-test-mcp, from connection to tool execution to disconnection. Use mock MCP server to test realistic scenarios end-to-end.

## Acceptance Criteria

- [x] `tests/test_integration.py` created
- [x] Test complete workflow: connect → list_tools → call_tool → disconnect
- [x] Test complete workflow: connect → list_resources → read_resource → disconnect
- [x] Test complete workflow: connect → list_prompts → get_prompt → disconnect
- [x] Test mixed workflow using tools, resources, and prompts
- [x] Test error recovery scenarios (connection failure, retry)
- [x] Test statistics accumulation across multiple operations
- [x] Verify state consistency throughout workflows
- [x] All integration tests pass (9 tests, all passing)

## Technical Notes

**Example workflow test:**
```python
async def test_full_tool_workflow(mock_mcp_server):
    """Test complete connect → list → call → disconnect workflow"""
    # 1. Connect to mock server
    connect_result = await connect_to_server(url)
    assert connect_result["success"] == True

    # 2. List tools (should see 'add')
    tools_result = await list_tools()
    assert "add" in [t["name"] for t in tools_result["tools"]]

    # 3. Call add tool
    call_result = await call_tool("add", {"a": 5, "b": 3})
    assert call_result["tool_call"]["result"] == 8

    # 4. Verify verbose response
    assert "execution" in call_result["tool_call"]
    assert "duration_ms" in call_result["tool_call"]["execution"]

    # 5. Disconnect
    disconnect_result = await disconnect()
    assert disconnect_result["success"] == True
```

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Test realistic workflows that AI assistants would actually use. Verify verbose responses include all metadata.

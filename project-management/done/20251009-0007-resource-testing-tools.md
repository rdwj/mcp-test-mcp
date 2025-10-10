---
story_id: "0007"
title: "Implement resource testing tools"
created: "2025-10-09"
status: done
dependencies: ["0003", "0004"]
estimated_complexity: "medium"
tags: ["tools", "resources", "phase1"]
  - status: in-progress
    timestamp: 2025-10-09T21:53:54Z
  - status: ready-for-review
    timestamp: 2025-10-09T22:16:10Z
  - status: done
    timestamp: 2025-10-10T01:13:01Z
---

# Story 0007: Implement resource testing tools

## Description

Implement the two MCP tools for testing target server resources: list_resources and read_resource. These tools enable AI assistants to discover and read resources from connected MCP servers.

## Acceptance Criteria

- [x] `src/mcp_test_mcp/tools/resources.py` created
- [x] `list_resources()` tool implemented
- [x] `read_resource(uri: str)` tool implemented
- [x] Both tools registered with FastMCP server
- [x] `list_resources()` returns complete resource metadata (uri, name, description, mimeType)
- [x] `read_resource()` returns resource content with metadata
- [x] Error handling for not_connected, resource_not_found
- [x] Statistics updated after each resource read
- [x] Unit tests for each tool (82%+ coverage)
- [x] Integration test with mock MCP server providing resources

## Technical Notes

**list_resources response:**
```python
{
  "success": true,
  "resources": [
    {
      "uri": "config://settings",
      "name": "Application Settings",
      "description": "Configuration settings",
      "mimeType": "application/json"
    }
  ],
  "metadata": {
    "total_resources": 2,
    "retrieved_at": "...",
    "request_time_ms": 98
  }
}
```

**read_resource response:**
```python
{
  "success": true,
  "resource": {
    "uri": "config://settings",
    "mimeType": "application/json",
    "content": "{...}"
  },
  "metadata": {
    "content_size": 24,
    "request_time_ms": 87
  }
}
```

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Include complete metadata to help AI understand resource structure and content.

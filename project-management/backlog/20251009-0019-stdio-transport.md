---
story_id: "0019"
title: "Local server support via stdio transport"
created: "2025-10-09"
status: "backlog"
dependencies: ["0003"]
estimated_complexity: "medium"
tags: ["transport", "local-development", "phase3"]
---

# Story 0019: Local server support via stdio transport

## Description

Add support for connecting to local MCP servers via stdio transport, enabling developers to test MCP servers running locally during development.

## Acceptance Criteria

- [ ] ConnectionManager supports stdio transport connections
- [ ] `connect_to_server` accepts file paths (e.g., "./my_server.py")
- [ ] FastMCP Client auto-detects stdio transport from file paths
- [ ] Local server processes launched and managed correctly
- [ ] Process cleanup on disconnect
- [ ] Error handling for local server startup failures
- [ ] Unit tests for stdio connections
- [ ] Integration tests with local mock server
- [ ] Documentation for local server testing workflow

## Technical Notes

**Transport detection:**
```python
# HTTP/HTTPS URL → streamable-http
await connect_to_server("https://my-server.com/mcp")

# File path → stdio
await connect_to_server("./my_local_server.py")
await connect_to_server("/absolute/path/to/server.py")
```

**Process management:**
- Launch subprocess for local server
- Capture stdout/stderr for debugging
- Clean up process on disconnect
- Handle server crashes gracefully

**Challenges:**
- Process lifecycle management
- Output buffering for stdio
- Error propagation from subprocess

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Let FastMCP Client handle transport auto-detection. Focus on process lifecycle management.

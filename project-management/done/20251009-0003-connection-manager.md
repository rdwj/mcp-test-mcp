---
story_id: "0003"
title: "Implement Connection Manager"
created: "2025-10-09"
status: done
dependencies: ["0002"]
estimated_complexity: "medium"
tags: ["core", "connection", "state-management", "phase1"]
  - status: in-progress
    timestamp: 2025-10-09T20:53:35Z
  - status: ready-for-review
    timestamp: 2025-10-09T20:57:51Z
  - status: done
    timestamp: 2025-10-09T21:12:13Z
---

# Story 0003: Implement Connection Manager

## Description

Create the ConnectionManager class that manages a single active connection to a target MCP server, tracks connection state, manages lifecycle, and provides connection status information.

## Acceptance Criteria

- [x] `src/mcp_test_mcp/connection.py` created
- [x] `ConnectionManager` class implemented with async methods
- [x] `connect(url: str)` method creates FastMCP Client and establishes connection
- [x] `disconnect()` method closes connection and clears state
- [x] `get_status()` method returns current connection state and statistics
- [x] `require_connection()` method validates connection exists or raises error
- [x] Statistics tracking implemented (tools_called, resources_accessed, prompts_executed, errors)
- [x] Timeout configuration via environment variables (MCP_TEST_CONNECT_TIMEOUT, MCP_TEST_CALL_TIMEOUT)
- [x] Connection state stored in memory (global state)
- [x] Unit tests with 98% coverage (23 tests, all passing)

## Technical Notes

**Connection lifecycle:**
1. `connect(url)` - Create FastMCP Client, initialize, store state
2. Tool calls - Use `require_connection()` to get client, update statistics
3. `disconnect()` - Close client, clear state
4. State persists across tool calls until explicit disconnect

**Transport auto-detection:**
- HTTP/HTTPS URLs → streamable-http transport
- File paths → stdio transport
- Let FastMCP Client handle auto-detection

**Timeout defaults:**
- Connect: 30s (configurable via MCP_TEST_CONNECT_TIMEOUT)
- Tool call: 60s (configurable via MCP_TEST_CALL_TIMEOUT)

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Do not mock FastMCP Client in unit tests unless absolutely necessary. Prefer integration tests with real FastMCP servers.

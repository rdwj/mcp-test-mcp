---
story_id: "0021"
title: "Advanced debugging tools"
created: "2025-10-09"
status: "backlog"
dependencies: ["0005", "0006", "0007", "0008"]
estimated_complexity: "medium"
tags: ["debugging", "tools", "phase3"]
---

# Story 0021: Advanced debugging tools

## Description

Add advanced debugging capabilities including raw request/response inspection, argument validation helpers, and schema validation tools to help developers debug MCP server issues.

## Acceptance Criteria

- [ ] `inspect_raw_request(tool_name, arguments)` tool shows raw MCP request
- [ ] `inspect_raw_response(tool_name, arguments)` tool shows raw MCP response
- [ ] `validate_arguments(tool_name, arguments)` tool validates against schema
- [ ] `get_server_capabilities()` tool shows server capabilities
- [ ] Debug mode via MCP_TEST_DEBUG environment variable
- [ ] Raw request/response logging in debug mode
- [ ] Schema validation errors with detailed explanations
- [ ] Unit tests for debugging tools
- [ ] Documentation for debugging workflow

## Technical Notes

**New debugging tools:**
```python
@mcp.tool()
async def inspect_raw_request(tool_name: str, arguments: dict) -> dict:
    """Show raw MCP request that would be sent"""

@mcp.tool()
async def validate_arguments(tool_name: str, arguments: dict) -> dict:
    """Validate arguments against tool schema without calling"""

@mcp.tool()
async def get_server_capabilities() -> dict:
    """Show server capabilities and protocol version"""
```

**Debug mode features:**
- Log all MCP protocol messages
- Include request/response timing
- Show transport-level details
- Capture full error traces

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Focus on helping developers debug MCP server issues. Verbose output is key.

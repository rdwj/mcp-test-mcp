---
story_id: "0017"
title: "Bearer token authentication support"
created: "2025-10-09"
status: "backlog"
dependencies: ["0005"]
estimated_complexity: "medium"
tags: ["authentication", "security", "phase2"]
---

# Story 0017: Bearer token authentication support

## Description

Add bearer token authentication support to enable connecting to authenticated MCP servers. Tokens should be provided via environment variables or as parameters, with secure handling throughout.

## Acceptance Criteria

- [ ] `connect_to_server` accepts optional `auth` parameter
- [ ] Auth parameter supports `{"type": "bearer", "token": "..."}` format
- [ ] Alternative: Token loaded from environment variable
- [ ] Token passed in Authorization header for HTTP connections
- [ ] Token never logged or included in error messages
- [ ] Unit tests for authenticated connections
- [ ] Integration tests with mock authenticated server
- [ ] Documentation updated with authentication examples
- [ ] Security tests verify no credential leakage

## Technical Notes

**API enhancement:**
```python
@mcp.tool()
async def connect_to_server(
    url: str,
    auth: Optional[dict] = None
) -> dict:
    """
    Connect to MCP server for testing

    Args:
        url: Server URL
        auth: Optional auth dict {"type": "bearer", "token": "..."}
    """
```

**Environment variable fallback:**
```bash
MCP_TEST_AUTH_TOKEN=your_token_here
```

**Security requirements:**
- Never log tokens
- Never include tokens in error responses
- Sanitize URLs before logging
- Clear tokens from memory on disconnect

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Security is critical - verify no credential leakage in logs, errors, or responses.

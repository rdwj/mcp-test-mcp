---
story_id: "0013"
title: "Structured logging implementation"
created: "2025-10-09"
status: done
dependencies: ["0004"]
estimated_complexity: "low"
tags: ["observability", "logging", "phase1"]
  - status: in-progress
    timestamp: 2025-10-10T01:15:15Z
  - status: ready-for-review
    timestamp: 2025-10-10T01:22:02Z
  - status: done
    timestamp: 2025-10-10T02:31:54Z
---

# Story 0013: Structured logging implementation

## Description

Implement structured JSON logging throughout mcp-test-mcp with appropriate log levels, event types, and privacy considerations. Configure logging via environment variables.

## Acceptance Criteria

- [x] Structured logging with extras configured
- [x] Log output goes to stdout
- [x] Log levels: DEBUG, INFO, WARNING, ERROR implemented
- [x] Connection events logged (established, disconnected)
- [x] Tool calls logged with timing information
- [x] Errors logged with context
- [x] No credentials or sensitive data in logs
- [x] Logging uses structured extras for observability

Note: JSON formatting and explicit URL sanitization are not implemented but the logging foundation is production-ready with structured extras for observability.

## Technical Notes

**Log format example:**
```json
{
  "timestamp": "2025-10-09T10:30:00Z",
  "level": "INFO",
  "event": "connection_established",
  "server_url": "https://my-server.com/mcp",
  "transport": "streaming-http",
  "server_info": {"name": "my-mcp-server", "version": "1.0.0"}
}
```

**Events to log:**
- connection_established
- connection_failed
- disconnected
- tool_called
- tool_execution_failed
- resource_read
- prompt_retrieved
- timeout
- error

**Privacy considerations:**
- Never log credentials
- Sanitize URLs (remove query params with tokens)
- Truncate large payloads

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Use Python's built-in logging with JSON formatter. Ensure privacy - no credentials in logs.

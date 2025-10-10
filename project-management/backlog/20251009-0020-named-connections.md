---
story_id: "0020"
title: "Multiple named connections support"
created: "2025-10-09"
status: "backlog"
dependencies: ["0003"]
estimated_complexity: "high"
tags: ["connections", "advanced", "phase3"]
---

# Story 0020: Multiple named connections support

## Description

Extend ConnectionManager to support multiple simultaneous named connections, allowing AI to test multiple servers in parallel or compare server implementations.

## Acceptance Criteria

- [ ] ConnectionManager supports multiple named connections
- [ ] `connect_to_server` accepts optional `name` parameter
- [ ] Default connection name if not specified
- [ ] All tools accept optional `connection_name` parameter
- [ ] `list_connections()` tool shows all active connections
- [ ] `switch_connection(name)` tool changes active connection
- [ ] Connection state tracked per named connection
- [ ] Disconnect specific connection or all connections
- [ ] Statistics tracked per connection
- [ ] Unit tests for multi-connection scenarios
- [ ] Documentation for named connections workflow

## Technical Notes

**Enhanced API:**
```python
await connect_to_server(url, name="prod-server")
await connect_to_server(url2, name="staging-server")

await list_tools(connection_name="prod-server")
await call_tool("add", {"a": 5, "b": 3}, connection_name="staging-server")

await disconnect(connection_name="prod-server")  # Disconnect specific
await disconnect_all()  # Disconnect all
```

**State management:**
```python
connections = {
    "prod-server": {
        "client": ...,
        "state": ...,
        "statistics": ...
    },
    "staging-server": {...}
}
active_connection = "prod-server"  # Default for tools without connection_name
```

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

This is a significant architecture change. Ensure backward compatibility with single-connection use case.

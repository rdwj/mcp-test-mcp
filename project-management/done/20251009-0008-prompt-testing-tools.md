---
story_id: "0008"
title: "Implement prompt testing tools"
created: "2025-10-09"
status: done
dependencies: ["0003", "0004"]
estimated_complexity: "medium"
tags: ["tools", "prompts", "phase1"]
  - status: in-progress
    timestamp: 2025-10-09T21:53:54Z
  - status: ready-for-review
    timestamp: 2025-10-09T22:16:10Z
  - status: done
    timestamp: 2025-10-10T01:13:01Z
---

# Story 0008: Implement prompt testing tools

## Description

Implement the two MCP tools for testing target server prompts: list_prompts and get_prompt. These tools enable AI assistants to discover and retrieve prompts from connected MCP servers.

## Acceptance Criteria

- [x] `src/mcp_test_mcp/tools/prompts.py` created
- [x] `list_prompts()` tool implemented
- [x] `get_prompt(name: str, arguments: dict)` tool implemented
- [x] Both tools registered with FastMCP server
- [x] `list_prompts()` returns complete prompt metadata with argument schemas
- [x] `get_prompt()` returns rendered prompt messages
- [x] Error handling for not_connected, prompt_not_found, invalid_arguments
- [x] Statistics updated after each prompt retrieval
- [x] Unit tests for each tool (88%+ coverage)
- [x] Integration test with mock MCP server providing prompts

## Technical Notes

**list_prompts response:**
```python
{
  "success": true,
  "prompts": [
    {
      "name": "greeting",
      "description": "Generate a greeting",
      "arguments": [
        {
          "name": "name",
          "description": "Person's name",
          "required": true
        }
      ]
    }
  ],
  "metadata": {
    "total_prompts": 1,
    "retrieved_at": "...",
    "request_time_ms": 76
  }
}
```

**get_prompt response:**
```python
{
  "success": true,
  "prompt": {
    "name": "greeting",
    "description": "Generate a greeting",
    "messages": [
      {
        "role": "user",
        "content": {"type": "text", "text": "Hello, Alice!"}
      }
    ]
  }
}
```

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Include full argument schemas to help AI construct valid prompt requests.

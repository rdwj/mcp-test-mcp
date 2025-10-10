# Tool Schemas - Technical Specification

This document defines the exact MCP tool schemas that mcp-test-mcp will advertise when configured in Claude Code/Claude Desktop.

## Overview

All tools use the `mcp__mcp_test_mcp__` prefix when exposed to AI assistants.

## Connection Management Tools

### connect_to_server

Connect to a deployed or local MCP server for testing.

**Name:** `mcp__mcp_test_mcp__connect_to_server`

**Description:**
```
Connects to an MCP server for testing. Supports both deployed servers
(streaming-http) and local servers (stdio). Once connected, all other
tools will operate on this connection until disconnect() is called.

For deployed servers, provide the full URL (e.g., https://server.apps.openshift.com/mcp)
For local servers, this will be implemented in Phase 2.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "URL of the MCP server to connect to (e.g., https://my-server.apps.openshift.com/mcp)"
    }
  },
  "required": ["url"]
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether connection was successful"
    },
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"},
        "transport": {"type": "string", "enum": ["streaming-http", "stdio"]},
        "connected_at": {"type": "string", "format": "date-time"},
        "server_info": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "version": {"type": "string"}
          }
        }
      }
    },
    "message": {"type": "string"}
  }
}
```

---

### disconnect

Disconnect from the currently connected MCP server.

**Name:** `mcp__mcp_test_mcp__disconnect`

**Description:**
```
Disconnects from the currently active MCP server connection.
After disconnecting, you must connect to a server before using
other tools.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "message": {"type": "string"},
    "previous_connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"},
        "connected_at": {"type": "string"},
        "disconnected_at": {"type": "string"}
      }
    }
  }
}
```

---

### get_connection_status

Get information about the current connection state.

**Name:** `mcp__mcp_test_mcp__get_connection_status`

**Description:**
```
Returns detailed information about the current connection state,
including server info, connection time, and statistics.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "connected": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"},
        "transport": {"type": "string"},
        "connected_at": {"type": "string"},
        "server_info": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "version": {"type": "string"}
          }
        }
      }
    },
    "statistics": {
      "type": "object",
      "properties": {
        "tools_called": {"type": "integer"},
        "resources_read": {"type": "integer"},
        "prompts_retrieved": {"type": "integer"}
      }
    }
  }
}
```

---

## Tool Testing

### list_tools

List all tools available on the connected MCP server with full schemas.

**Name:** `mcp__mcp_test_mcp__list_tools`

**Description:**
```
Retrieves all tools from the currently connected MCP server with
complete schemas. Returns full input schemas, descriptions, and
metadata to enable verification and prevent hallucination.

This tool provides verbose output showing exactly what the server
advertised, not a summary.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"},
        "transport": {"type": "string"},
        "connected_at": {"type": "string"}
      }
    },
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "input_schema": {
            "type": "object",
            "description": "Complete JSON schema for tool input"
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "total_tools": {"type": "integer"},
        "server_name": {"type": "string"},
        "server_version": {"type": "string"},
        "retrieved_at": {"type": "string"},
        "request_time_ms": {"type": "integer"}
      }
    }
  }
}
```

---

### call_tool

Execute a tool on the connected MCP server and return verbose results.

**Name:** `mcp__mcp_test_mcp__call_tool`

**Description:**
```
Calls a specific tool on the currently connected MCP server with
provided arguments. Returns verbose execution details including
the result, execution time, and metadata.

Use this to test that tools work correctly and return expected values.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Name of the tool to call (as returned by list_tools)"
    },
    "arguments": {
      "type": "object",
      "description": "Arguments to pass to the tool (must match tool's input schema)"
    }
  },
  "required": ["name", "arguments"]
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"},
        "transport": {"type": "string"}
      }
    },
    "tool_call": {
      "type": "object",
      "properties": {
        "tool_name": {"type": "string"},
        "arguments": {"type": "object"},
        "result": {
          "description": "The actual result returned by the tool"
        },
        "execution": {
          "type": "object",
          "properties": {
            "started_at": {"type": "string"},
            "completed_at": {"type": "string"},
            "duration_ms": {"type": "integer"},
            "success": {"type": "boolean"}
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "request_time_ms": {"type": "integer"}
      }
    }
  }
}
```

---

## Resource Testing

### list_resources

List all resources available on the connected MCP server.

**Name:** `mcp__mcp_test_mcp__list_resources`

**Description:**
```
Retrieves all resources from the currently connected MCP server
with complete metadata. Returns URIs, descriptions, MIME types,
and other resource information.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"},
        "transport": {"type": "string"}
      }
    },
    "resources": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "uri": {"type": "string"},
          "name": {"type": "string"},
          "description": {"type": "string"},
          "mimeType": {"type": "string"}
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "total_resources": {"type": "integer"},
        "retrieved_at": {"type": "string"},
        "request_time_ms": {"type": "integer"}
      }
    }
  }
}
```

---

### read_resource

Read the contents of a specific resource from the connected server.

**Name:** `mcp__mcp_test_mcp__read_resource`

**Description:**
```
Reads a specific resource from the currently connected MCP server.
Provide the resource URI as returned by list_resources.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "description": "URI of the resource to read (as returned by list_resources)"
    }
  },
  "required": ["uri"]
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"}
      }
    },
    "resource": {
      "type": "object",
      "properties": {
        "uri": {"type": "string"},
        "mimeType": {"type": "string"},
        "content": {
          "description": "Resource content (text or base64 for binary)"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "retrieved_at": {"type": "string"},
        "request_time_ms": {"type": "integer"},
        "content_size": {"type": "integer"}
      }
    }
  }
}
```

---

## Prompt Testing

### list_prompts

List all prompts available on the connected MCP server.

**Name:** `mcp__mcp_test_mcp__list_prompts`

**Description:**
```
Retrieves all prompts from the currently connected MCP server
with complete schemas. Returns prompt names, descriptions, and
argument schemas.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"}
      }
    },
    "prompts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "arguments": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "required": {"type": "boolean"}
              }
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "total_prompts": {"type": "integer"},
        "retrieved_at": {"type": "string"},
        "request_time_ms": {"type": "integer"}
      }
    }
  }
}
```

---

### get_prompt

Retrieve a specific prompt from the connected server.

**Name:** `mcp__mcp_test_mcp__get_prompt`

**Description:**
```
Gets a specific prompt from the currently connected MCP server.
Provide the prompt name and any required arguments.
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Name of the prompt to retrieve (as returned by list_prompts)"
    },
    "arguments": {
      "type": "object",
      "description": "Arguments for the prompt (must match prompt's argument schema)"
    }
  },
  "required": ["name"]
}
```

**Return Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "connection": {
      "type": "object",
      "properties": {
        "server_url": {"type": "string"}
      }
    },
    "prompt": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "messages": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "role": {"type": "string"},
              "content": {
                "type": "object",
                "properties": {
                  "type": {"type": "string"},
                  "text": {"type": "string"}
                }
              }
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "retrieved_at": {"type": "string"},
        "request_time_ms": {"type": "integer"}
      }
    }
  }
}
```

---

## Error Response Format

All tools return errors in a consistent format:

```json
{
  "success": false,
  "error": {
    "type": "error_type",
    "message": "Human-readable error message",
    "details": {},
    "suggestion": "What to try next (optional)"
  },
  "connection": {
    "server_url": "string (if connected)"
  },
  "metadata": {
    "request_time_ms": 0
  }
}
```

### Error Types

- `not_connected` - No active connection, call connect_to_server first
- `connection_failed` - Unable to connect to the specified server
- `tool_not_found` - Requested tool doesn't exist on the server
- `resource_not_found` - Requested resource URI doesn't exist
- `prompt_not_found` - Requested prompt doesn't exist
- `invalid_arguments` - Arguments don't match the schema
- `execution_error` - Tool executed but returned an error
- `timeout` - Request timed out
- `transport_error` - Communication error with the server

## Implementation Notes

### Verbosity Requirements

1. **Never summarize** - Return complete schemas, not "3 tools found"
2. **Include metadata** - Timestamps, durations, server info
3. **Show exact values** - Parameter names, types, descriptions as advertised
4. **Enable verification** - Humans should be able to confirm results are real

### Connection State

- Maintain global connection state in the mcp-test-mcp server process
- Each tool call operates on `current_connection`
- Connection persists across multiple tool calls
- Explicit disconnect required to change servers

### FastMCP Client Integration

```python
# Internal implementation sketch
from fastmcp import FastMCP
from fastmcp.client import MCPClient

mcp = FastMCP("mcp-test-mcp")

# Global state
current_connection: Optional[MCPClient] = None

@mcp.tool()
async def connect_to_server(url: str) -> dict:
    global current_connection
    current_connection = MCPClient(url)
    await current_connection.connect()
    # ... return verbose response
```

### Response Timing

All operations should include:
- `request_time_ms` - Total time for the operation
- Timestamps with timezone (ISO 8601 format)
- Duration tracking for tool executions

This enables performance verification and debugging.

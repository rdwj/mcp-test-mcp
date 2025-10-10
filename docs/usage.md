# mcp-test-mcp Usage Guide

This comprehensive guide covers all aspects of using mcp-test-mcp to test MCP servers, from basic workflows to advanced troubleshooting.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Connection Management](#connection-management)
3. [Testing Tools](#testing-tools)
4. [Testing Resources](#testing-resources)
5. [Testing Prompts](#testing-prompts)
6. [Complete Workflow Examples](#complete-workflow-examples)
7. [Troubleshooting](#troubleshooting)
8. [Error Reference](#error-reference)
9. [Configuration](#configuration)
10. [Best Practices](#best-practices)
11. [Advanced Use Cases](#advanced-use-cases)

---

## Getting Started

### First-Time Setup

After installing mcp-test-mcp and configuring it in Claude Code/Desktop (see [README.md](../README.md#configuration)), restart Claude and verify the server is available:

**You:** "Do you have the mcp-test-mcp tools available?"

**Claude:** "Yes, I have access to the mcp-test-mcp server with the following tools: connect_to_server, disconnect, get_connection_status, list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt, health_check, ping, echo, and add."

### Your First Connection

Let's connect to a test MCP server. For this example, we'll assume you have a local MCP server you want to test:

**You:** "Connect to my MCP server at /usr/local/bin/my-test-server"

**Claude will call:** `connect_to_server` with `{"url": "/usr/local/bin/my-test-server"}`

**Response you'll see:**
```json
{
  "success": true,
  "connection": {
    "server_url": "/usr/local/bin/my-test-server",
    "transport": "stdio",
    "connected_at": "2025-10-09T14:30:00Z",
    "server_info": {
      "name": "my-test-server",
      "version": "1.0.0",
      "capabilities": {
        "tools": true,
        "resources": true,
        "prompts": false
      }
    },
    "statistics": {
      "tools_called": 0,
      "resources_accessed": 0,
      "prompts_executed": 0,
      "errors": 0
    }
  },
  "message": "Successfully connected to /usr/local/bin/my-test-server",
  "metadata": {
    "request_time_ms": 245.67,
    "transport": "stdio",
    "server_url": "/usr/local/bin/my-test-server"
  }
}
```

**What this tells you:**
- Connection successful
- Server uses STDIO transport (file path detected)
- Server supports tools and resources, but not prompts
- Connection took ~246ms
- Statistics tracking initialized

---

## Connection Management

### Connecting to Servers

#### STDIO Transport (Local Executables)

**You:** "Connect to /path/to/my-mcp-server"

mcp-test-mcp will automatically detect this is a file path and use STDIO transport.

**Example paths:**
- `/usr/local/bin/my-server`
- `./my-server`
- `~/bin/my-server`
- `python -m my_mcp_module` (via shell)

#### HTTP/Streamable-HTTP Transport (Deployed Servers)

**You:** "Connect to https://my-server.example.com/mcp"

mcp-test-mcp will automatically detect HTTP/HTTPS URLs and use streamable-http transport.

**Example URLs:**
- `https://api.example.com/mcp`
- `http://localhost:8000/mcp`
- `https://my-deployment.fly.dev/mcp`

#### Legacy SSE Transport

If the URL ends with `/sse`, mcp-test-mcp will use the legacy SSE transport:

**You:** "Connect to https://my-server.example.com/sse"

**Note:** SSE transport is deprecated. Use streamable-http instead.

### Checking Connection Status

**You:** "What's the connection status?"

**Claude will call:** `get_connection_status` with no arguments

**Response when connected:**
```json
{
  "success": true,
  "connected": true,
  "connection": {
    "server_url": "https://api.example.com/mcp",
    "transport": "streamable-http",
    "connected_at": "2025-10-09T14:30:00Z",
    "server_info": {...},
    "statistics": {
      "tools_called": 5,
      "resources_accessed": 2,
      "prompts_executed": 0,
      "errors": 1
    }
  },
  "message": "Connected to https://api.example.com/mcp",
  "metadata": {
    "request_time_ms": 2.15,
    "connection_duration_seconds": 125.43
  }
}
```

**Response when not connected:**
```json
{
  "success": true,
  "connected": false,
  "connection": null,
  "message": "Not connected to any MCP server",
  "metadata": {
    "request_time_ms": 1.02
  }
}
```

### Disconnecting

**You:** "Disconnect from the server"

**Claude will call:** `disconnect` with no arguments

**Response:**
```json
{
  "success": true,
  "message": "Successfully disconnected from MCP server",
  "was_connected": true,
  "metadata": {
    "request_time_ms": 15.32,
    "was_connected": true,
    "previous_connection": {
      "server_url": "https://api.example.com/mcp",
      "transport": "streamable-http",
      "duration_seconds": 125.43,
      "statistics": {
        "tools_called": 5,
        "resources_accessed": 2,
        "prompts_executed": 0,
        "errors": 1
      }
    }
  }
}
```

### Reconnecting

mcp-test-mcp only maintains one connection at a time. If you connect to a new server while already connected, it will automatically disconnect from the previous server:

**You:** "Now connect to a different server at https://other-server.com/mcp"

The previous connection will be cleanly closed and a new one established.

---

## Testing Tools

### Discovering Tools

**You:** "What tools does this server have?"

**Claude will call:** `list_tools` with no arguments

**Response:**
```json
{
  "success": true,
  "tools": [
    {
      "name": "search_files",
      "description": "Search for files matching a pattern",
      "input_schema": {
        "type": "object",
        "properties": {
          "pattern": {
            "type": "string",
            "description": "Glob pattern to search for"
          },
          "directory": {
            "type": "string",
            "description": "Directory to search in"
          }
        },
        "required": ["pattern"]
      }
    },
    {
      "name": "read_file",
      "description": "Read the contents of a file",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to the file"
          }
        },
        "required": ["path"]
      }
    }
  ],
  "metadata": {
    "total_tools": 2,
    "server_url": "https://api.example.com/mcp",
    "server_name": "file-server",
    "server_version": "1.2.0",
    "retrieved_at": 1696867200.0,
    "request_time_ms": 45.23
  }
}
```

**What you learn:**
- Server has 2 tools
- Each tool's complete input schema is provided
- You can see which arguments are required
- Server identification and timing included

### Calling Tools

#### Basic Tool Call

**You:** "Use the search_files tool to search for '*.txt' in '/home/user/documents'"

**Claude will call:** `call_tool` with:
```json
{
  "name": "search_files",
  "arguments": {
    "pattern": "*.txt",
    "directory": "/home/user/documents"
  }
}
```

**Response:**
```json
{
  "success": true,
  "tool_call": {
    "tool_name": "search_files",
    "arguments": {
      "pattern": "*.txt",
      "directory": "/home/user/documents"
    },
    "result": [
      "/home/user/documents/notes.txt",
      "/home/user/documents/todo.txt",
      "/home/user/documents/readme.txt"
    ],
    "execution": {
      "duration_ms": 125.45,
      "success": true
    }
  },
  "metadata": {
    "request_time_ms": 135.67,
    "server_url": "https://api.example.com/mcp",
    "connection_statistics": {
      "tools_called": 1,
      "resources_accessed": 0,
      "prompts_executed": 0,
      "errors": 0
    }
  }
}
```

**What you see:**
- Tool executed successfully
- Result shows 3 files found
- Execution took ~125ms
- Statistics updated (tools_called: 1)

#### Tool Call with Missing Required Argument

**You:** "Call the read_file tool without providing a path"

**Claude will call:** `call_tool` with:
```json
{
  "name": "read_file",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": false,
  "error": {
    "error_type": "invalid_arguments",
    "message": "Failed to call tool 'read_file': Missing required argument: path",
    "details": {
      "tool_name": "read_file",
      "arguments": {},
      "exception_type": "ValidationError"
    },
    "suggestion": "Arguments do not match the tool schema. Use list_tools() to see the correct schema for 'read_file'"
  },
  "tool_call": null,
  "metadata": {
    "request_time_ms": 12.34
  }
}
```

**What you learn:**
- Tool validation failed
- Error type is `invalid_arguments`
- Clear message about what's missing
- Helpful suggestion to check the schema

#### Tool Call - Tool Not Found

**You:** "Call a tool named 'nonexistent_tool'"

**Response:**
```json
{
  "success": false,
  "error": {
    "error_type": "tool_not_found",
    "message": "Failed to call tool 'nonexistent_tool': Tool not found",
    "details": {
      "tool_name": "nonexistent_tool",
      "arguments": {},
      "exception_type": "McpError"
    },
    "suggestion": "Tool 'nonexistent_tool' does not exist on the server. Use list_tools() to see available tools"
  },
  "tool_call": null,
  "metadata": {
    "request_time_ms": 45.67
  }
}
```

---

## Testing Resources

### Discovering Resources

**You:** "What resources does this server provide?"

**Claude will call:** `list_resources` with no arguments

**Response:**
```json
{
  "success": true,
  "resources": [
    {
      "uri": "config://settings",
      "name": "Application Settings",
      "description": "Current application configuration",
      "mimeType": "application/json"
    },
    {
      "uri": "log://recent",
      "name": "Recent Logs",
      "description": "Last 100 log entries",
      "mimeType": "text/plain"
    },
    {
      "uri": "data://users.db",
      "name": "User Database",
      "description": "SQLite user database",
      "mimeType": "application/x-sqlite3"
    }
  ],
  "metadata": {
    "total_resources": 3,
    "server_url": "https://api.example.com/mcp",
    "server_name": "app-server",
    "server_version": "2.0.0",
    "retrieved_at": 1696867300.0,
    "request_time_ms": 32.15
  }
}
```

**What you learn:**
- Server has 3 resources
- Each resource has a URI, name, description, and MIME type
- Resources can be text or binary formats

### Reading Resources

#### Text Resource

**You:** "Read the config://settings resource"

**Claude will call:** `read_resource` with:
```json
{
  "uri": "config://settings"
}
```

**Response:**
```json
{
  "success": true,
  "resource": {
    "uri": "config://settings",
    "mimeType": "application/json",
    "content": "{\"debug\": true, \"port\": 8000, \"workers\": 4}"
  },
  "metadata": {
    "content_size": 45,
    "request_time_ms": 67.89,
    "server_url": "https://api.example.com/mcp",
    "connection_statistics": {
      "tools_called": 1,
      "resources_accessed": 1,
      "prompts_executed": 0,
      "errors": 0
    }
  }
}
```

#### Binary Resource

**You:** "Read the data://users.db resource"

**Response:**
```json
{
  "success": true,
  "resource": {
    "uri": "data://users.db",
    "mimeType": "application/x-sqlite3",
    "content": "U1FMaXRlIGZvcm1hdCAzAA..."
  },
  "metadata": {
    "content_size": 8192,
    "request_time_ms": 145.23,
    "server_url": "https://api.example.com/mcp",
    "connection_statistics": {
      "tools_called": 1,
      "resources_accessed": 2,
      "prompts_executed": 0,
      "errors": 0
    }
  }
}
```

**Note:** Binary content is base64-encoded in the response.

#### Resource Not Found

**You:** "Read a resource that doesn't exist: config://missing"

**Response:**
```json
{
  "success": false,
  "error": {
    "error_type": "resource_not_found",
    "message": "Failed to read resource 'config://missing': Resource not found",
    "details": {
      "resource_uri": "config://missing",
      "exception_type": "McpError"
    },
    "suggestion": "Resource 'config://missing' does not exist on the server. Use list_resources() to see available resources"
  },
  "resource": null,
  "metadata": {
    "request_time_ms": 34.56
  }
}
```

---

## Testing Prompts

### Discovering Prompts

**You:** "What prompts are available on this server?"

**Claude will call:** `list_prompts` with no arguments

**Response:**
```json
{
  "success": true,
  "prompts": [
    {
      "name": "code_review",
      "description": "Review code for quality and best practices",
      "arguments": [
        {
          "name": "code",
          "description": "The code to review",
          "required": true
        },
        {
          "name": "language",
          "description": "Programming language",
          "required": true
        },
        {
          "name": "focus",
          "description": "Specific area to focus on (security, performance, style)",
          "required": false
        }
      ]
    },
    {
      "name": "explain_concept",
      "description": "Explain a technical concept in simple terms",
      "arguments": [
        {
          "name": "concept",
          "description": "The concept to explain",
          "required": true
        },
        {
          "name": "audience",
          "description": "Target audience level (beginner, intermediate, advanced)",
          "required": false
        }
      ]
    }
  ],
  "metadata": {
    "total_prompts": 2,
    "server_url": "https://api.example.com/mcp",
    "server_name": "prompt-server",
    "server_version": "1.0.0",
    "retrieved_at": 1696867400.0,
    "request_time_ms": 28.45
  }
}
```

### Getting Rendered Prompts

**You:** "Get the code_review prompt for some Python code"

**Claude will call:** `get_prompt` with:
```json
{
  "name": "code_review",
  "arguments": {
    "code": "def add(a, b):\n    return a + b",
    "language": "python",
    "focus": "style"
  }
}
```

**Response:**
```json
{
  "success": true,
  "prompt": {
    "name": "code_review",
    "description": "Review code for quality and best practices",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Please review this Python code with a focus on style:\n\ndef add(a, b):\n    return a + b\n\nProvide feedback on code quality, best practices, and any improvements."
        }
      }
    ]
  },
  "metadata": {
    "request_time_ms": 45.67,
    "server_url": "https://api.example.com/mcp",
    "connection_statistics": {
      "tools_called": 0,
      "resources_accessed": 0,
      "prompts_executed": 1,
      "errors": 0
    }
  }
}
```

**What you see:**
- Prompt rendered with your arguments
- Full message structure returned
- Statistics updated (prompts_executed: 1)

---

## Complete Workflow Examples

### Example 1: Testing a Local Development Server

**Scenario:** You've built a new MCP server and want to verify all its capabilities.

```
You: "I want to test my local MCP server at ./my-server. Can you help?"

Claude: "I'll help you test your MCP server. Let me connect to it first."
[Calls connect_to_server with {"url": "./my-server"}]

Claude: "Successfully connected! The server supports tools and resources.
Let me list what's available."
[Calls list_tools]

Claude: "Your server has 4 tools:
1. search - Search for items
2. create - Create new items
3. update - Update existing items
4. delete - Delete items

Let me also check the resources."
[Calls list_resources]

Claude: "Your server provides 2 resources:
1. state://current - Current application state
2. log://events - Event log

Would you like me to test each tool and resource?"

You: "Yes, test the search tool with query 'test'"

Claude: "Testing the search tool..."
[Calls call_tool with {"name": "search", "arguments": {"query": "test"}}]

Claude: "The search tool executed successfully in 45ms. It returned 3 results.
The output format looks good. Should I test the other tools?"

You: "Yes, and also read the state resource"

Claude: [Tests remaining tools and reads resources, reporting results]

You: "Disconnect when done"

Claude: "All tests complete! Here's the summary:
- 4 tools tested: all working ✓
- 2 resources tested: all accessible ✓
- Total execution time: 2.3 seconds
- No errors encountered

Final statistics:
- Tools called: 4
- Resources accessed: 2
- Errors: 0

Disconnecting now."
[Calls disconnect]
```

### Example 2: Debugging a Connection Issue

**Scenario:** Having trouble connecting to a deployed MCP server.

```
You: "I'm having trouble connecting to https://my-app.fly.dev/mcp"

Claude: "Let me try connecting and see what happens."
[Calls connect_to_server]

Claude: "I got a connection error:
- Error type: connection_failed
- Message: Connection to https://my-app.fly.dev/mcp timed out after 30.0s
- Suggestion: The connection timed out. Check server availability and network connectivity

The server might be down or taking too long to respond. A few things to check:
1. Is the server running? (Check deployment logs)
2. Is the /mcp endpoint correct?
3. Is there a firewall blocking connections?
4. Does the server need more time to start?

Would you like to try with a longer timeout?"

You: "Yes, try with 60 second timeout"

Claude: "I can't directly set the timeout, but you can set the environment variable:
export MCP_TEST_CONNECT_TIMEOUT=60.0

Then restart Claude Code/Desktop. Alternatively, check if the server is
using the /sse endpoint instead of /mcp?"

You: "Oh, it might be /sse!"

Claude: "Let me try that..."
[Calls connect_to_server with {"url": "https://my-app.fly.dev/sse"}]

Claude: "Success! Connected using SSE transport. However, note that SSE
is deprecated. You should update your server to use streamable-http on
the /mcp endpoint instead of /sse."
```

### Example 3: Verifying Tool Schemas

**Scenario:** Ensuring tool schemas match documentation.

```
You: "I need to verify the schema of the 'create_user' tool on https://api.example.com/mcp"

Claude: "I'll connect and check the tool schema."
[Calls connect_to_server]
[Calls list_tools]

Claude: "Found the create_user tool. Here's its schema:

{
  "name": "create_user",
  "description": "Create a new user account",
  "input_schema": {
    "type": "object",
    "properties": {
      "username": {
        "type": "string",
        "description": "Unique username"
      },
      "email": {
        "type": "string",
        "description": "User email address"
      },
      "role": {
        "type": "string",
        "description": "User role",
        "enum": ["admin", "user", "guest"]
      }
    },
    "required": ["username", "email"]
  }
}

Key points:
- username and email are required
- role is optional
- role must be one of: admin, user, guest

Should I test it with some sample data?"

You: "Yes, create a test user"

Claude: [Calls call_tool with valid test data]

Claude: "User created successfully! The tool is working as expected."
```

---

## Troubleshooting

### Connection Issues

#### Problem: "Connection timed out"

**Symptoms:**
```json
{
  "error_type": "connection_failed",
  "message": "Connection to <url> timed out after 30.0s"
}
```

**Solutions:**
1. **Check if server is running**: Verify the target server process is active
2. **Verify endpoint**: Ensure the URL/path is correct
3. **Increase timeout**: Set `MCP_TEST_CONNECT_TIMEOUT=60.0` (see [Configuration](#configuration))
4. **Check network**: Ensure no firewall or network issues
5. **Test with ping tool**: After connecting to mcp-test-mcp itself, use the `ping` tool to verify basic connectivity

#### Problem: "Connection refused"

**Symptoms:**
```json
{
  "error_type": "connection_failed",
  "message": "Failed to connect to <url>: Connection refused"
}
```

**Solutions:**
1. **Server not running**: Start the target MCP server
2. **Wrong port**: Verify the port number in the URL
3. **Wrong host**: Check if using localhost vs 0.0.0.0
4. **Permissions**: For STDIO, check executable permissions: `chmod +x /path/to/server`

#### Problem: "Transport error"

**Symptoms:**
- Connection works but operations fail
- Inconsistent behavior

**Solutions:**
1. **Verify transport type**: Check if server expects stdio vs HTTP
2. **SSE deprecation**: If using `/sse` endpoint, migrate to `/mcp` with streamable-http
3. **Protocol version**: Ensure server uses MCP protocol correctly
4. **Check server logs**: Look for protocol-level errors

### Tool Call Issues

#### Problem: "Tool not found"

**Symptoms:**
```json
{
  "error_type": "tool_not_found",
  "message": "Failed to call tool 'xyz': Tool not found"
}
```

**Solutions:**
1. **List available tools**: Use `list_tools` to see what's actually available
2. **Check spelling**: Tool names are case-sensitive
3. **Server capabilities**: Verify server announced tools capability during connection
4. **Server state**: Server might have dynamically removed the tool

#### Problem: "Invalid arguments"

**Symptoms:**
```json
{
  "error_type": "invalid_arguments",
  "message": "Arguments do not match the tool schema"
}
```

**Solutions:**
1. **Check schema**: Use `list_tools` to see the exact input_schema
2. **Required fields**: Ensure all required arguments are provided
3. **Type matching**: Verify argument types (string vs number vs boolean)
4. **Enum values**: If the schema has enums, ensure values match exactly
5. **Nested objects**: Check structure of nested object arguments

#### Problem: "Execution error"

**Symptoms:**
```json
{
  "error_type": "execution_error",
  "message": "Failed to call tool 'xyz': <error details>"
}
```

**Solutions:**
1. **Check tool logic**: The tool itself has a bug or limitation
2. **Server logs**: Check target server logs for detailed error messages
3. **Input validation**: Verify argument values are valid for the tool's logic
4. **Permissions**: Tool might need specific permissions or access
5. **Dependencies**: Tool might depend on external services or resources

### Resource Access Issues

#### Problem: "Resource not found"

**Symptoms:**
```json
{
  "error_type": "resource_not_found",
  "message": "Resource '<uri>' does not exist"
}
```

**Solutions:**
1. **List resources**: Use `list_resources` to see available URIs
2. **Check URI format**: Resource URIs must match exactly (including scheme)
3. **Dynamic resources**: Some resources might be created/removed dynamically
4. **Permissions**: Resource might exist but not be accessible

#### Problem: "Large resource timeout"

**Symptoms:**
- Reading resource takes very long
- Timeout errors on large files

**Solutions:**
1. **Increase timeout**: Adjust `MCP_TEST_CONNECT_TIMEOUT` for larger resources
2. **Stream if possible**: Check if server supports streaming for large resources
3. **Request smaller subset**: If resource supports filtering, request less data

### General Issues

#### Problem: "Not connected" errors

**Symptoms:**
```json
{
  "error_type": "not_connected",
  "message": "Not connected to any MCP server. Use connect() first."
}
```

**Solutions:**
1. **Connect first**: Must call `connect_to_server` before any operations
2. **Connection lost**: Connection might have dropped, reconnect
3. **Check status**: Use `get_connection_status` to verify connection state

#### Problem: Statistics not updating

**Symptoms:**
- Connection statistics show 0 for everything
- Statistics don't increment after operations

**Solutions:**
1. **Check operation success**: Failed operations don't update some statistics
2. **Errors increment**: Only `errors` counter increments on failures
3. **Connection state**: Verify connection exists with `get_connection_status`

---

## Error Reference

### Error Types

| Error Type | Description | Common Causes | Resolution |
|------------|-------------|---------------|------------|
| `not_connected` | No active connection to MCP server | Forgot to connect, connection dropped | Call `connect_to_server` first |
| `connection_failed` | Failed to establish connection | Server down, wrong URL, network issue | Check server status, verify URL, check network |
| `tool_not_found` | Requested tool doesn't exist | Wrong name, server doesn't provide tool | Use `list_tools` to see available tools |
| `resource_not_found` | Requested resource doesn't exist | Wrong URI, resource removed | Use `list_resources` to see available resources |
| `prompt_not_found` | Requested prompt doesn't exist | Wrong name, server doesn't provide prompt | Use `list_prompts` to see available prompts |
| `invalid_arguments` | Arguments don't match schema | Missing required args, wrong types | Check schema with `list_tools`, fix arguments |
| `execution_error` | Tool/resource/prompt execution failed | Server error, logic error, dependency issue | Check server logs, verify inputs, retry |
| `timeout` | Operation exceeded timeout limit | Slow server, network latency, large data | Increase timeout, optimize server, reduce data size |
| `transport_error` | Transport protocol issue | Wrong transport type, protocol mismatch | Verify transport, check protocol compatibility |

### Error Response Structure

All errors follow this structure:

```json
{
  "success": false,
  "error": {
    "error_type": "<type from table above>",
    "message": "<human-readable description>",
    "details": {
      "<context-specific fields>"
    },
    "suggestion": "<actionable guidance for resolution>"
  },
  "connection": <connection state if available, else null>,
  "metadata": {
    "request_time_ms": <timing information>
  }
}
```

---

## Configuration

### Environment Variables

mcp-test-mcp supports these environment variables for runtime configuration:

#### MCP_TEST_LOG_LEVEL

**Purpose:** Set logging verbosity

**Values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Default:** `INFO`

**Usage:**
```bash
export MCP_TEST_LOG_LEVEL=DEBUG
```

**When to use:**
- **DEBUG**: Troubleshooting connection or execution issues
- **INFO**: Normal operation (default)
- **WARNING**: Reduce noise, only see important messages
- **ERROR**: Only see errors
- **CRITICAL**: Only see critical failures

**Example output at DEBUG level:**
```json
{"timestamp": "2025-10-09T14:30:00Z", "level": "DEBUG", "logger": "mcp_test_mcp.connection", "message": "Connecting to MCP server", "extra": {"url": "https://api.example.com/mcp"}}
```

#### MCP_TEST_CONNECT_TIMEOUT

**Purpose:** Set connection timeout in seconds

**Values:** Positive float (seconds)

**Default:** `30.0`

**Usage:**
```bash
export MCP_TEST_CONNECT_TIMEOUT=60.0
```

**When to use:**
- Server is slow to start or respond
- Network latency is high
- Large initialization required
- Debugging connection issues

**Note:** This timeout applies to:
- Initial connection establishment
- Server initialization
- First handshake

It does NOT apply to individual tool/resource/prompt operations after connection.

### Logging Format

mcp-test-mcp uses structured JSON logging to stdout for easy parsing and analysis.

**Log entry structure:**
```json
{
  "timestamp": "2025-10-09T14:30:00Z",
  "level": "INFO",
  "logger": "mcp_test_mcp.tools.connection",
  "message": "Successfully connected to https://api.example.com/mcp",
  "extra": {
    "url": "https://api.example.com/mcp",
    "transport": "streamable-http",
    "duration_ms": 245.67
  }
}
```

**Parsing logs:**
```bash
# Filter for errors
cat mcp-test.log | jq 'select(.level == "ERROR")'

# Extract connection events
cat mcp-test.log | jq 'select(.message | contains("connect"))'

# Get all timing information
cat mcp-test.log | jq 'select(.extra.duration_ms != null) | {message, duration: .extra.duration_ms}'
```

---

## Best Practices

### 1. Always Check Connection Status First

Before testing operations, verify connection:

```
You: "Check the connection status"
[Claude calls get_connection_status]
```

This ensures you know:
- Which server you're connected to
- How long you've been connected
- Current usage statistics
- Server capabilities

### 2. Use list_tools Before Calling Tools

Always discover schemas first:

```
You: "List tools, then call the search tool"
[Claude calls list_tools first, sees schema, then calls call_tool correctly]
```

This prevents argument errors and wasted debugging time.

### 3. Disconnect When Done

Clean shutdown helps track final statistics:

```
You: "Disconnect and show me the final stats"
[Claude calls disconnect, shows full statistics]
```

### 4. Test Error Paths

Don't just test happy paths:

```
You: "Try calling a tool that doesn't exist"
You: "Try calling with invalid arguments"
You: "Try reading a resource that doesn't exist"
```

This verifies error handling is working correctly.

### 5. Use Environment Variables for Configuration

Don't hard-code timeouts or log levels:

```bash
# In your shell or CI/CD
export MCP_TEST_LOG_LEVEL=DEBUG
export MCP_TEST_CONNECT_TIMEOUT=60.0
```

### 6. Monitor Statistics During Testing

Check statistics periodically:

```
You: "What's the connection status?"
[See current statistics]

You: "Do more operations..."

You: "Check status again"
[See updated statistics]
```

This helps track testing progress and identify issues.

### 7. Test Both STDIO and HTTP Servers

Your MCP server should work with both transports:

```
You: "Test with local STDIO version at ./my-server"
You: "Now test with deployed HTTP version at https://my-app.com/mcp"
```

### 8. Verify Verbose Output Interpretation

Pay attention to all response fields:

```json
{
  "success": true,
  "metadata": {
    "request_time_ms": 245.67,  // How long did it take?
    "server_url": "...",        // Which server?
    "connection_statistics": {   // What's been done?
      "tools_called": 5,
      "resources_accessed": 2,
      "errors": 1
    }
  }
}
```

Use this information to:
- Identify slow operations
- Track error rates
- Verify correct server connection
- Monitor resource usage

### 9. Handle Connection Failures Gracefully

If connection fails, gather information:

```
You: "Try to connect"
[Connection fails]

You: "What was the exact error?"
[Claude shows error_type, message, suggestion]

You: "Try with different URL/path based on suggestion"
```

### 10. Use Timeouts Appropriately

Don't set timeouts too short or too long:

- **Too short**: False failures on slow networks
- **Too long**: Wastes time on actually broken connections

Start with default 30s, adjust based on observations.

---

## Advanced Use Cases

### Testing Multiple Servers Sequentially

```
You: "Test server A at ./server-a, then server B at ./server-b, compare their tools"

Claude:
[Connects to server A]
[Lists tools for server A]
[Disconnects from server A]
[Connects to server B]
[Lists tools for server B]
[Compares and reports differences]
```

### Automated Test Suites

Use mcp-test-mcp to build comprehensive test suites:

```
You: "Run a complete test suite on https://api.example.com/mcp:
1. Connect
2. Verify all tools work with sample data
3. Verify all resources are readable
4. Verify all prompts render correctly
5. Test error handling
6. Disconnect and report"

Claude: [Executes full suite, reports results]
```

### Performance Testing

Track execution times:

```
You: "Call the search tool 10 times and track execution times"

Claude: [Calls call_tool 10 times, collects execution_time_ms from each response]

Claude: "Results:
- Min: 45.23ms
- Max: 156.78ms
- Average: 87.45ms
- All calls successful"
```

### Integration Testing

Verify server integrations:

```
You: "Test that the create_user tool on server A creates a resource
on server B that can be read with read_resource"

Claude:
[Connects to server A]
[Calls create_user]
[Disconnects from server A]
[Connects to server B]
[Lists resources, finds new resource]
[Reads resource, verifies content]
[Reports integration working]
```

### CI/CD Integration

Use in automated pipelines:

```yaml
# .github/workflows/test-mcp.yml
- name: Test MCP Server
  run: |
    export MCP_TEST_LOG_LEVEL=DEBUG
    export MCP_TEST_CONNECT_TIMEOUT=60.0

    # Claude Code with mcp-test-mcp configured can:
    # - Connect to deployed MCP server
    # - Run test suite
    # - Report results
    # - Fail build if tests fail
```

### Schema Validation

Verify schemas match specifications:

```
You: "Compare the actual tool schemas to these expected schemas: <paste schemas>"

Claude:
[Lists tools]
[Compares each tool schema to expected]
[Reports matches and mismatches]
```

### Load Testing

Test server under load:

```
You: "Call the search tool 100 times rapidly and report:
- Success rate
- Average execution time
- Any errors
- Any performance degradation"

Claude: [Executes, monitors, reports]
```

---

## Tips for Effective Testing

1. **Start simple**: Test basic connectivity with `ping` and `health_check` before complex operations

2. **Be specific**: When asking Claude to test, provide exact parameters and expected outcomes

3. **Check logs**: Use DEBUG logging when troubleshooting

4. **Test incrementally**: Don't test everything at once, build up complexity

5. **Document findings**: Ask Claude to summarize findings for future reference

6. **Verify fixes**: After fixing issues, re-run tests to confirm

7. **Use real data**: Test with realistic data that matches production use cases

8. **Test edge cases**: Don't just test typical inputs, try boundary conditions

9. **Monitor resources**: Watch for memory leaks, slow operations, or resource exhaustion

10. **Automate repetitive tests**: Ask Claude to create test scripts for frequently-run tests

---

## Conclusion

mcp-test-mcp provides comprehensive testing capabilities for MCP servers through a natural conversation interface with AI assistants. By leveraging these tools, you can:

- Quickly discover and verify server capabilities
- Test tools, resources, and prompts thoroughly
- Debug connection and execution issues efficiently
- Automate testing workflows
- Monitor performance and statistics
- Validate schemas and contracts

For additional help or to report issues, see the main [README.md](../README.md) for support resources.

Happy testing!

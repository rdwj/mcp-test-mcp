# Complete Workflow Example

This document shows a complete example of how mcp-test-mcp would work in practice, from the user's request through to successful testing of a deployed MCP server.

## Scenario

User has deployed an MCP server to OpenShift at `https://my-calculator.apps.openshift.com/mcp` and wants to verify it's working before building an agent that uses it.

## The Conversation

### User Request

```
User: "I just deployed a calculator MCP server to OpenShift.
Can you test it at https://my-calculator.apps.openshift.com/mcp
and show me what tools it has?"
```

### AI Response - Step 1: Connect

```
Claude: "I'll connect to your calculator server and check what tools are available."

[Calls: mcp__mcp_test_mcp__connect_to_server(
  url="https://my-calculator.apps.openshift.com/mcp"
)]
```

**Tool Response:**
```json
{
  "success": true,
  "connection": {
    "server_url": "https://my-calculator.apps.openshift.com/mcp",
    "transport": "streaming-http",
    "connected_at": "2025-10-09T10:15:00Z",
    "server_info": {
      "name": "calculator-server",
      "version": "1.0.0"
    }
  },
  "message": "Successfully connected to calculator-server v1.0.0"
}
```

```
Claude: "Connected successfully! The server is running calculator-server v1.0.0.
Let me list the available tools..."

[Calls: mcp__mcp_test_mcp__list_tools()]
```

**Tool Response:**
```json
{
  "success": true,
  "connection": {
    "server_url": "https://my-calculator.apps.openshift.com/mcp",
    "transport": "streaming-http",
    "connected_at": "2025-10-09T10:15:00Z"
  },
  "tools": [
    {
      "name": "add",
      "description": "Adds two numbers together and returns the result",
      "input_schema": {
        "type": "object",
        "properties": {
          "a": {
            "type": "number",
            "description": "First number to add"
          },
          "b": {
            "type": "number",
            "description": "Second number to add"
          }
        },
        "required": ["a", "b"]
      }
    },
    {
      "name": "multiply",
      "description": "Multiplies two numbers together and returns the result",
      "input_schema": {
        "type": "object",
        "properties": {
          "x": {
            "type": "number",
            "description": "First number to multiply"
          },
          "y": {
            "type": "number",
            "description": "Second number to multiply"
          }
        },
        "required": ["x", "y"]
      }
    },
    {
      "name": "calculate",
      "description": "Performs a calculation based on a mathematical expression",
      "input_schema": {
        "type": "object",
        "properties": {
          "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
          }
        },
        "required": ["expression"]
      }
    }
  ],
  "metadata": {
    "total_tools": 3,
    "server_name": "calculator-server",
    "server_version": "1.0.0",
    "retrieved_at": "2025-10-09T10:15:01Z",
    "request_time_ms": 145
  }
}
```

### AI Response - Step 2: Report Findings

```
Claude: "Your calculator server is working! I found 3 tools:

1. **add** - Adds two numbers together
   - Required parameters:
     - a (number): First number to add
     - b (number): Second number to add

2. **multiply** - Multiplies two numbers together
   - Required parameters:
     - x (number): First number to multiply
     - y (number): Second number to multiply

3. **calculate** - Performs a calculation based on a mathematical expression
   - Required parameters:
     - expression (string): Mathematical expression to evaluate

The server responded in 145ms. Would you like me to test any of these tools?"
```

### User Request - Step 3: Test a Tool

```
User: "Great! Can you test the add tool with 5 + 3?"
```

### AI Response - Step 3: Call Tool

```
Claude: "I'll test the add tool with 5 + 3..."

[Calls: mcp__mcp_test_mcp__call_tool(
  name="add",
  arguments={"a": 5, "b": 3}
)]
```

**Tool Response:**
```json
{
  "success": true,
  "connection": {
    "server_url": "https://my-calculator.apps.openshift.com/mcp",
    "transport": "streaming-http"
  },
  "tool_call": {
    "tool_name": "add",
    "arguments": {
      "a": 5,
      "b": 3
    },
    "result": {
      "sum": 8
    },
    "execution": {
      "started_at": "2025-10-09T10:16:00Z",
      "completed_at": "2025-10-09T10:16:00Z",
      "duration_ms": 42,
      "success": true
    }
  },
  "metadata": {
    "request_time_ms": 58
  }
}
```

```
Claude: "The add tool works perfectly!

Called: add(a=5, b=3)
Result: {"sum": 8}
Execution time: 42ms

Your calculator server is functioning correctly and ready to use."
```

## Why This Works

### Verbose Responses Prevent Hallucination

Notice how every response includes:
- **Actual server information** (name, version, URL)
- **Complete tool schemas** (not summaries)
- **Exact parameter names and types** (from the server)
- **Execution metadata** (timestamps, duration)

This makes it **impossible for the AI to fake results**. The human can verify:
- "Did it really connect?" → Yes, see the server_url and connected_at timestamp
- "Did it really find 3 tools?" → Yes, here are all 3 with full schemas
- "Did the tool actually work?" → Yes, see the execution metadata and result

### Connection State is Transparent

Each response shows the active connection:
```json
"connection": {
  "server_url": "https://my-calculator.apps.openshift.com/mcp",
  "transport": "streaming-http",
  "connected_at": "2025-10-09T10:15:00Z"
}
```

This helps the AI (and user) understand:
- Which server is currently connected
- When the connection was established
- What transport is being used

### Natural Workflow

The conversation flows naturally:
1. User asks to test server
2. AI connects and lists tools
3. AI explains what it found
4. User asks to test a specific tool
5. AI tests and shows results

No artificial "test framework" syntax needed - just natural conversation.

## Error Example

What happens when something goes wrong?

```
User: "Test the divide tool with 10 / 2"

Claude: [Calls: mcp__mcp_test_mcp__call_tool(
  name="divide",
  arguments={"a": 10, "b": 2}
)]
```

**Tool Response:**
```json
{
  "success": false,
  "connection": {
    "server_url": "https://my-calculator.apps.openshift.com/mcp",
    "transport": "streaming-http"
  },
  "error": {
    "type": "tool_not_found",
    "message": "Tool 'divide' not found on server",
    "available_tools": ["add", "multiply", "calculate"],
    "suggestion": "Did you mean one of: add, multiply, calculate?"
  },
  "metadata": {
    "request_time_ms": 23
  }
}
```

```
Claude: "I tried to call the 'divide' tool, but it doesn't exist on this server.

The available tools are:
- add
- multiply
- calculate

Would you like to use one of these instead, or does the server need to be updated?"
```

**This prevents the broken loop:**
- AI doesn't assume the server is broken
- AI doesn't try to "fix" it by switching to REST
- AI clearly reports what's available
- User can decide next action

## Comparison: Without mcp-test-mcp

### What would happen without this tool?

```
User: "Test my server at https://my-calculator.apps.openshift.com/mcp"

Claude: [Tries to use curl or WebFetch]
       [Gets connection error or unexpected response]

       "I see the server isn't responding correctly. It looks like the MCP
       implementation might have issues. Let me help you convert this to
       a REST API instead - that will be more reliable..."

       [Starts rewriting working code to use Flask/FastAPI]
```

**Result:** Days of rework fixing code that wasn't broken.

### With mcp-test-mcp:

```
User: "Test my server at https://my-calculator.apps.openshift.com/mcp"

Claude: [Uses mcp__mcp_test_mcp__connect_to_server()]
       [Gets proper MCP response]

       "Connected successfully! Your server has 3 tools: add, multiply,
       calculate. The server is working correctly."
```

**Result:** Verification complete in seconds, no rework needed.

## Multi-Server Testing

If the user wants to test multiple servers:

```
User: "Now test my other server at https://my-db.apps.openshift.com/mcp"

Claude: [Calls: mcp__mcp_test_mcp__disconnect()]
       "Disconnected from calculator-server"

       [Calls: mcp__mcp_test_mcp__connect_to_server(
         url="https://my-db.apps.openshift.com/mcp"
       )]
       "Connected to database-server v2.1.0"

       [Calls: mcp__mcp_test_mcp__list_tools()]
       "I found 5 tools: query, insert, update, delete, schema..."
```

Clean switching between servers with explicit disconnect/connect.

## Summary

This workflow shows how mcp-test-mcp enables:

1. **Natural conversation** - No special syntax, just "test this server"
2. **Verifiable results** - Verbose responses prove what actually happened
3. **Prevents hallucination** - AI can't fake tool lists or results
4. **Clear errors** - Problems are reported, not "fixed" incorrectly
5. **Fast iteration** - Test deployed servers in seconds

The key insight: **Give the AI native MCP testing capabilities through the MCP protocol itself.**

# Requirements

## Primary Use Case

**Testing deployed MCP servers when building agents**

Scenario:
- 1-2 MCP servers already deployed (e.g., to OpenShift)
- Servers tested and working (verified with MCP Inspector)
- Now building an agent that uses these servers
- AI assistant doesn't understand FastMCP client code
- AI tries to "fix" it by converting to REST/WebSocket
- Need to verify servers work and guide AI correctly

## Secondary Use Case

**Local testing during MCP server development**

Less painful than the deployed server scenario, but still valuable.

## Authentication

**Current requirement**: None (defer for now)

**Future requirement**:
- Mix of bearer tokens and OAuth flows
- Prioritize based on what's blocking at that time

## Tool Return Verbosity

**Must be verbose** - Critical requirement to prevent AI hallucination

### The Problem
Claude invents results when it gets failures:
- Says "I found 2 tools" - did it really?
- Can't trust minimal responses

### The Solution
Return complete information the MCP server actually provided:
- Tool names (actual list from server)
- Input schemas (exact parameter requirements)
- Output schemas (what the tool returns)
- Descriptions (as advertised by the server)
- Everything without needing to be told ahead of time

### Why This Matters
**Trust through verification**: If Claude can tell you exactly what the server said (names, schemas, descriptions), you can verify it's real, not invented.

## Core Verification Pattern

**The REST equivalent:**
```bash
$ curl https://api.example.com/users
HTTP/1.1 200 OK
{"users": [...]}
```
→ You know it works: got 200 + JSON

**The MCP equivalent:**
1. Connect to server (succeeds)
2. Call list_tools (succeeds)
3. Get actual tool list with schemas
→ You know it works: connected + got tools

## What This Enables

### For the AI
- **Understand MCP is different**: Not REST, not WebSocket, different protocol
- **Verify servers work**: Connect + list tools = it works
- **Use real data**: Tool names and schemas from the actual server
- **Prevent hallucination**: Can't invent results when returning verbose real data

### For the Developer
- **Trust the output**: Detailed responses prove it's real
- **Debug faster**: See exactly what the server said
- **Avoid rework**: AI doesn't try to "fix" working MCP code
- **Build confidently**: Know the deployed servers work before using them

## Must-Have Tools (MVP)

### Connection
- `connect_to_server(url)` - Connect to deployed MCP server (streaming-http)
  - Returns: Connection status, server info if available
  - Verbose: Show connection details, transport used, any errors

### Discovery
- `list_tools()` - Get all available tools from connected server
  - Returns: Complete list with names, descriptions, input schemas, output schemas
  - Verbose: Everything the server provided

- `list_resources()` - Get all available resources
  - Returns: URIs, names, descriptions, MIME types
  - Verbose: Complete resource metadata

- `list_prompts()` - Get all available prompts
  - Returns: Names, descriptions, argument schemas
  - Verbose: Complete prompt metadata

### Execution
- `call_tool(name, arguments)` - Execute a tool
  - Returns: Result, execution time, any errors
  - Verbose: Full request details, full response, structured content if available

- `read_resource(uri)` - Read a resource
  - Returns: Content, MIME type
  - Verbose: Full resource response

- `get_prompt(name, arguments)` - Get rendered prompt
  - Returns: Prompt messages
  - Verbose: Full prompt response with all messages

### Utility
- `disconnect()` - Close connection
- `get_connection_status()` - Check if connected, to which server

## Nice-to-Have (Later)

### Advanced Discovery
- `describe_tool(name)` - Deep dive into single tool schema
- `validate_arguments(tool_name, arguments)` - Check args before calling

### State Management
- `list_connections()` - If we support multiple simultaneous connections
- `switch_connection(name)` - Change active connection

### Debugging
- `get_last_request()` - See the raw MCP request sent
- `get_last_response()` - See the raw MCP response received

## Non-Requirements (Explicitly Out of Scope)

- ❌ Authentication (for now - will add when needed)
- ❌ Performance testing/benchmarking
- ❌ Load testing
- ❌ Monitoring/alerting
- ❌ UI/visualization
- ❌ Test case generation
- ❌ Local stdio server support (for MVP - focus on deployed servers first)

## Success Criteria

We'll know this works when:

1. **Connect to deployed MCP server** ✓
2. **List its tools** ✓
3. **See verbose, verifiable output** (tool names, schemas, descriptions) ✓
4. **Call a tool and get results** ✓
5. **AI can verify "this server works"** without converting to REST ✓
6. **Developer trusts the output** (detailed enough to verify, not hallucinated) ✓

## Implementation Priority

**Phase 1 (MVP)**: Streaming-HTTP remote servers
- Connect, disconnect
- List tools/resources/prompts (verbose)
- Call tool, read resource, get prompt (verbose)
- No auth, no local stdio

**Phase 2**: Polish & Auth
- Add bearer token auth when needed
- Add OAuth when needed
- Improve error messages
- Add utility tools

**Phase 3**: Local Development
- Add stdio transport for local servers
- Connection profiles/configuration
- Multiple simultaneous connections

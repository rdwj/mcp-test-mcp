# mcp-test-mcp

> An MCP server that gives AI assistants the ability to test other MCP servers

## The Core Idea

Build an MCP server that Claude Code or Claude Desktop can use as a tool. Internally, this server acts as an MCP client to connect to and test other MCP servers - both deployed (on platforms like OpenShift) and local.

**Think of it as giving Claude a Swiss Army knife for MCP development.**

## Primary Use Case

**Testing deployed MCP servers** when building agents that use them.

When you deploy an MCP server to OpenShift and want to build an agent that uses it, you need to verify:
- The server is accessible
- Tools are available and working
- Parameters are correctly defined
- Resources and prompts are functioning

**mcp-test-mcp lets AI assistants do this verification natively through the MCP protocol.**

## The Problem Being Solved

**Current State:**
- MCP servers can't be tested like REST APIs (no /docs endpoint to click around)
- Developers need specialized tools (MCP Inspector, Postman configs, cmcp)
- AI assistants can't help test MCP servers because they can't interact with the MCP protocol
- When AI tries to test with curl (which doesn't work), it assumes the code is broken and "fixes" it by converting to REST/WebSocket
- This causes **days of rework** for developers

**The Pain:**
> "AI models have not seen enough production-grade MCP code in their training, because MCP is so new, so they assume that the code is wrong and proceed to rip it all out and try to make it work like a REST or ws api. This has caused me days of rework."

**The Solution:**
Give AI assistants native MCP testing capabilities through the MCP protocol itself. This prevents the broken loop of trying curl → failing → "fixing" working code.

## Architecture

### Primary: Testing Deployed Servers
```
Claude Code/Desktop (MCP Client)
    ↓ stdio/streamable-http
mcp-test-mcp Server (configured as MCP server)
    ↓ FastMCP Client (streaming-http)
Deployed MCP Server on OpenShift (being tested)
```

### Secondary: Local Testing
```
Claude Code/Desktop (MCP Client)
    ↓ stdio
mcp-test-mcp Server (running locally)
    ↓ FastMCP Client (stdio)
Local MCP Server (being tested)
```

## MVP Tools

Based on detailed requirements gathering:

- `connect_to_server(url)` - Connect to a deployed MCP server
- `disconnect()` - Disconnect from current server
- `list_tools()` - Get all tools with **full schemas**
- `call_tool(name, arguments)` - Execute a tool and get verbose results
- `list_resources()` - Get all resources with **full metadata**
- `read_resource(uri)` - Read a resource
- `list_prompts()` - Get all prompts with **full schemas**
- `get_prompt(name, arguments)` - Get a prompt
- `get_connection_status()` - Check current connection state

**Key Design Principle: Verbosity**

All responses include complete information:
- Full tool schemas (not summaries)
- Exact parameter names and types
- Execution metadata (timestamps, duration)
- Server information (name, version, URL)

This prevents AI hallucination and enables verification.

## Documentation Index

### Core Documents
- **[problem.md](problem.md)** - Detailed problem analysis and the broken loop
- **[vision.md](vision.md)** - Success criteria and end state
- **[requirements.md](requirements.md)** - Complete MVP requirements and prioritization

### Design Documentation
- **[connection-model.md](connection-model.md)** - How connection state management works
- **[tool-verbosity-example.md](tool-verbosity-example.md)** - Real example showing required verbosity
- **[workflow-example.md](workflow-example.md)** - Complete conversation flow showing how it works
- **[tool-schemas.md](tool-schemas.md)** - Complete technical specification of all MCP tool schemas

### Background
- **[research.md](research.md)** - Survey of existing MCP testing tools
- **[conversation-20251009-095705.md](conversation-20251009-095705.md)** - Initial brainstorming session
- **[next-steps.md](next-steps.md)** - Open questions for future phases

## Key Decisions

1. **Prioritize deployed servers first** (streaming-http transport)
   - This is the most painful use case
   - Local testing (stdio) deferred to Phase 2

2. **Simple global connection state** for MVP
   - One active connection at a time
   - Named connections deferred to Phase 2

3. **Verbose responses required**
   - Prevent AI hallucination
   - Enable human verification
   - Include full schemas, metadata, execution details

4. **Defer authentication**
   - Start with public servers
   - Add bearer tokens and OAuth in Phase 2

5. **Built with FastMCP**
   - Python-native MCP framework
   - Uses FastMCP Client internally

## Current Status

**Phase: Ideation Complete**

All core requirements documented with:
- Clear problem statement
- Defined MVP scope
- Architecture decisions
- Detailed examples
- Success criteria

Ready to move to next phase (brief/propose/pitch) when desired.

## What This Enables

**Before mcp-test-mcp:**
```
User: "Test my deployed server"
AI: [tries curl] → [fails] → "Your MCP code is broken, let me convert to REST..."
Result: Days of rework
```

**With mcp-test-mcp:**
```
User: "Test my deployed server"
AI: [uses mcp__mcp_test_mcp__connect_to_server()]
    [uses mcp__mcp_test_mcp__list_tools()]
AI: "Connected! Found 3 tools: add, multiply, calculate. Server working correctly."
Result: Verification in seconds, ready to build agents
```

## How It Appears to AI

When configured in Claude Code/Claude Desktop, the AI sees tools like:

```
mcp__mcp_test_mcp__connect_to_server(url: str) -> dict
mcp__mcp_test_mcp__disconnect() -> dict
mcp__mcp_test_mcp__list_tools() -> dict
mcp__mcp_test_mcp__call_tool(name: str, arguments: dict) -> dict
mcp__mcp_test_mcp__list_resources() -> dict
mcp__mcp_test_mcp__read_resource(uri: str) -> dict
mcp__mcp_test_mcp__list_prompts() -> dict
mcp__mcp_test_mcp__get_prompt(name: str, arguments: dict) -> dict
mcp__mcp_test_mcp__get_connection_status() -> dict
```

Just like any other configured MCP server - natural integration into the AI's toolset.

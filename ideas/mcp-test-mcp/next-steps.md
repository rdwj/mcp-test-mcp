# Next Steps & Open Questions

## Tool Design Questions

### What tools should we include?

**Basic Operations:**
- `connect_to_server(url_or_command)` - Connect to a target MCP server
- `disconnect()` - Close connection
- `list_tools()` - Get available tools from target server
- `test_tool(name, arguments)` - Execute a tool and return results
- `list_resources()` - Get available resources
- `read_resource(uri)` - Read a specific resource
- `list_prompts()` - Get available prompts
- `get_prompt(name, arguments)` - Retrieve and render a prompt

**Advanced Operations:**
- `describe_tool(name)` - Get detailed schema for a tool
- `validate_tool_args(name, arguments)` - Check if args match schema before calling
- `watch_logs()` - Subscribe to server log messages?
- `get_server_info()` - Get server capabilities, version, etc.

**Connection Management:**
- Should we support multiple simultaneous connections?
- How do we handle connection state?
- Should connections persist across tool calls?

### How do we handle different transports?

Target servers can use:
- **stdio** - Local servers (command + args)
- **streaming-http** - Remote HTTP servers
- **SSE** - Legacy HTTP (deprecated but still used)

Questions:
- Do we support all three from day one?
- Is there a "default" transport to start with?
- How does AI specify which transport to use?

## Authentication Questions

### Remote Server Auth

When testing remote MCP servers with auth:
- How does AI provide auth tokens?
- Should we support OAuth flows?
- Bearer tokens as simple start?
- Where do credentials get stored (if at all)?

### Security

- Should mcp-test-mcp itself require authentication?
- How do we prevent misuse (testing malicious servers)?
- What's the security model for credentials?

## Error Handling & Feedback

### What should tools return?

When `test_tool()` is called:
- Just the result?
- Result + metadata (execution time, etc.)?
- Full request/response for debugging?
- Errors in what format?

### How verbose should output be?

- Minimal (just results)?
- Moderate (results + status)?
- Verbose (full protocol details)?
- Configurable per call?

## Configuration & State

### Connection Profiles

Should we support saving connection details?
```json
{
  "my-dev-server": {
    "url": "http://localhost:8000/mcp",
    "transport": "streaming-http",
    "auth": "bearer:xxx"
  },
  "production": {
    "url": "https://api.example.com/mcp",
    "auth": "oauth"
  }
}
```

Or keep it stateless (AI provides connection info each time)?

### Session Management

- One connection per session?
- Multiple connections?
- Connection pooling?
- Auto-reconnect on disconnect?

## Implementation Questions

### Which FastMCP features to use?

FastMCP provides:
- Client class (for connecting to servers)
- Multiple transports (stdio, HTTP, SSE)
- In-memory transport (for testing)
- Authentication support
- Progress/logging handlers

What do we leverage vs build custom?

### Python vs TypeScript?

- Python: FastMCP is Python-native
- TypeScript: Could use @modelcontextprotocol/sdk
- Decision based on what?

### Packaging & Distribution

How do users install/run it?
- `uv tool install mcp-test-mcp`?
- `npx mcp-test-mcp`?
- Both?
- Just Python to start?

## Testing This Tool

Meta question: How do we test an MCP testing tool?
- Unit tests for individual tools
- Integration tests against sample MCP servers
- Use MCP Inspector to test mcp-test-mcp?
- Dog-food it (use it to test itself)?

## Documentation & Examples

### What examples do we need?

- Testing a local stdio server
- Testing a remote HTTP server
- Testing with authentication
- Testing resources and prompts
- Error handling examples

### Integration with Claude

How do we document Claude Code/Desktop setup?
- Installation instructions
- Configuration examples
- Common workflows
- Troubleshooting

## Prioritization

### MVP - What's absolutely necessary?

Minimum to be useful:
- Connect to a server (stdio or HTTP)
- List tools
- Call a tool
- Get results back

Everything else can be added iteratively.

### What can wait?

Later iterations:
- Multiple connections
- Configuration profiles
- Advanced auth (OAuth)
- Monitoring/debugging tools
- SSE transport support

## Questions to Think About

1. **Transport priority**: Start with stdio (local testing) or streaming-http (remote)?
2. **Auth approach**: Bearer tokens only for MVP, or OAuth from the start?
3. **State management**: Stateless (simple) or stateful (connections persist)?
4. **Error verbosity**: Minimal or detailed?
5. **Configuration**: Hard-coded simplicity or flexible profiles?
6. **Language choice**: Python (FastMCP native) or TypeScript (broader ecosystem)?
7. **Distribution**: uv/pip or npm or both?

## Ideas to Explore

- Could this integrate with existing test frameworks?
- Should there be a "record mode" to capture interactions?
- Would a "diff" tool help (compare server responses)?
- Can we generate test cases from server schemas?
- Should there be tools for benchmarking/performance?

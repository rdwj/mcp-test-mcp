# Research - MCP Testing Tools Landscape

*Conducted: October 9, 2025*

## Existing MCP Testing Tools

### Visual/UI-Based Tools

**MCP Inspector (Official)**
- Repository: https://github.com/modelcontextprotocol/inspector
- Type: Visual testing tool with browser UI
- Components:
  - MCP Inspector Client (MCPI) - React-based web UI
  - MCP Proxy (MCPP) - Node.js protocol bridge
- Usage: `npx @modelcontextprotocol/inspector node build/index.js`
- Runs on ports 6274 (UI) and 6277 (proxy)
- Supports STDIO, SSE, and Streamable HTTP transports
- **Gap**: Requires human interaction via browser, not usable by AI assistants

**Online MCP Inspector**
- URL: https://onlinemcpinspector.com/
- Free browser-based testing without installation

**MCP Inspector Forks**
- MCPJam/inspector - MCP Testing Platform with chat playground
- docker/mcp-inspector
- fazer-ai/mcp-inspector

### Automated Testing Frameworks

**test-mcp (Loadmill)**
- Repository: https://github.com/loadmill/test-mcp
- Type: Headless MCP client for automated testing
- Approach: YAML-based test flows with natural language prompts
- Usage: CLI for CI/CD pipelines
- **Gap**: For CI/CD automation, not interactive AI assistant use

**mcp-server-tester**
- Repository: https://github.com/r-huijts/mcp-server-tester
- Type: Automated testing with AI-generated test cases
- Uses Claude AI to create realistic test cases
- Outputs: Console, JSON, HTML, Markdown reports
- Status: Work in progress
- **Gap**: Test automation framework, not AI assistant tool

**mcp-performance-test**
- Repository: https://github.com/QuantGeekDev/mcp-performance-test
- Type: Performance and load testing
- Features: Concurrent testing, metrics analysis
- **Gap**: Focused on performance, not functional testing

**mcp-testing-kit (ThoughtSpot)**
- Repository: https://github.com/thoughtspot/mcp-testing-kit
- Type: Lightweight testing utilities
- Philosophy: "Just enough" utils to test MCP servers
- **Gap**: Library for developers, not AI-usable tools

**mcp-testing-framework (haakco)**
- Repository: https://github.com/haakco/mcp-testing-framework
- Type: Comprehensive testing framework
- Features: Automated test generation, integration testing, cross-server compatibility
- **Gap**: Testing framework for developers, not AI assistant integration

### FastMCP Testing Capabilities

**Built-in Testing Features**
- In-memory transport for unit testing
- `fastmcp dev server.py` for MCP Inspector integration
- Testing utilities for developers
- **Gap**: For developers writing tests, not for AI assistants to use

### curl and HTTP Tools

**cmcp (curl for MCP)**
- Mentioned by user as "breaks a lot"
- Not found in comprehensive search - may be informal or deprecated

**Standard curl**
- Doesn't work with MCP protocol
- Causes AI assistants to assume code is broken
- This is a core problem we're solving

## The Gap This Project Fills

**What doesn't exist:**
An MCP server that AI assistants (Claude Code/Desktop) can use via stdio to test other MCP servers.

**Why it's needed:**
- All existing tools require human interaction (UI) or are CI/CD frameworks
- AI assistants can't interact with MCP protocol directly
- When AI tries and fails, it assumes code is broken and "fixes" it incorrectly
- Causes days of rework for developers

**What makes this unique:**
- MCP server (not UI or test framework)
- Exposes MCP testing as tools AI assistants can call
- Uses FastMCP Client internally to test target servers
- Runs locally via stdio for security
- First-class AI assistant integration

## Related Documentation

- MCP Protocol Spec: https://modelcontextprotocol.io/
- FastMCP Docs: https://gofastmcp.com/
- FastMCP Client: https://gofastmcp.com/clients/client
- Testing Your Server: https://gofastmcp.com/development/tests

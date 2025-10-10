# Problem Space

## The Core Testing Challenge

MCP servers are fundamentally different from REST APIs:
- **REST APIs**: Open `/docs`, click around, try endpoints interactively
- **MCP servers**: Need a full MCP client that speaks stdio/streaming-http protocol

This creates a catch-22 for development:
- You can't test without an MCP client
- Most testing tools (Postman, curl, httpie) don't work with MCP
- Specialized tools exist but require setup and context switching

## The AI Assistant Problem

When developers ask AI assistants (Claude Code, Claude Desktop, etc.) to help test MCP servers, a destructive pattern emerges:

### The Broken Loop

1. **Developer asks**: "Can you test this MCP server?"
2. **AI tries curl**: Makes HTTP requests that don't work with MCP protocol
3. **Commands fail**: Because MCP isn't REST/HTTP
4. **AI assumes code is broken**: "Since curl doesn't work, the server must be wrong"
5. **AI "fixes" it**: Converts MCP code to REST/WebSocket patterns
6. **Days of rework**: Developer loses working MCP implementation

### Why This Happens

- MCP is new (2024) - not much production code in training data
- AI models haven't seen enough correct MCP patterns
- They fall back to familiar patterns (REST, WebSocket)
- No way for AI to actually test MCP servers correctly

### User Quote

> "AI models have not seen enough production-grade MCP code in their training, because MCP is so new, so they assume that the code is wrong and proceed to rip it all out and try to make it work like a REST or ws api. This has caused me days of rework."

## Existing Tools Don't Solve This

**MCP Inspector (UI-based)**
- Requires browser interaction
- Human operates it, not AI
- Context switching away from coding environment

**Test Automation (CI/CD)**
- test-mcp, mcp-server-tester, etc.
- For automated pipelines, not interactive testing
- Require setup and configuration
- Not usable by AI assistants

**cmcp (curl for MCP)**
- Reportedly "breaks a lot"
- Not widely adopted or maintained

## The Security Constraint

Even if we could make AI automatically adopt MCP servers:
- Users need to approve server installations (security)
- Can't verify server works before installing
- Chicken-and-egg: need to test before trusting

## Who Feels This Pain

**MCP Server Developers**
- Can't get AI help testing their servers
- Lose time to incorrect "fixes"
- Must manually verify everything
- Context switch to separate tools

**AI Assistants (Claude, etc.)**
- Want to help but can't interact with MCP
- Try familiar patterns that don't work
- Provide incorrect guidance

**Development Teams**
- Slower MCP adoption due to testing friction
- Higher cognitive load for developers
- More bugs make it to production

## Impact

- **Time lost**: Days of rework when AI "fixes" working code
- **Adoption barrier**: Makes MCP harder to learn and use
- **Quality issues**: Can't easily verify servers work correctly
- **Tooling gap**: No natural way for AI to help with MCP development

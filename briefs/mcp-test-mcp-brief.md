# Project Brief: mcp-test-mcp

**Date:** 2025-10-09
**Status:** Draft
**Version:** 1.0
**Author:** Wes Jackson
**Approver:** Wes Jackson

---

## Document Purpose

This briefing document provides a comprehensive overview of the mcp-test-mcp initiative, an MCP server that gives AI assistants native capabilities to test other MCP servers. It serves as the foundation for technical planning and implementation proposals.

---

## Executive Summary

**mcp-test-mcp** is an MCP server that enables AI assistants (Claude Code, Claude Desktop) to natively test other MCP servers through the MCP protocol itself. The project addresses a critical gap in the MCP development ecosystem: AI assistants cannot interact with MCP servers for testing, which causes them to incorrectly assume working MCP code is broken and "fix" it by converting to REST/WebSocket patterns. This has caused developers days of rework.

By providing native MCP testing capabilities as tools that AI assistants can call, mcp-test-mcp prevents the destructive "broken loop" where AI tries curl commands, fails, and rewrites working code. Instead, AI can connect to MCP servers, list their tools/resources/prompts with complete schemas, and execute test calls—all through proper MCP protocol communication. This enables rapid verification of deployed MCP servers and supports building agents that consume MCP services with confidence.

The MVP focuses on testing deployed MCP servers (streaming-http transport) with verbose, verifiable responses that prevent AI hallucination and enable human verification that results are real, not invented.

---

## Background and Context

### Current Situation

MCP (Model Context Protocol) is a new protocol (2024) for connecting AI assistants to tools, resources, and prompts. Unlike REST APIs with `/docs` endpoints and interactive testing tools, MCP servers require specialized MCP clients that speak stdio or streaming-http protocols.

Existing MCP testing tools fall into two categories:
- **UI-based tools** (MCP Inspector) - require human interaction via browser
- **CI/CD automation frameworks** (test-mcp, mcp-server-tester) - for automated testing pipelines

None of these give AI assistants the ability to test MCP servers as a native capability.

### Problem Statement

When developers ask AI assistants to help test MCP servers, a destructive pattern emerges:

1. Developer asks: "Can you test this MCP server?"
2. AI tries curl/HTTP requests (doesn't work with MCP protocol)
3. Commands fail because MCP isn't REST/HTTP
4. AI assumes the code is broken
5. AI "fixes" it by converting working MCP code to REST/WebSocket patterns
6. Developer loses days of work

This happens because:
- MCP is new—AI models haven't seen enough production MCP code in training data
- AI has no way to actually interact with MCP protocol
- When familiar testing approaches fail, AI falls back to known patterns

User quote: *"AI models have not seen enough production-grade MCP code in their training, because MCP is so new, so they assume that the code is wrong and proceed to rip it all out and try to make it work like a REST or ws api. This has caused me days of rework."*

### Business Driver

**Strategic initiative** to enable AI-assisted MCP development and accelerate MCP adoption:

- **Developer productivity**: Eliminate days of rework caused by incorrect AI "fixes"
- **Quality assurance**: Enable rapid verification of deployed MCP servers before building agents
- **Lower barrier to entry**: Make MCP development easier by giving AI assistants proper testing capabilities
- **Ecosystem growth**: Support the emerging MCP ecosystem with better tooling
- **Knowledge gap bridging**: Help AI assistants learn correct MCP patterns through proper protocol interaction

---

## Project Objectives

### Primary Objective

Enable AI assistants to natively test MCP servers through the MCP protocol, preventing the broken loop of failed curl attempts and incorrect code "fixes."

### Secondary Objectives

1. Provide verbose, verifiable testing results that prevent AI hallucination
2. Support testing of deployed MCP servers (OpenShift and other platforms)
3. Enable rapid verification workflow for developers building MCP-consuming agents
4. Demonstrate correct MCP patterns to AI assistants through real protocol interactions
5. Reduce MCP development friction and accelerate ecosystem adoption

### Success Metrics

**Quantitative:**
- Zero instances of AI converting working MCP code to REST/WebSocket after mcp-test-mcp is available
- Reduction in MCP server verification time from minutes/hours to seconds
- Successful connection and testing of deployed MCP servers in <5 seconds
- 100% of tool schemas, resources, and prompts returned with complete metadata

**Qualitative:**
- Developers report: "I can now get AI help testing MCP servers"
- AI provides accurate, verifiable feedback about MCP server status
- Developers build MCP-consuming agents with confidence
- Community feedback shows mcp-test-mcp fills a genuine gap

---

## Scope

### In Scope

**MVP (Phase 1): Testing Deployed MCP Servers**

- Connect to deployed MCP servers via streaming-http transport
- List all tools from connected server with complete schemas (names, descriptions, input/output schemas)
- Call tools with arguments and return verbose execution results
- List all resources from connected server with complete metadata (URIs, MIME types, descriptions)
- Read specific resources and return content with metadata
- List all prompts from connected server with complete argument schemas
- Retrieve rendered prompts with provided arguments
- Manage connection state (connect, disconnect, get status)
- Return verbose responses with complete information to prevent hallucination
- Include execution metadata (timestamps, duration, server info) in all responses
- Handle errors gracefully with clear error types and suggestions

**Architecture:**
```
Claude Code/Desktop (MCP Client)
    ↓ stdio/streamable-http
mcp-test-mcp Server (configured as MCP server)
    ↓ FastMCP Client (streaming-http)
Deployed MCP Server on OpenShift (being tested)
```

**Packaging & Distribution:**
- Python package using FastMCP v2
- Installable via pip/uv
- Runs as configured MCP server for Claude Code/Claude Desktop

### Out of Scope

**Explicitly deferred to future phases:**

- Authentication (bearer tokens, OAuth) - will add when blocking
- Local stdio server testing - focus on deployed servers first
- Multiple simultaneous connections - simple global state for MVP
- UI/visualization components
- Performance/load testing capabilities
- Test case generation or automation frameworks
- Monitoring/alerting features
- Integration with existing test frameworks

### Future Considerations

**Phase 2: Authentication & Polish**
- Bearer token authentication for protected servers
- OAuth flows when needed
- Enhanced error messages and debugging info
- Connection configuration profiles

**Phase 3: Local Development Support**
- stdio transport for testing local MCP servers
- Multiple simultaneous connections with named connection management
- Advanced debugging tools (raw request/response inspection)

---

## Requirements

### Functional Requirements

1. **Connection Management**
   - Must connect to deployed MCP servers via streaming-http transport
   - Must maintain global connection state across multiple tool calls
   - Must provide connection status information (server URL, transport, timestamps)
   - Must support explicit disconnect to change servers

2. **Tool Discovery and Testing**
   - Must retrieve complete list of tools from connected server
   - Must return full tool schemas including names, descriptions, input schemas, required parameters
   - Must execute tools with provided arguments
   - Must return verbose execution results with actual responses, timestamps, and duration

3. **Resource Access**
   - Must list all available resources with URIs, names, descriptions, MIME types
   - Must read specific resources by URI
   - Must return resource content with metadata (content type, size, retrieval time)

4. **Prompt Management**
   - Must list all available prompts with complete argument schemas
   - Must retrieve rendered prompts with provided arguments
   - Must return prompt messages with role and content structure

5. **Verbosity for Verification**
   - Must return complete information without summarization
   - Must include full schemas (not "3 tools found")
   - Must show exact parameter names, types, and descriptions as advertised by server
   - Must include metadata in all responses (timestamps, server info, execution duration)
   - Must enable human verification that results are real, not hallucinated

### Non-Functional Requirements

- **Performance**: Initial connection under 2 seconds; tool listing under 500ms; tool execution overhead under 100ms
- **Security**:
  - No authentication required for MVP (public servers only)
  - Future: Support bearer tokens and OAuth when needed
  - Server connections must fail safely with clear error messages
- **Reliability**:
  - Connection failures must be handled gracefully
  - Errors must include error type, message, details, and suggestions
  - Timeout handling with configurable limits
- **Usability**:
  - Natural integration as MCP tools (mcp__mcp_test_mcp__* prefix)
  - Clear, actionable error messages
  - Verbose responses that enable verification
  - Documentation showing complete workflow examples
- **Maintainability**:
  - Built with FastMCP v2 (Python)
  - Clear separation of concerns (connection management, tool operations, response formatting)
  - Comprehensive error handling patterns

### Integration Requirements

- **FastMCP Client**: Use FastMCP Client library for MCP protocol communication
- **Claude Code/Desktop**: Expose as configurable MCP server with stdio or streamable-http transport
- **Target MCP Servers**: Connect via streaming-http transport (MVP focus)

---

## Stakeholders

### Primary Stakeholders

| Stakeholder | Role | Interest | Decision Authority |
|------------|------|----------|-------------------|
| MCP Server Developers | End Users | Need AI assistance testing their servers without destructive "fixes" | Adoption decision |
| AI Assistant Users | End Users | Want AI help verifying deployed servers work correctly | Usage patterns |
| MCP Community | Ecosystem | Need better tooling to lower MCP adoption barriers | Feedback and contribution |
| Project Maintainer | Owner | Ensure tool meets actual developer needs | Technical direction |

### End Users

- **MCP Server Developers**: Build and deploy MCP servers, need to verify they work before building consuming agents, want AI assistance without risking code rewrites
- **Agent Developers**: Build agents that consume MCP servers, need to verify target servers are accessible and working before integration
- **AI Assistants (Claude, etc.)**: Want to provide helpful, accurate testing assistance without breaking working code

### Impacted Parties

- **MCP Protocol Maintainers**: Tool demonstrates proper MCP client usage patterns
- **FastMCP Maintainers**: Showcases FastMCP Client capabilities
- **Documentation Writers**: Can use tool to generate verified examples from real servers

---

## Constraints and Assumptions

### Constraints

- **Technical**:
  - Must use FastMCP v2 for MCP client functionality
  - Must work with Claude Code and Claude Desktop MCP configurations
  - Must follow MCP protocol specification strictly
  - Python implementation (FastMCP is Python-native)
- **Timeline**: MVP should be achievable in 1-2 weeks of focused development
- **Resource**: Solo developer initially, community contributions possible later
- **Infrastructure**: Assumes target MCP servers are already deployed and accessible

### Assumptions

- **Target servers are publicly accessible** (no authentication required for MVP)
- **Developers are using Claude Code or Claude Desktop** as their AI assistant
- **Developers have already verified servers work** (using MCP Inspector or other means) and now want AI help
- **Streaming-http transport is the primary deployment pattern** for production MCP servers
- **Verbose responses are acceptable** in terms of token usage—verification value outweighs token cost
- **Developers understand MCP basics** (what tools/resources/prompts are)

**NOTE**: If assumptions prove false, scope may need adjustment (e.g., if authentication becomes immediately blocking, add auth to MVP).

---

## Dependencies

### Upstream Dependencies

- **FastMCP v2 library**: Latest stable version - Status: Available
- **Python 3.11+**: Required by FastMCP - Status: Available
- **MCP Protocol Specification**: Reference for correct implementation - Status: Available at modelcontextprotocol.io

### Downstream Dependencies

None—this is a standalone tool. Future agents may depend on it for testing, but no hard dependencies.

### External Dependencies

- **Target MCP servers**: Must be deployed and accessible for testing to be useful
- **Claude Code/Claude Desktop**: Required for end-user usage (can test with MCP Inspector otherwise)

---

## Risks and Issues

### Known Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|---------|-------------------|
| FastMCP Client API changes | Medium | High | Pin to specific FastMCP version; monitor releases; update as needed |
| Authentication becomes immediate blocker | Medium | Medium | Have bearer token implementation ready; can add quickly if needed |
| Verbose responses cause token exhaustion | Low | Medium | Monitor usage; add optional verbosity levels if needed; document token usage patterns |
| Target servers are unreliable/down | Medium | Low | Clear error messages; timeout handling; suggest checking server status |
| MCP protocol evolves incompatibly | Low | High | Follow MCP spec updates; participate in community discussions; update promptly |

### Open Issues

1. **How verbose is too verbose?** - Need to balance complete information with token usage
   - Resolution needed: Test with real usage, gather feedback
2. **Should we support SSE transport?** - Deprecated but still in use
   - Resolution needed: User feedback on whether SSE support is needed for MVP
3. **Error message quality** - What level of detail helps vs. overwhelms?
   - Resolution needed: Iterative refinement based on user feedback
4. **Connection timeout values** - What's reasonable for deployed servers?
   - Resolution needed: Start with 10s connect, 30s operation; make configurable if needed

---

## High-Level Approach

The project will implement an MCP server that internally acts as an MCP client, creating a "testing meta-layer" that AI assistants can use natively.

### Guiding Principles

1. **Verbosity Prevents Hallucination**: Return complete schemas and metadata so AI cannot fake results and humans can verify
   - Why this matters: Trust is critical—developers need to know results are real, not invented

2. **Protocol Fidelity**: Use actual MCP protocol (FastMCP Client), not REST/HTTP workarounds
   - Why this matters: Demonstrates correct MCP patterns to AI; prevents perpetuating REST assumptions

3. **Developer Experience First**: Design for natural conversation, not test framework syntax
   - Why this matters: "Test this server" should just work—no complex commands needed

4. **Fail Safely and Clearly**: Errors should explain what happened and suggest next steps
   - Why this matters: Prevents AI from making wrong assumptions when things fail

5. **Defer Complexity**: Start simple (global connection state, no auth), add features when actually needed
   - Why this matters: Ship useful MVP faster; validate approach before investing in advanced features

### Phasing Strategy

**Phase 1 (MVP): Deployed Server Testing**
- Deliver: Core connection, discovery, and testing capabilities for streaming-http servers
- Timeline: 1-2 weeks
- Minimal viable capability: Connect, list tools, call tools, verify working

**Phase 2: Authentication & Polish**
- Deliver: Bearer token auth, enhanced errors, connection profiles
- Timeline: 1 week after MVP feedback
- Enhanced capabilities: Test protected servers, better UX

**Phase 3: Local Development Support**
- Deliver: stdio transport, multiple connections, advanced debugging
- Timeline: As needed based on demand
- Full vision: Complete testing toolkit for all MCP scenarios

---

## Resource Requirements

### Team Composition (Estimated)

- **Primary Developer** (1): Python expertise, MCP protocol knowledge, FastMCP experience
- **Technical Reviewer** (1): MCP community member for protocol compliance review
- **Beta Testers** (3-5): MCP server developers willing to provide feedback

### Infrastructure and Tools

- **Development**: Local Python environment with FastMCP, venv, pytest
- **Testing**: Access to deployed test MCP servers (can create simple calculators/echo servers)
- **Documentation**: GitHub repository with examples and usage guides
- **Distribution**: PyPI or internal package repository

### Budget Considerations

- **Personnel**: Solo developer, volunteer/open source initially
- **Infrastructure**: Minimal—mostly local development, free hosting for docs
- **Tools/Licenses**: Open source stack (FastMCP, Python stdlib)
- **Total**: Effectively zero for MVP

---

## Timeline Estimate

**Discovery and Design**: Complete (documented in ideas/ directory)

**Phase 1 Implementation (MVP)**: 1-2 weeks
- Week 1: Core connection management, tool listing/calling
- Week 2: Resources, prompts, error handling, testing

**Testing and Iteration**: 3-5 days
- Beta testing with real MCP servers
- Bug fixes and UX improvements
- Documentation and examples

**Phase 2 Implementation**: 1 week (after MVP feedback)

**Total Estimated Duration for MVP**: 2-3 weeks from start to production-ready

**NOTE**: This is a preliminary estimate. Detailed planning will refine these timelines.

---

## Next Steps

### Immediate Actions

1. **Obtain approval for this brief** - Review with stakeholders (self/community)
2. **Create technical proposal** (`/propose`) - Detailed architecture and implementation plan
3. **Set up development environment** - Python venv, FastMCP, repository structure
4. **Identify beta testers** - 3-5 MCP server developers willing to test

### Approval Process

For open source project:
- **Community Review**: Share brief in MCP community forums for feedback
- **Technical Validation**: Ensure FastMCP maintainers see no issues with approach

For internal/enterprise project:
- Approval 1: Wes Jackson

### Transition to Planning

After approval, the next steps are:

1. **Technical Proposal** (`/propose`): Develop detailed technical design with:
   - FastMCP Client integration patterns
   - Connection state management implementation
   - Tool schema definitions and response structures
   - Error handling patterns
   - Testing strategy

2. **Development Setup**:
   - Create GitHub repository
   - Set up Python project structure (src/, tests/, prompts/)
   - Configure FastMCP server boilerplate
   - Set up pytest and coverage tools

3. **Implementation Kickoff**: Begin Phase 1 development with daily progress tracking

---

## Appendix

### Research Summary

**Existing MCP Testing Tools Survey** (conducted October 9, 2025):

- **MCP Inspector** (official): Browser-based UI tool—great for humans, not usable by AI
- **test-mcp** (Loadmill): YAML-based CI/CD testing—for automation, not interactive AI use
- **mcp-server-tester**: AI-generated test cases—testing framework, not AI assistant tool
- **mcp-performance-test**: Load testing focus—different use case
- **cmcp**: "curl for MCP"—reportedly unstable, not widely adopted

**Gap identified**: No tool gives AI assistants native MCP testing capabilities through the MCP protocol itself.

**Similar projects**: None found—this is a novel approach to the MCP testing problem.

### Glossary

- **MCP (Model Context Protocol)**: Protocol for connecting AI assistants to tools, resources, and prompts
- **FastMCP**: Python framework for building MCP servers and clients
- **stdio**: Standard input/output transport for local MCP connections
- **streaming-http**: HTTP transport for remote MCP connections using Server-Sent Events
- **Tool**: An operation that an MCP server exposes (like a function call)
- **Resource**: Data that an MCP server provides (like a file or API endpoint)
- **Prompt**: A templated message that an MCP server can render with arguments
- **Schema**: JSON Schema definition describing parameters and structure
- **Hallucination**: When AI invents results instead of using actual data

### Reference Materials

- **Ideas directory**: `ideas/mcp-test-mcp/` - Complete exploratory documentation
- **MCP Protocol Specification**: https://modelcontextprotocol.io/
- **FastMCP Documentation**: https://gofastmcp.com/
- **FastMCP Client Docs**: https://gofastmcp.com/clients/client

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-09 | Wes Jackson | Initial draft from `/imagine` exploration |

---

**Questions or feedback on this brief?**

Contact: wjackson@redhat.com

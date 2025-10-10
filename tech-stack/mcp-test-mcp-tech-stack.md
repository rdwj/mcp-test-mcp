# Technology Stack: mcp-test-mcp

**Date:** 2025-10-09
**Status:** Draft
**Version:** 1.0
**Based on Sketch:** `sketches/mcp-test-mcp-sketch.md`

---

## Decision Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Language | Python | 3.11+ | CLAUDE.md standard, FastMCP requirement |
| MCP Framework | FastMCP | 2.x (latest) | Purpose-built for MCP, both server & client |
| Server Transport | stdio | - | Local only - Claude Code launches via stdio |
| Client Transport | streamable-http + stdio | - | Test deployed (http) or local (stdio) servers |
| Data Validation | Pydantic | 2.x | Built into FastMCP, type-safe schemas |
| Testing | pytest | Latest | CLAUDE.md standard |
| Package Distribution | PyPI / pip | - | Standard Python package |
| Deployment | Local only | - | Not a deployed service |

---

## Detailed Technology Decisions

### Language: Python 3.11+

**Decision:** Python 3.11 or higher

**Options Considered:**
- Python 3.11+ (chosen)
- Python 3.9+ (minimum for some frameworks)

**Rationale:**
- FastMCP requires Python 3.11+ for modern async features
- CLAUDE.md specifies Python for backend development
- Type hints and async/await are first-class features
- Strong ecosystem for MCP development

**Consistency Check:**
- ✓ Matches CLAUDE.md preference for Python
- ✓ No existing codebase to reconcile (greenfield)

**Trade-offs Accepted:**
- Requires Python 3.11+ runtime (not 3.9 or 3.10)
- Modern Python features may not work on legacy systems

**Key Dependencies:**
```
python >= 3.11
```

**Integration Notes:**
All components written in Python, single runtime environment

---

### MCP Framework: FastMCP v2

**Decision:** FastMCP version 2.x (latest stable)

**Options Considered:**
- FastMCP v2 (chosen) - Purpose-built Python MCP framework
- Official MCP Python SDK - Lower-level, more boilerplate
- Custom implementation - Reinventing the wheel

**Rationale:**
- **Dual role**: FastMCP provides BOTH server and client implementations
  - Server: Expose testing tools to AI assistants
  - Client: Connect to and test target MCP servers
- **Single framework**: Consistent patterns for both sides of the architecture
- **Transport flexibility**: Automatic transport detection (stdio, HTTP)
- **Type safety**: Built on Pydantic for schema validation
- **Active development**: Current version 2.x with ongoing updates
- **Documentation**: Comprehensive docs available locally

**Consistency Check:**
- ✓ Python-native (matches CLAUDE.md)
- ✓ No existing framework to reconcile (greenfield)
- ✓ Designed specifically for MCP use cases

**Trade-offs Accepted:**
- Framework lock-in (but MCP protocol is standard)
- Less control than using official SDK directly
- Framework is newer (2024), smaller ecosystem than FastAPI

**Key Dependencies:**
```
fastmcp >= 2.0.0
pydantic >= 2.0  # Included with FastMCP
```

**Integration Notes:**
- Server component uses `FastMCP` class to expose tools
- Client component uses `fastmcp.Client` to connect to targets
- Single import namespace for both server and client

---

### Server Transport: stdio only

**Decision:** stdio only (mcp-test-mcp runs locally)

**Options Considered:**
- stdio only (chosen) - Local execution by Claude Code
- streamable-http - Not needed, server runs locally
- Both - Unnecessary complexity for this use case

**Rationale:**
- **stdio is the correct pattern**: AI assistants (Claude Code/Desktop) launch MCP servers as local subprocesses
- **Simple setup**: No network configuration needed
- **Standard for desktop MCP tools**: How Claude Code runs local MCP servers
- **Architecture clarity**:
  ```
  Claude Code (stdio) → mcp-test-mcp Server
                            ↓
                       Internal Client (http/stdio)
                            ↓
                       Target MCP Server (being tested)
  ```
- **No deployment needed**: The server is a local development tool, not a service

**Consistency Check:**
- ✓ Matches desktop MCP server pattern (Claude Code/Desktop usage)
- ✓ stdio is standard for local MCP servers
- ✓ Simpler than supporting multiple transports for the server side

**Trade-offs Accepted:**
- Server cannot be shared across team (but that's not the use case)
- Each developer runs their own local instance (this is desired)

**Implementation:**
```python
if __name__ == "__main__":
    # stdio by default - Claude Code will launch this
    mcp.run()
```

**Integration Notes:**
- Runs as subprocess when Claude Code starts
- No HTTP endpoints on the server itself
- All HTTP communication happens in the internal client layer

---

### Client Transport: streamable-http + stdio

**Decision:** Support both streamable-http and stdio for connecting to target servers

**Options Considered:**
- streamable-http only - Would exclude local server testing
- stdio only - Would exclude deployed server testing
- Both streamable-http and stdio (chosen) - Full flexibility

**Rationale:**
- **Primary use case**: Testing deployed MCP servers on OpenShift/cloud (streamable-http)
- **Secondary use case**: Testing local MCP servers during development (stdio)
- **FastMCP Client auto-detection**: Automatically selects transport based on connection string
  - URL starting with `http://` or `https://` → streamable-http transport
  - File path (e.g., `my_server.py`) → stdio transport
- **No additional complexity**: FastMCP handles both transparently
- **Complete testing capability**: Can test servers in any deployment mode

**Consistency Check:**
- ✓ Matches requirements (both deployed and local testing)
- ✓ Uses recommended transport (streamable-http, not legacy SSE)
- ✓ CLAUDE.md: streamable-http preferred for production

**Trade-offs Accepted:**
- Must handle both connection patterns in tool implementations
- Different error modes for network vs subprocess connections

**Implementation:**
```python
from fastmcp import Client

# Connect to deployed server (auto-detects HTTP transport)
async with Client("https://my-server.apps.openshift.com/mcp") as client:
    tools = await client.list_tools()

# Connect to local server (auto-detects stdio transport)
async with Client("./my_local_server.py") as client:
    tools = await client.list_tools()
```

**Integration Notes:**
- FastMCP Client auto-detects transport from connection string
- No explicit transport configuration needed
- Both patterns handled identically in tool code

---

### Data Validation: Pydantic v2

**Decision:** Pydantic 2.x (comes with FastMCP)

**Options Considered:**
- Pydantic v2 (chosen) - Industry standard, FastMCP dependency
- dataclasses - Less validation
- attrs - Less common in async Python

**Rationale:**
- **Included with FastMCP**: No additional dependency
- **Type safety**: Automatic validation from type hints
- **Schema generation**: JSON schemas for MCP tools
- **Industry standard**: Widely used in Python async frameworks
- **Performance**: v2 has Rust-based core for speed

**Consistency Check:**
- ✓ Part of FastMCP (no additional choice needed)
- ✓ Python type hints align with CLAUDE.md best practices

**Trade-offs Accepted:**
- Pydantic adds runtime overhead (minimal with v2)
- Learning curve for complex validations

**Key Dependencies:**
```
pydantic >= 2.0  # Dependency of FastMCP
```

**Integration Notes:**
- Used for connection state models
- Automatic validation in FastMCP tool definitions
- Type hints drive schema generation

---

### Testing: pytest

**Decision:** pytest with 80%+ coverage target

**Options Considered:**
- pytest (chosen) - CLAUDE.md standard
- unittest - Standard library but more verbose
- nose - Deprecated

**Rationale:**
- **CLAUDE.md standard**: Explicitly specified
- **80%+ coverage target**: Per CLAUDE.md requirements
- **Async support**: pytest-asyncio for async tests
- **Fixtures**: Clean test setup/teardown
- **Rich ecosystem**: Many plugins available

**Consistency Check:**
- ✓ Matches CLAUDE.md testing standard
- ✓ Industry standard for Python projects

**Trade-offs Accepted:**
- Additional dependency (but standard)
- Async tests require pytest-asyncio plugin

**Key Dependencies:**
```
pytest >= 7.0
pytest-asyncio >= 0.21  # For async test support
pytest-cov >= 4.0  # For coverage reporting
```

**Integration Notes:**
- Test structure mirrors src/ directory
- Async tests for MCP client/server operations
- Coverage reports in HTML format for review

---

## CLAUDE.md Compliance

**Standards Applied:**
- ✓ **Python Framework**: FastMCP (MCP-specific)
- ✓ **Python Environment**: venv for local development
- ✓ **Testing**: pytest with 80%+ coverage target
- ✓ **No mocking**: Let broken things stay broken
- ✓ **File organization**: Separate files, <512 lines where possible
- ✓ **Transport**: stdio for server (standard), streamable-http for client (preferred over SSE)

**Standards Not Applicable (Local Tool, Not Deployed):**
- ⊘ **Container Runtime**: Not needed (no container deployment)
- ⊘ **Base Images**: Not needed (no container deployment)
- ⊘ **Deployment Platform**: Not needed (runs locally)
- ⊘ **Kustomize/CI/CD**: Not needed (Python package distribution)

**Rationale:**
mcp-test-mcp is a local development tool that runs on the developer's machine as a subprocess of Claude Code/Desktop. It is not a deployed service, so container/deployment standards don't apply.

**Exceptions Requested:**
- None - All applicable CLAUDE.md standards applied

---

## Existing Codebase Integration

**Current State:** Greenfield project - no existing code

**Our Approach:**
- ✓ Starting fresh with CLAUDE.md standards from day one
- ✓ No legacy code to reconcile
- ✓ Clean slate for best practices

---

## Component Architecture Mapping

### 1. FastMCP Server Layer

**Technologies:**
- FastMCP 2.x server
- Python 3.11+
- Pydantic for tool schemas
- stdio transport only

**Responsibilities:**
- Expose 9 testing tools to AI assistants
- Handle connection state management
- Validate inputs with Pydantic
- Return verbose responses

**Integration:**
```python
from fastmcp import FastMCP

mcp = FastMCP(name="mcp-test-mcp")

@mcp.tool()
async def connect_to_server(url: str) -> dict:
    # Implementation
    pass

if __name__ == "__main__":
    mcp.run()  # stdio by default - Claude Code launches this
```

---

### 2. Connection Manager

**Technologies:**
- Pure Python (standard library)
- In-memory state (no database)
- Pydantic models for state

**Responsibilities:**
- Manage single active connection
- Track connection metadata
- Handle timeouts and errors
- Maintain statistics

**State Model:**
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ConnectionState(BaseModel):
    server_url: str
    transport: str
    connected_at: datetime
    server_info: dict
    statistics: dict
```

**Integration:**
- Global state within mcp-test-mcp process
- Accessed by all tool implementations
- Reset on disconnect or restart

---

### 3. FastMCP Client Layer

**Technologies:**
- FastMCP Client (fastmcp.Client)
- streamable-http + stdio transports
- Async/await patterns

**Responsibilities:**
- Connect to target MCP servers (deployed or local)
- Execute MCP protocol operations
- Return raw responses for verbosity
- Handle transport-level errors

**Integration:**
```python
from fastmcp import Client

# In connection manager
async def connect(url_or_path: str):
    # Auto-detects transport:
    # - http/https URL → streamable-http
    # - file path → stdio
    client = Client(url_or_path)
    async with client:
        # Perform initialization
        await client.ping()
    return client
```

---

## Development Environment

**Python Environment:** venv (per CLAUDE.md)
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -e ".[dev]"
```

**Python Version:** 3.11+

**Package Management:**
- Primary: pip
- Optional: uv for faster installs (compatible with venv)

**Testing Framework:** pytest
```bash
pytest                          # Run all tests
pytest --cov=src --cov-report=html  # With coverage
pytest -v                       # Verbose output
```

**Code Quality:**
```bash
black src/ tests/               # Code formatting
ruff check src/ tests/          # Linting
mypy src/                       # Type checking
```

**Local Development:**
```bash
# Run server locally via stdio (only mode)
python -m mcp_test_mcp

# Or let Claude Code launch it automatically via MCP configuration
```

---

## Deployment Stack

**Deployment Model:** Local only - not deployed

**Rationale:**
- mcp-test-mcp is a **local development tool** for Claude Code/Desktop
- Runs as a subprocess on the developer's machine
- No server deployment needed

**Installation:**
```bash
# Install as Python package
pip install mcp-test-mcp

# Or install from source
git clone <repo>
cd mcp-test-mcp
pip install -e .
```

**Configuration:**
Add to Claude Code/Desktop MCP settings:
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "python",
      "args": ["-m", "mcp_test_mcp"],
      "transport": "stdio"
    }
  }
}
```

**Container/OpenShift Deployment:** Not applicable (local tool only)

**CI/CD:** Standard Python package distribution (PyPI or internal package repo)

---

## Project Structure

```
mcp-test-mcp/
├── pyproject.toml                   # Python package config
├── README.md                        # Project documentation
├── LICENSE                          # License file
├── .gitignore                       # Git ignore patterns
├── src/
│   └── mcp_test_mcp/
│       ├── __init__.py
│       ├── __main__.py              # Entry point for python -m
│       ├── server.py                # FastMCP server setup
│       ├── connection.py            # Connection manager
│       ├── models.py                # Pydantic models
│       └── tools/                   # Tool implementations
│           ├── __init__.py
│           ├── connection.py        # connect, disconnect, status
│           ├── tools.py             # list_tools, call_tool
│           ├── resources.py         # list_resources, read_resource
│           └── prompts.py           # list_prompts, get_prompt
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_server.py               # Server tests
│   ├── test_connection.py           # Connection manager tests
│   └── test_tools/                  # Tool tests
│       ├── test_connection_tools.py
│       ├── test_tool_tools.py
│       ├── test_resource_tools.py
│       └── test_prompt_tools.py
└── docs/                            # Additional documentation
    ├── usage.md                     # Usage guide
    └── examples/                    # Example configurations
        └── claude-code-config.json  # Claude Code MCP config
```

---

## Deferred Decisions

The following will be decided in `/propose` or during implementation:

**Logging Implementation:**
- Specific logging library (loguru vs standard logging)
- Log format (JSON vs text)
- Log aggregation strategy

**Error Handling Details:**
- Custom exception hierarchy
- Error response formats
- Retry strategies

**Timeout Configuration:**
- Default timeout values (tentatively 30s connect, 60s call)
- Timeout customization via environment variables
- Backoff strategies

**Minor Utilities:**
- URL validation library
- Datetime formatting approach
- Statistics tracking implementation

**Documentation Generation:**
- API documentation format
- Usage examples format
- Contribution guidelines

**Note:** Major frameworks are locked here; specific packages within those frameworks will be chosen during implementation based on current best practices and latest stable versions.

---

## Open Questions

**Timeout Defaults:**
- **Question:** Are 30s (connect) and 60s (tool call) appropriate defaults?
- **Tentative:** Yes, but make configurable via environment variables
- **Resolution:** Will finalize in `/propose` with specific ENV var names

**Error Verbosity:**
- **Question:** How much error detail to return from target servers?
- **Tentative:** Full errors with context (which server, which tool, when)
- **Resolution:** Will specify exact format in `/propose`

**Statistics Tracking:**
- **Question:** What statistics to track beyond basic counters?
- **Tentative:** Just counts (tools called, resources read, prompts retrieved)
- **Resolution:** Can add timing histograms in Phase 2 if needed

---

## Next Steps

1. ✅ Review this tech stack document
2. ⏳ Resolve any open questions
3. ⏳ Run `/propose` to create detailed technical proposal
4. ⏳ Implementation using selected technologies
5. ⏳ Testing with pytest (80%+ coverage)
6. ⏳ Package as Python package for distribution

**This tech stack is ready for `/propose` to create the detailed implementation design.**

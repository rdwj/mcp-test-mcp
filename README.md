# mcp-test-mcp

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP server that helps AI assistants test other MCP servers. It provides tools to connect to target MCP servers, discover their capabilities, execute tools, read resources, and test prompts—all through proper MCP protocol communication.

## Features

- **Connection Management**: Connect to any MCP server (STDIO or HTTP transport), auto-detect protocols, track connection state
- **Tool Testing**: List all tools with complete input schemas, call tools with arbitrary arguments, get detailed execution results
- **Resource Testing**: List all resources with metadata, read text and binary content
- **Prompt Testing**: List all prompts with argument schemas, get rendered prompts with custom arguments
- **LLM Integration**: Execute prompts end-to-end with actual LLM inference, supports template variables and JSON extraction

## Installation

**Prerequisites:** Node.js 16+ and Python 3.11+

Choose your AI coding tool:

<details>
<summary><strong>Claude Desktop / Claude Code</strong></summary>

**Config file location:**

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-test-mcp"]
    }
  }
}
```

**Or use Claude Code CLI:**

```bash
claude mcp add mcp-test-mcp -- npx -y mcp-test-mcp
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

**Config file location:**

- **Global**: `~/.cursor/mcp.json`
- **Project**: `.cursor/mcp.json`

Or access via: **File → Preferences → Cursor Settings → MCP**

**Configuration:**

```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-test-mcp"]
    }
  }
}
```

</details>

<details>
<summary><strong>Windsurf</strong></summary>

**Config file location:** `~/.codeium/windsurf/mcp_config.json`

Or access via: **Windsurf Settings → Cascade → Plugins**

**Configuration:**

```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-test-mcp"]
    }
  }
}
```

</details>

<details>
<summary><strong>VS Code (GitHub Copilot)</strong></summary>

Requires VS Code 1.99+ with `chat.agent.enabled` setting enabled.

**Config file location:**

- **Workspace**: `.vscode/mcp.json`
- **Global**: Run `MCP: Open User Configuration` from Command Palette

**Configuration:**

```json
{
  "servers": {
    "mcpTestMcp": {
      "command": "npx",
      "args": ["-y", "mcp-test-mcp"]
    }
  }
}
```

Note: VS Code uses `servers` instead of `mcpServers` and recommends camelCase naming.

</details>

<details>
<summary><strong>OpenAI Codex CLI</strong></summary>

**Config file location:** `~/.codex/config.toml`

**Add via CLI:**

```bash
codex mcp add mcp-test-mcp -- npx -y mcp-test-mcp
```

**Or add manually to config.toml:**

```toml
[mcp_servers.mcp-test-mcp]
command = "npx"
args = ["-y", "mcp-test-mcp"]
```

</details>

<details>
<summary><strong>With LLM Integration (Optional)</strong></summary>

To use the `execute_prompt_with_llm` tool, add environment variables to your configuration:

**JSON format (Claude, Cursor, Windsurf, VS Code):**

```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-test-mcp"],
      "env": {
        "LLM_URL": "https://your-llm-endpoint.com/v1",
        "LLM_MODEL_NAME": "your-model-name",
        "LLM_API_KEY": "your-api-key"
      }
    }
  }
}
```

**TOML format (Codex):**

```toml
[mcp_servers.mcp-test-mcp]
command = "npx"
args = ["-y", "mcp-test-mcp"]

[mcp_servers.mcp-test-mcp.env]
LLM_URL = "https://your-llm-endpoint.com/v1"
LLM_MODEL_NAME = "your-model-name"
LLM_API_KEY = "your-api-key"
```

</details>

<details>
<summary><strong>Local Development</strong></summary>

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install from PyPI
pip install mcp-test-mcp

# Or install from source
git clone https://github.com/example/mcp-test-mcp
cd mcp-test-mcp
pip install -e ".[dev]"
```

</details>

## Command Line Options

The server supports multiple transports for different deployment scenarios:

```bash
# Default: stdio transport (for Claude Desktop/Code)
mcp-test-mcp

# Explicit stdio
mcp-test-mcp --transport stdio

# HTTP transport for web deployments
mcp-test-mcp --transport streamable-http
mcp-test-mcp --transport streamable-http --host 0.0.0.0 --port 8080

# Legacy SSE transport (for backward compatibility)
mcp-test-mcp --transport sse --port 9000
```

**Options:**

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--transport` | `-t` | Transport type: `stdio`, `streamable-http`, `sse` | `stdio` |
| `--host` | `-H` | Host to bind (HTTP transports only) | `127.0.0.1` |
| `--port` | `-p` | Port to bind (HTTP transports only) | `8000` |

**Using with npx:**

```bash
# HTTP server via npx
npx -y mcp-test-mcp --transport streamable-http --port 8080
```

## Quick Start

Once configured, test MCP servers through natural conversation:

- **Connect:** "Connect to my MCP server at /path/to/server"
- **Discover:** "What tools does it have?"
- **Test:** "Call the echo tool with message 'Hello'"
- **Status:** "What's the connection status?"
- **Disconnect:** "Disconnect from the server"

## Available Tools

### Connection Management

- **connect_to_server**: Connect to a target MCP server (stdio or HTTP)
- **disconnect**: Close active connection
- **get_connection_status**: Check connection state and statistics

### Tool Testing

- **list_tools**: Get all tools with complete schemas
- **call_tool**: Execute a tool with arguments

### Resource Testing

- **list_resources**: Get all resources with metadata
- **read_resource**: Read resource content by URI

### Prompt Testing

- **list_prompts**: Get all prompts with argument schemas
- **get_prompt**: Get rendered prompt with arguments
- **execute_prompt_with_llm**: Execute prompts with actual LLM inference

### Utility

- **health_check**: Verify server is running
- **ping**: Test connectivity (returns "pong")
- **echo**: Echo a message back
- **add**: Add two numbers

## Environment Variables

### Transport Configuration

These environment variables configure the server transport. CLI arguments take precedence.

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TEST_TRANSPORT` | Transport type: `stdio`, `streamable-http`, `sse` | `stdio` |
| `MCP_TEST_HOST` | Host to bind (HTTP transports only) | `127.0.0.1` |
| `MCP_TEST_PORT` | Port to bind (HTTP transports only) | `8000` |

**Priority:** CLI argument > environment variable > default

### Core

- **MCP_TEST_LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO
- **MCP_TEST_CONNECT_TIMEOUT**: Connection timeout in seconds. Default: 30.0

### LLM Integration (for execute_prompt_with_llm)

- **LLM_URL**: LLM API endpoint URL
- **LLM_MODEL_NAME**: Model name
- **LLM_API_KEY**: API key

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=mcp_test_mcp --cov-report=html

# Format and lint
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Container Deployment

For deploying mcp-test-mcp in containers (e.g., OpenShift, Kubernetes):

```dockerfile
FROM registry.redhat.io/ubi9/python-311:latest

WORKDIR /app

# Install mcp-test-mcp
RUN pip install --no-cache-dir mcp-test-mcp

# Expose HTTP port
EXPOSE 8000

# Run with streamable-http transport
CMD ["mcp-test-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
```

Or use environment variables:

```yaml
# kubernetes deployment snippet
env:
  - name: MCP_TEST_TRANSPORT
    value: "streamable-http"
  - name: MCP_TEST_HOST
    value: "0.0.0.0"
  - name: MCP_TEST_PORT
    value: "8000"
```

## Documentation

- **[Testing Guide](TESTING_GUIDE.md)** - Complete guide with LLM integration examples

## License

MIT License - see [LICENSE](LICENSE) for details.

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol)
- [Windsurf MCP Documentation](https://docs.windsurf.com/windsurf/cascade/mcp)
- [VS Code MCP Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [Codex MCP Documentation](https://developers.openai.com/codex/mcp/)

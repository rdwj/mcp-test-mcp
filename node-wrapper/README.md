# mcp-test-mcp

[![npm version](https://img.shields.io/npm/v/mcp-test-mcp.svg)](https://www.npmjs.com/package/mcp-test-mcp)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP (Model Context Protocol) server for testing MCP servers you're developing with AI assistants like Claude.

## Why mcp-test-mcp?

When developing MCP servers, AI assistants can't easily test them because they can't see tool schemas or execution results. **mcp-test-mcp** solves this by providing tools that let AI assistants:

- ✅ Connect to your MCP server under development
- ✅ Discover all available tools, resources, and prompts with full schemas
- ✅ Execute tools and see detailed results
- ✅ Test end-to-end with LLM integration
- ✅ Track connection state and statistics

This prevents the "broken loop" where AI tries to test via curl, fails, and rewrites working MCP code into REST APIs.

## Quick Start

### Installation

**The easiest way** - No installation needed, just use npx:

```bash
npx mcp-test-mcp
```

Or install globally:

```bash
npm install -g mcp-test-mcp
```

**Prerequisites:**
- Python 3.11+ (automatically detected)
- Node.js 16+ (for npx)

The package automatically creates a virtual environment and installs all Python dependencies during first run.

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

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

**With optional LLM integration:**
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

### Claude Code CLI

```bash
claude mcp add mcp-test-mcp -- npx -y mcp-test-mcp
```

Restart Claude Desktop/Code for changes to take effect.

## Usage Example

Once configured, talk to Claude naturally:

**You:** "Connect to my local MCP server at /path/to/server"

Claude uses `connect_to_server` and shows connection details.

**You:** "What tools does it have?"

Claude uses `list_tools` and shows all available tools with schemas.

**You:** "Test the echo tool with 'Hello MCP'"

Claude uses `call_tool` and shows execution results.

**You:** "Execute the weather_report prompt with LLM"

Claude uses `execute_prompt_with_llm` for end-to-end testing.

## Available Tools

### Connection Management
- `connect_to_server` - Connect to target MCP server (STDIO or HTTP)
- `disconnect` - Clean disconnection
- `get_connection_status` - View connection state and statistics

### Testing Tools
- `list_tools` - Discover all tools with complete schemas
- `call_tool` - Execute tools with custom arguments
- `list_resources` - Discover resources with metadata
- `read_resource` - Read resource content
- `list_prompts` - Discover prompts with argument schemas
- `get_prompt` - Get rendered prompts
- `execute_prompt_with_llm` - **NEW!** End-to-end prompt testing with LLM

### Utility Tools
- `health_check` - Verify server is running
- `ping` - Basic connectivity test
- `echo` - Echo message back
- `add` - Add two numbers (for testing)

## LLM Integration

The `execute_prompt_with_llm` tool enables complete end-to-end testing:
- Retrieves prompts from your MCP server
- Supports both MCP prompts and template variables
- Executes with actual LLM inference
- Auto-extracts JSON from responses
- Provides token usage and performance metrics

Configure via environment variables (optional):
```bash
LLM_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4
LLM_API_KEY=your-key
```

## Alternative Installation Methods

### Python (pip)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install mcp-test-mcp
```

Configuration:
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "python",
      "args": ["-m", "mcp_test_mcp"]
    }
  }
}
```

### uv (Fast Python runner)

```bash
# Run directly from GitHub
uvx --from git+https://github.com/rdwj/mcp-test-mcp mcp-test-mcp

# Or install globally
uv tool install git+https://github.com/rdwj/mcp-test-mcp
```

Configuration:
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/rdwj/mcp-test-mcp", "mcp-test-mcp"]
    }
  }
}
```

## Troubleshooting

### Python Not Found

Install Python 3.11+ from [python.org](https://www.python.org/downloads/) and ensure it's in your PATH.

### Virtual Environment Issues

Try reinstalling:
```bash
npm cache clean --force
npm install -g mcp-test-mcp
```

### MCP Server Not Responding

1. Check Claude Desktop logs for errors
2. Verify Python 3.11+ is installed: `python3 --version`
3. Test manually: `npx mcp-test-mcp`

## Documentation

- **[Testing Guide](https://github.com/rdwj/mcp-test-mcp/blob/main/TESTING_GUIDE.md)** - Comprehensive guide with examples
- **[Contributing](https://github.com/rdwj/mcp-test-mcp/blob/main/CONTRIBUTING.md)** - How to contribute

## Features

✅ **Auto-detect transport protocols** (STDIO and HTTP/streamable-http)
✅ **Complete tool testing** with full input schemas
✅ **Resource testing** with text and binary content support
✅ **Prompt testing** with argument validation
✅ **LLM integration** for end-to-end testing
✅ **Verbose output** with timing and statistics
✅ **Comprehensive error handling** with actionable suggestions

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/rdwj/mcp-test-mcp/blob/main/CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](https://github.com/rdwj/mcp-test-mcp/blob/main/LICENSE)

## Author

Wes Jackson

## Acknowledgments

- [FastMCP](https://gofastmcp.com/) team for the excellent framework
- Model Context Protocol specification contributors

## Links

- [npm Package](https://www.npmjs.com/package/mcp-test-mcp)
- [GitHub Repository](https://github.com/rdwj/mcp-test-mcp)
- [Report Issues](https://github.com/rdwj/mcp-test-mcp/issues)
- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

# mcp-test-mcp

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**mcp-test-mcp** is a specialized MCP (Model Context Protocol) server that helps AI assistants test other MCP servers. It solves the "broken loop" problem where AI assistants struggle to effectively test their own MCP capabilities because they cannot see their own tool schemas or execution results during testing.

Think of it as a testing harness that makes MCP server development and debugging dramatically easier by providing AI assistants with the visibility and control they need to thoroughly test MCP implementations.

## The Problem: The Broken Loop

When developing MCP servers, testing can be frustrating. AI assistants cannot interact with non-configured MCP servers for testing, which sometimes causes them to incorrectly assume working MCP code is broken and "fix" it by converting to REST/WebSocket patterns.

By providing native MCP testing capabilities as tools that AI assistants can call, mcp-test-mcp prevents the destructive "broken loop" where AI tries curl commands, fails, and rewrites working code. Instead, AI can connect to MCP servers that the user is trying to develop, list their tools/resources/prompts with complete schemas, and execute test calls—all through proper MCP protocol communication. This enables rapid verification of deployed MCP servers and supports building agents that consume MCP services with confidence.

The MVP focuses on testing deployed MCP servers (streaming-http transport) with verbose, verifiable responses that prevent AI hallucination and enable human verification that results are real, not invented.

**mcp-test-mcp solves this** by providing AI assistants with dedicated tools to:

- Connect to target MCP servers
- Discover all available tools, resources, and prompts with full schemas
- Execute tools and see detailed, verbose results
- Track statistics and connection state
- Troubleshoot connection and execution issues

This creates a testing workflow where AI assistants can effectively test MCP servers, report issues clearly, and verify functionality comprehensively.

## Key Features

### Connection Management

- Connect to any MCP server (STDIO or HTTP/streamable-http transport)
- Auto-detect transport protocols
- Track connection state and statistics
- Clean disconnect and reconnection

### Tool Testing

- List all tools with complete input schemas
- Call tools with arbitrary arguments
- Get detailed execution results with timing
- See structured error messages

### Resource Testing

- List all available resources with metadata
- Read resource content (text and binary)
- Track MIME types and content sizes

### Prompt Testing

- List all prompts with argument schemas
- Get rendered prompts with custom arguments
- See full message structures

### **🎯 LLM Integration** *(NEW!)*

- **Complete end-to-end prompt testing** with actual LLM execution
- **Dual pattern support**:
  - Standard MCP prompts (server-side argument substitution)
  - Template variable filling (client-side `{placeholder}` replacement)
- **Automatic JSON extraction** from markdown code blocks
- **Comprehensive metrics**: Token usage, timing, and performance data
- **Flexible LLM configuration**: Supports any OpenAI-compatible API

### Comprehensive Error Handling

- Detailed error types (not_connected, tool_not_found, etc.)
- Contextual error messages
- Actionable suggestions for resolution
- Full error metadata for debugging

### Verbose Output

- Connection statistics (tools called, resources accessed, etc.)
- Request timing information
- Server capabilities and metadata
- Execution duration tracking

## Requirements

- Python 3.11 or higher
- FastMCP v2.12.4+
- Pydantic v2.12.0+
- python-dotenv v1.0.0+ (for .env file support)
- httpx v0.27.0+ (for LLM API calls)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/example/mcp-test-mcp
cd mcp-test-mcp

# Create and activate virtual environment (REQUIRED)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Using pip

```bash
# Create virtual environment first (REQUIRED)
python -m venv venv
source venv/bin/activate

# Install the package
pip install mcp-test-mcp
```

### Using uv (Recommended for Quick Setup)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and runner. With the project on GitHub, you can run mcp-test-mcp directly without cloning:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on macOS: brew install uv

# Run the server directly from GitHub (no clone needed!)
uvx --from git+https://github.com/rdwj/mcp-test-mcp mcp-test-mcp

# Or run from a local clone
git clone https://github.com/rdwj/mcp-test-mcp
cd mcp-test-mcp
uv run mcp-test-mcp

# Install globally with uv for use in Claude Code
uv tool install git+https://github.com/rdwj/mcp-test-mcp
```

#### Claude Code Configuration with uv

You have several options for configuring mcp-test-mcp with uv in Claude Code/Desktop:

**Option 1: Run from GitHub (recommended - no clone needed!)**

*Basic configuration (most users):*
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

*With LLM integration (optional):*
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/rdwj/mcp-test-mcp", "mcp-test-mcp"],
      "env": {
        "LLM_URL": "https://your-llm-endpoint.com/v1",
        "LLM_MODEL_NAME": "your-model-name",
        "LLM_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Option 2: Run from local clone**

*Basic configuration:*
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-test-mcp", "mcp-test-mcp"]
    }
  }
}
```

*With LLM integration (optional):*
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-test-mcp", "mcp-test-mcp"],
      "env": {
        "LLM_URL": "https://your-llm-endpoint.com/v1",
        "LLM_MODEL_NAME": "your-model-name",
        "LLM_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Option 3: Global install with uv tool**

*Basic configuration:*
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "mcp-test-mcp"
    }
  }
}
```

*With LLM integration (optional):*
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "mcp-test-mcp",
      "env": {
        "LLM_URL": "https://your-llm-endpoint.com/v1",
        "LLM_MODEL_NAME": "your-model-name",
        "LLM_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Note about LLM configuration:** The `env` section is **completely optional**. The server and all testing tools work without it. LLM configuration is only required if you want to use the `execute_prompt_with_llm` tool for end-to-end prompt testing. All other tools (connect, list_tools, call_tool, list_resources, list_prompts, etc.) work without any LLM configuration.

## Configuration

### Claude Code Configuration

Add mcp-test-mcp to your Claude Code MCP settings (typically in `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

**Using standard Python (pip install)**

*Basic configuration:*
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

*With LLM integration (optional):*
```json
{
  "mcpServers": {
    "mcp-test-mcp": {
      "command": "python",
      "args": ["-m", "mcp_test_mcp"],
      "env": {
        "LLM_URL": "https://your-llm-endpoint.com/v1",
        "LLM_MODEL_NAME": "your-model-name",
        "LLM_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Using uv (recommended)**

See the "Using uv" section above for multiple configuration options.

After adding this configuration, restart Claude Code/Desktop for the changes to take effect.

### Claude Desktop Configuration

The configuration is identical for Claude Desktop - add the same JSON to your MCP settings file.

### LLM Integration Configuration

To use the `execute_prompt_with_llm` tool, create a `.env` file in the project root:

```bash
# .env file
LLM_URL=https://your-llm-endpoint.com/v1
LLM_MODEL_NAME=your-model-name
LLM_API_KEY=your-api-key
```

The tool supports any OpenAI-compatible API endpoint (including OpenAI, Azure OpenAI, local models via vLLM/Ollama, and enterprise endpoints).

## Quick Start

Once configured, you can immediately start testing MCP servers through natural conversation with Claude:

### 1. Connect to a Server

**User:** "Connect to my local MCP server at /path/to/server"

**Claude will:** Use the `connect_to_server` tool and show you:

- Connection success/failure
- Transport type (stdio or streamable-http)
- Server information (name, version, capabilities)
- Connection timing

### 2. Discover Tools

**User:** "What tools does it have?"

**Claude will:** Use the `list_tools` tool and show you:

- All available tools by name
- Complete descriptions
- Full input schemas for each tool

### 3. Test a Tool

**User:** "Test the echo tool with the message 'Hello MCP'"

**Claude will:** Use the `call_tool` tool and show you:

- Tool execution result
- Execution time
- Success/failure status
- Updated statistics

### 4. Check Status

**User:** "What's the connection status?"

**Claude will:** Use the `get_connection_status` tool and show you:

- Current server URL
- Connection duration
- Statistics (tools called, resources accessed, errors)

### 5. Test with LLM *(NEW!)*

**User:** "Execute the weather_report prompt with that data using an LLM"

**Claude will:** Use the `execute_prompt_with_llm` tool and show you:

- Prompt retrieval and variable substitution
- LLM request and response
- Auto-parsed JSON (if applicable)
- Token usage and timing metrics

### 6. Disconnect

**User:** "Disconnect from the server"

**Claude will:** Use the `disconnect` tool and confirm disconnection with final statistics.

## Available Tools

mcp-test-mcp provides **14 tools** organized into functional categories:

### Connection Management (3 tools)

- **connect_to_server**: Establish connection to target MCP server
  - Supports stdio (file paths) and streamable-http (URLs)
  - Returns connection state and server capabilities
- **disconnect**: Close active connection cleanly
  - Returns final statistics
- **get_connection_status**: Check current connection state
  - Shows connection duration and usage statistics

### Tool Testing (2 tools)

- **list_tools**: Discover all tools with complete schemas
  - Returns tool names, descriptions, and input schemas
- **call_tool**: Execute a tool with specified arguments
  - Returns execution results and timing
  - Tracks tool usage statistics

### Resource Testing (2 tools)

- **list_resources**: Discover all resources with metadata
  - Returns URIs, names, descriptions, and MIME types
- **read_resource**: Read resource content by URI
  - Supports text and binary content
  - Returns content with size and timing

### Prompt Testing (2 tools)

- **list_prompts**: Discover all prompts with argument schemas
  - Returns prompt names, descriptions, and required arguments
- **get_prompt**: Get rendered prompt with arguments
  - Returns full message structures
  - Tracks prompt usage statistics

### **LLM Integration (1 tool)** *(NEW!)*

- **execute_prompt_with_llm**: Complete end-to-end prompt testing with LLM
  - Retrieves prompts from connected MCP server
  - Supports both standard MCP prompts and template variable filling
  - Executes prompts with actual LLM inference
  - Returns structured responses with timing and token usage
  - Auto-extracts JSON from markdown code blocks
  - See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed examples

### Utility Tools (4 tools)

- **health_check**: Verify server is running
- **ping**: Test basic connectivity (returns "pong")
- **echo**: Echo a message back
- **add**: Add two numbers (for testing basic tool calls)

## Common Workflows

### Testing a New MCP Server

```text
1. Connect → check connection status
2. List tools → understand available functionality
3. Call each tool → verify behavior
4. List resources → check resource capabilities
5. Read resources → verify content
6. List prompts → check prompt templates
7. Get prompts → verify rendering
8. Execute prompts with LLM → test end-to-end (NEW!)
9. Disconnect → clean shutdown
```

### End-to-End LLM Testing *(NEW!)*

```text
1. Connect to MCP server
2. Call a tool to get data (e.g., get_weather)
3. Execute a prompt with the data using execute_prompt_with_llm
4. Verify LLM generates expected output format
5. Check token usage and performance metrics
```

### Debugging Connection Issues

```text
1. Try connecting with verbose output
2. Check error messages for specific issues
3. Verify transport type (stdio vs HTTP)
4. Check server logs for additional context
5. Use health_check and ping for basic connectivity
```

### Verifying Tool Schemas

```text
1. Connect to server
2. List tools to get full schemas
3. Compare with expected schemas
4. Test edge cases with various arguments
5. Verify error handling with invalid inputs
```

## Environment Variables

Configure behavior through environment variables:

### Core Configuration

- **MCP_TEST_LOG_LEVEL**: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Default: INFO
  - Example: `export MCP_TEST_LOG_LEVEL=DEBUG`
- **MCP_TEST_CONNECT_TIMEOUT**: Connection timeout in seconds
  - Default: 30.0
  - Example: `export MCP_TEST_CONNECT_TIMEOUT=60.0`

### LLM Integration *(Required for execute_prompt_with_llm)*

- **LLM_URL**: LLM API endpoint URL
  - Example: `https://api.openai.com/v1`
  - Supports any OpenAI-compatible API
- **LLM_MODEL_NAME**: Model name to use
  - Example: `gpt-4` or `llama-4-scout-17b`
- **LLM_API_KEY**: API key for authentication
  - Keep this secure, never commit to version control

These can be set in a `.env` file in the project root, which is automatically loaded by the server.

## Documentation

For detailed usage examples, troubleshooting, and advanced scenarios, see:

- **[Testing Guide](TESTING_GUIDE.md)** - Complete guide with LLM integration examples
- **[Project Management](project-management/PROJECT-MANAGEMENT-RULES.md)** - Development workflow and contribution process

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=mcp_test_mcp --cov-report=html

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### Project Structure

```
mcp-test-mcp/
├── src/
│   └── mcp_test_mcp/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # CLI entry point
│       ├── server.py            # FastMCP server instance
│       ├── connection.py        # ConnectionManager
│       └── tools/               # Tool implementations
│           ├── connection.py    # Connection management tools
│           ├── tools.py         # Tool testing tools
│           ├── resources.py     # Resource testing tools
│           ├── prompts.py       # Prompt testing tools
│           └── llm.py           # LLM integration (NEW!)
├── tests/                       # Test suite
├── fastmcp-client-docs/         # FastMCP client documentation
├── fastmcp-server-docs/         # FastMCP server documentation
├── project-management/          # Project workflow files
├── TESTING_GUIDE.md             # Comprehensive testing guide
├── pyproject.toml               # Project configuration
├── .env                         # Environment variables (create this)
├── README.md                    # This file
└── LICENSE                      # MIT License
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=mcp_test_mcp --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=mcp_test_mcp --cov-report=html

# Run specific test file
pytest tests/test_connection.py -v
```

### Code Quality

This project maintains high code quality standards:

- **pytest**: Testing framework with async support (80%+ coverage target)
- **black**: Code formatting (line length: 100)
- **ruff**: Fast Python linter
- **mypy**: Static type checking with strict mode

All tools are configured in `pyproject.toml`.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Set up your development environment** with `pip install -e ".[dev]"`
3. **Write tests** for new functionality (maintain 80%+ coverage)
4. **Follow code style**: Use black for formatting, pass ruff and mypy checks
5. **Update documentation** for user-facing changes
6. **Submit a pull request** with a clear description of changes

### Development Standards

- All code must have type hints
- Tests required for new features and bug fixes
- Documentation updates for API changes
- Follow existing patterns in the codebase
- Use structured logging (JSON format)

## Testing Principles

The project follows Test-Driven Development (TDD):

- 80%+ code coverage requirement
- Test both happy paths and error cases
- Use descriptive test names
- Include integration tests for MCP server interactions
- Test timeout and error handling scenarios

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- Wes Jackson

## Acknowledgments

- [FastMCP](https://gofastmcp.com/) team for the excellent FastMCP framework
- Model Context Protocol specification contributors
- Open source community

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Python Packaging Guide](https://packaging.python.org/)

## Support

For issues, questions, or contributions:

- **Issues**: Report bugs and request features through GitHub Issues
- **Discussions**: Join community discussions for questions and ideas
- **Documentation**: Check docs/ directory for detailed guides

---

**Ready to start testing?** Configure Claude Code with mcp-test-mcp and start exploring your MCP servers through natural conversation!

# MCP Test Client - Complete Testing Guide

This guide covers how to use `mcp-test-mcp` to comprehensively test MCP servers, including tools, resources, prompts, and end-to-end LLM integration.

## Overview

`mcp-test-mcp` is a FastMCP-based MCP server that provides tools for testing other MCP servers. It can test all MCP capabilities:

- **Tools**: List and execute tools
- **Resources**: List and read resources
- **Prompts**: List, retrieve, and execute prompts with an LLM
- **LLM Integration**: End-to-end prompt testing with actual LLM execution

## Quick Start

### 1. Installation

```bash
# Install in development mode
pip install -e .

# Set up environment variables for LLM testing
cp .env.example .env
# Edit .env and add your LLM credentials
```

### 2. Basic Connection

```python
from mcp_test_mcp.connection import ConnectionManager

# Connect to a target MCP server
await ConnectionManager.connect("https://your-mcp-server.com/mcp/")
```

### 3. Test Tools

```python
from mcp_test_mcp.tools.tools import list_tools, call_tool

# List available tools
tools = await list_tools()

# Execute a tool
result = await call_tool("get_weather", {"location": "Boston, MA"})
```

## Available Test Tools

### Connection Management

#### `connect_to_server(url: str)`
Establishes connection to a target MCP server.

**Parameters:**
- `url`: Server URL (HTTP/HTTPS) or file path (stdio)

**Returns:**
- Connection details and server information

**Example:**
```python
result = await connect_to_server(
    "https://weather-mcp.example.com/mcp/"
)
```

#### `disconnect()`
Closes the current connection.

#### `get_connection_status()`
Returns current connection state and statistics.

### Tool Testing

#### `list_tools()`
Lists all tools exposed by the connected server.

**Returns:**
- List of tools with names, descriptions, and input schemas

#### `call_tool(name: str, arguments: dict)`
Executes a tool on the connected server.

**Parameters:**
- `name`: Tool name
- `arguments`: Tool arguments as dictionary

**Returns:**
- Tool execution result with timing metadata

**Example:**
```python
result = await call_tool(
    "get_weather",
    {"location": "Seattle, WA"}
)
```

### Resource Testing

#### `list_resources()`
Lists all resources exposed by the connected server.

**Returns:**
- List of resources with URIs, names, descriptions, and MIME types

#### `read_resource(uri: str)`
Reads a resource from the connected server.

**Parameters:**
- `uri`: Resource URI (e.g., `citations://all`)

**Returns:**
- Resource content with MIME type and size

**Example:**
```python
result = await read_resource("citations://all")
content = result["resource"]["content"]
```

### Prompt Testing

#### `list_prompts()`
Lists all prompts exposed by the connected server.

**Returns:**
- List of prompts with names, descriptions, and argument schemas

#### `get_prompt(name: str, arguments: dict)`
Retrieves a rendered prompt from the server.

**Parameters:**
- `name`: Prompt name
- `arguments`: Prompt arguments

**Returns:**
- Rendered prompt messages ready for LLM consumption

**Example:**
```python
result = await get_prompt(
    "weather_report",
    {}
)
messages = result["prompt"]["messages"]
```

### LLM Integration

#### `execute_prompt_with_llm(prompt_name, prompt_arguments, fill_variables, llm_config)`
Complete end-to-end prompt testing with LLM execution.

**Supports Two Patterns:**

##### Pattern 1: Standard MCP Prompts
For prompts that accept arguments via the MCP protocol.

```python
result = await execute_prompt_with_llm(
    prompt_name="user_greeting",
    prompt_arguments={
        "name": "Alice",
        "role": "administrator"
    }
)
```

##### Pattern 2: Template Variable Filling
For prompts with `{variable}` placeholders that need manual filling.

```python
result = await execute_prompt_with_llm(
    prompt_name="weather_report",
    prompt_arguments={},  # No MCP arguments
    fill_variables={
        "weather_data": {
            "location": "Boston, MA",
            "temperature": "48.2°F"
        },
        "output_format": "JSON"
    }
)
```

**Parameters:**
- `prompt_name` (required): Prompt to execute
- `prompt_arguments` (optional): MCP prompt arguments, default `{}`
- `fill_variables` (optional): Template variables for `{placeholder}` replacement
- `llm_config` (optional): LLM configuration (defaults to environment variables)

**LLM Configuration:**
- `url`: LLM endpoint (default: `LLM_URL` env var)
- `model`: Model name (default: `LLM_MODEL_NAME` env var)
- `api_key`: API key (default: `LLM_API_KEY` env var)
- `max_tokens`: Max response tokens (default: 1000)
- `temperature`: Sampling temperature (default: 0.7)

**Returns:**
- `success`: Boolean indicating success
- `prompt`: Original prompt information
- `llm_request`: Request sent to LLM
- `llm_response`: LLM response with usage stats
- `parsed_response`: Auto-parsed JSON (if response is JSON)
- `metadata`: Detailed timing information

**Features:**
- Automatically extracts JSON from markdown code blocks
- JSON-serializes non-string fill_variables
- Comprehensive error handling
- Detailed performance metrics

## Complete Testing Workflow

### Example: Testing a Weather MCP Server

```python
import asyncio
from mcp_test_mcp.connection import ConnectionManager
from mcp_test_mcp.tools.tools import list_tools, call_tool
from mcp_test_mcp.tools.resources import list_resources, read_resource
from mcp_test_mcp.tools.prompts import list_prompts
from mcp_test_mcp.tools.llm import execute_prompt_with_llm

async def test_weather_server():
    # 1. Connect
    await ConnectionManager.connect(
        "https://weather-mcp.example.com/mcp/"
    )

    # 2. Test Tools
    print("Testing tools...")
    tools = await list_tools()
    print(f"Found {len(tools['tools'])} tools")

    weather_result = await call_tool(
        "get_weather",
        {"location": "Boston, MA"}
    )
    print(f"Weather: {weather_result['tool_call']['result']}")

    # 3. Test Resources
    print("\nTesting resources...")
    resources = await list_resources()
    print(f"Found {len(resources['resources'])} resources")

    citation = await read_resource("citations://all")
    print(f"Citation content: {len(citation['resource']['content'])} bytes")

    # 4. Test Prompts
    print("\nTesting prompts...")
    prompts = await list_prompts()
    print(f"Found {len(prompts['prompts'])} prompts")

    # 5. Test with LLM
    print("\nTesting prompt with LLM...")
    weather_data = json.loads(weather_result['tool_call']['result'])

    llm_result = await execute_prompt_with_llm(
        prompt_name="weather_report",
        fill_variables={
            "weather_data": weather_data,
            "output_format": "JSON"
        }
    )

    if llm_result["success"]:
        print("✓ LLM generated weather report")
        if llm_result["parsed_response"]:
            print(f"  Response has {len(llm_result['parsed_response'])} fields")

    # 6. Disconnect
    await ConnectionManager.disconnect()

# Run the test
asyncio.run(test_weather_server())
```

## Test Scripts

The repository includes example test scripts:

### `test_prompt_with_llm.py`
Demonstrates manual prompt filling and LLM execution.

```bash
python3 test_prompt_with_llm.py
```

### `test_both_prompt_patterns.py`
Shows both standard MCP and template variable patterns.

```bash
python3 test_both_prompt_patterns.py
```

## Environment Variables

### Required for LLM Testing

```bash
# .env file
LLM_URL=https://your-llm-endpoint.com/v1
LLM_MODEL_NAME=your-model-name
LLM_API_KEY=your-api-key
```

### Optional Configuration

```bash
# Connection timeout (seconds)
MCP_TEST_CONNECT_TIMEOUT=30

# Request timeout (seconds)
MCP_TEST_REQUEST_TIMEOUT=60

# Log level
MCP_TEST_LOG_LEVEL=INFO
```

## Using with Claude Code

`mcp-test-mcp` is designed to work seamlessly with Claude Code:

1. Claude Code automatically exposes the tools as `mcp__mcp-test-mcp__*`
2. Use these tools interactively to test MCP servers
3. All tools include comprehensive error messages and suggestions

Example:
```
User: Connect to the weather MCP and test its tools
Claude: I'll use mcp__mcp-test-mcp__connect_to_server to connect...
```

## Testing Checklist

When testing an MCP server comprehensively:

- [ ] Connection
  - [ ] Successfully connects with correct URL
  - [ ] Returns server information
  - [ ] Handles connection errors gracefully

- [ ] Tools
  - [ ] Lists all available tools
  - [ ] Tool descriptions are clear
  - [ ] Input schemas are complete
  - [ ] Tools execute successfully
  - [ ] Error handling works correctly

- [ ] Resources
  - [ ] Lists all available resources
  - [ ] Resource URIs are correct
  - [ ] Resources return expected content
  - [ ] MIME types are accurate

- [ ] Prompts
  - [ ] Lists all available prompts
  - [ ] Prompt arguments are documented
  - [ ] Prompts render correctly
  - [ ] LLM execution produces valid output
  - [ ] Response format matches expectations

## Troubleshooting

### Connection Issues

**Error: Connection timeout**
```python
# Increase timeout
os.environ["MCP_TEST_CONNECT_TIMEOUT"] = "60"
```

**Error: Invalid URL**
- Ensure URL includes `/mcp/` path
- Check for trailing slash requirements
- Verify HTTPS certificate

### Tool Execution Issues

**Error: Tool not found**
- Use `list_tools()` to see available tools
- Check tool name spelling

**Error: Invalid arguments**
- Use `list_tools()` to see input schema
- Verify argument types match schema

### LLM Integration Issues

**Error: Missing LLM configuration**
- Set `LLM_URL`, `LLM_MODEL_NAME`, `LLM_API_KEY` in `.env`
- Or pass `llm_config` parameter

**Error: LLM request failed**
- Verify API endpoint is accessible
- Check API key validity
- Confirm model name is correct

### Resource Reading Issues

**Error: Resource returns null content**
- Ensure you're using the FastMCP client (automatically handled)
- Check resource URI is correct
- Verify server implements resources correctly

## Architecture

### Design Principles

1. **Comprehensive**: Tests all MCP capabilities
2. **Flexible**: Works with any MCP server
3. **Informative**: Detailed error messages and timing
4. **Reusable**: Clean API for programmatic use
5. **Interactive**: Works well with Claude Code

### Key Components

- **Connection Manager**: Global connection state management
- **Tool Testing**: Tool discovery and execution
- **Resource Testing**: Resource listing and reading
- **Prompt Testing**: Prompt retrieval and rendering
- **LLM Integration**: End-to-end prompt execution

### Transport Support

- **HTTP/HTTPS**: `streamable-http` transport
- **STDIO**: Local command-line servers
- **SSE**: Legacy SSE transport (deprecated)

## Contributing

See project management workflow in `project-management/PROJECT-MANAGEMENT-RULES.md`.

## Known Issues

- **CLI Entry Point**: `mcp-test-mcp` CLI command requires fix (see `project-management/backlog/fix-main-entry-point.md`)
- Works perfectly as an MCP server integrated with Claude Code

## License

MIT

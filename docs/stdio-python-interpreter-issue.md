# Stdio Transport: Python Interpreter Issue

## Problem Summary

When connecting to MCP servers via stdio using a `.py` file path, `mcp-test-mcp` uses the Python interpreter running mcp-test-mcp itself (`sys.executable`), not the interpreter specified in the script's shebang or the server's virtual environment.

This causes connection failures when the target MCP server has dependencies not installed in mcp-test-mcp's Python environment.

## Current Behavior

The `PythonStdioTransport` in FastMCP (used by mcp-test-mcp) runs:

```python
# In fastmcp/client/transports.py
super().__init__(
    command=python_cmd,  # defaults to sys.executable
    args=[str(script_path)],
    ...
)
```

This means:
1. **Shebang lines are ignored** - `#!/path/to/venv/bin/python` has no effect
2. **Entry points without `.py` extension fail** - e.g., `venv/bin/my-mcp-server` returns "Unsupported script type"
3. **Virtual environment isolation is broken** - server's dependencies must be in mcp-test-mcp's environment

## Reproduction Steps

```bash
# Create a simple MCP server with dependencies
mkdir test-server && cd test-server
python -m venv venv
source venv/bin/activate
pip install fastmcp pydantic

# Create server.py
cat > server.py << 'PYEOF'
#!/path/to/test-server/venv/bin/python
from fastmcp import FastMCP
mcp = FastMCP("test")

@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
PYEOF

# Try to connect via mcp-test-mcp
# Result: "Connection closed" because fastmcp isn't in mcp-test-mcp's Python
```

## Workaround

Run the MCP server with HTTP/SSE transport instead:

```python
# Server side
mcp.run(transport='sse', host='127.0.0.1', port=8765)
```

```
# Connect via mcp-test-mcp
connect_to_server("http://127.0.0.1:8765/sse")
```

## Proposed Solutions

### Option 1: Add `python_executable` Parameter (Minimal Change)

Add an optional parameter to `connect_to_server` for stdio connections:

```python
@mcp.tool
async def connect_to_server(
    url: Annotated[str, "Server URL or file path"],
    python_executable: Annotated[str | None, "Python interpreter for .py files"] = None,
    ctx: Context
) -> dict[str, Any]:
    ...
```

When connecting to a `.py` file with `python_executable` specified, pass it to `PythonStdioTransport`.

### Option 2: Support Entry Point Scripts (Better UX)

Recognize pip-installed entry points (scripts without `.py` extension) and run them directly:

```python
def infer_transport(transport: str | Path) -> ClientTransport:
    path = Path(transport)
    
    if path.suffix == ".py":
        return PythonStdioTransport(path, python_cmd=python_executable or sys.executable)
    elif path.suffix == ".js":
        return NodeStdioTransport(path)
    elif path.exists() and os.access(path, os.X_OK):
        # Executable file without extension - run directly (uses shebang)
        return StdioTransport(command=str(path), args=[])
    else:
        raise ValueError(f"Unsupported script type: {transport}")
```

### Option 3: Support Config Dict Format (Most Flexible)

Allow passing a configuration dict instead of just a URL string:

```python
connect_to_server({
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "env": {"VIRTUAL_ENV": "/path/to/venv"},
    "cwd": "/path/to/project"
})

# Or for venv-based servers:
connect_to_server({
    "script": "/path/to/server.py",
    "python": "/path/to/venv/bin/python"
})
```

## Recommendation

**Implement Option 2** as the default behavior change (low risk, high value), and **Option 1** as an escape hatch for edge cases.

Option 2 would allow:
```
connect_to_server("/path/to/venv/bin/my-mcp-server")  # Just works
```

This matches user expectations - if a script is executable, run it directly and let the OS handle the shebang.

## Impact

- Users testing MCP servers in isolated virtual environments
- Users testing pip-installed MCP server packages
- Any stdio-based MCP server with dependencies not in mcp-test-mcp's environment

## Related Files

- `src/mcp_test_mcp/connection.py` - `ConnectionManager.connect()` 
- FastMCP: `fastmcp/client/transports.py` - `infer_transport()`, `PythonStdioTransport`

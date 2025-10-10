# Connection Model - How This Works

## Key Insight from User

> "mcp-test-mcp will work the same way these other ones do, so the way you see it will be similar."

## How MCP Servers Work for AI Assistants

When an MCP server is configured for Claude Code/Desktop:

1. **User configures server** (outside of Claude's view)
   - Adds to Claude's MCP configuration
   - Provides connection details (URL, transport, auth, etc.)
   - Server starts/connects

2. **Claude receives tools**
   - Tools appear with prefix (e.g., `mcp__context7__resolve-library-id`)
   - Full schemas are available
   - Can call tools directly
   - **Cannot introspect the server itself** (this is the gap)

3. **AI uses tools**
   - Calls tools by name
   - Provides arguments
   - Gets results

## How mcp-test-mcp Will Work

**Same pattern:**

1. **User configures mcp-test-mcp** (just like any MCP server)
   - Runs locally via stdio OR deployed remotely
   - Added to Claude's MCP server list
   - Tools become available with `mcp__mcp_test_mcp__` prefix

2. **Claude receives mcp-test-mcp tools**
   - `mcp__mcp_test_mcp__connect_to_server`
   - `mcp__mcp_test_mcp__list_tools`
   - `mcp__mcp_test_mcp__call_tool`
   - etc.

3. **AI uses these tools to test other servers**
   - Calls `connect_to_server("https://my-server.com/mcp")`
   - Calls `list_tools()` to introspect
   - Calls `call_tool("add", {"a": 5, "b": 3})` to test
   - Gets verbose results to verify

## Connection State Management

Since mcp-test-mcp tools will be called like any other MCP tool, connection state needs to be managed **within the mcp-test-mcp server process**.

**Two approaches:**

### Option A: Simple Global State
```python
# mcp-test-mcp maintains one active connection at a time
current_connection = None

@mcp.tool
def connect_to_server(url: str):
    global current_connection
    current_connection = Client(url)
    # ... connect ...
    return {"connected": True, "server": url}

@mcp.tool
def list_tools():
    if not current_connection:
        return {"error": "Not connected to any server"}
    tools = current_connection.list_tools()
    return {"tools": tools, ...}
```

**Pros:**
- Simple for AI to use (no passing connection objects)
- Matches mental model (connect once, then operate)

**Cons:**
- Can only test one server at a time
- Need to disconnect/reconnect to switch servers

### Option B: Named Connections
```python
# mcp-test-mcp maintains multiple named connections
connections = {}
active_connection = None

@mcp.tool
def connect_to_server(url: str, name: str = None):
    name = name or url
    connections[name] = Client(url)
    # ... connect ...
    active_connection = name
    return {"connected": True, "name": name, "server": url}

@mcp.tool
def list_tools(connection: str = None):
    conn_name = connection or active_connection
    if conn_name not in connections:
        return {"error": f"No connection named {conn_name}"}
    tools = connections[conn_name].list_tools()
    return {"tools": tools, ...}
```

**Pros:**
- Can test multiple servers
- Switch between connections
- More flexible

**Cons:**
- More complex API
- AI needs to track connection names
- More potential for errors

## Recommendation

**Start with Option A (Simple Global State)**

Reasons:
1. Simpler mental model for AI
2. Primary use case is testing ONE deployed server at a time
3. Can always add Option B later if needed
4. Reduces API surface area (fewer parameters)

**Typical workflow:**
```
1. connect_to_server("https://my-server.com/mcp")
2. list_tools()  # Uses current connection
3. call_tool("add", {"a": 5, "b": 3})  # Uses current connection
4. disconnect()
5. connect_to_server("https://other-server.com/mcp")  # New connection
6. list_tools()  # Uses new connection
```

## What the AI Sees

When mcp-test-mcp is configured, Claude will see tools like:

```
mcp__mcp_test_mcp__connect_to_server(url: str) -> dict
mcp__mcp_test_mcp__disconnect() -> dict
mcp__mcp_test_mcp__list_tools() -> dict
mcp__mcp_test_mcp__call_tool(name: str, arguments: dict) -> dict
mcp__mcp_test_mcp__list_resources() -> dict
mcp__mcp_test_mcp__read_resource(uri: str) -> dict
mcp__mcp_test_mcp__list_prompts() -> dict
mcp__mcp_test_mcp__get_prompt(name: str, arguments: dict) -> dict
mcp__mcp_test_mcp__get_connection_status() -> dict
```

Just like how I currently see:
```
mcp__context7__resolve-library-id(libraryName: str)
mcp__context7__get-library-docs(context7CompatibleLibraryID: str, ...)
```

## Why This Matters

**User experience:**
```
User: "Test my server at https://my-server.apps.openshift.com/mcp"

Claude: [calls mcp__mcp_test_mcp__connect_to_server(...)]
        "Connected! Let me check what tools are available..."

        [calls mcp__mcp_test_mcp__list_tools()]
        "I found 3 tools:
        1. add - Adds two numbers
           - Required: a (number), b (number)
           - Returns: number
        ..."

User: "Test the add tool"

Claude: [calls mcp__mcp_test_mcp__call_tool("add", {"a": 5, "b": 3})]
        "The add tool works! Called add(5, 3) and got result: 8
        Execution time: 142ms"
```

Clean, natural workflow - just like using any other MCP tool.

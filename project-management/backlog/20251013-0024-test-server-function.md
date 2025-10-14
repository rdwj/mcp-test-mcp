---
story_id: "0024"
title: "Add test_server convenience function for comprehensive testing"
created: "2025-10-13"
status: "backlog"
dependencies: []
estimated_complexity: "medium"
tags: ["testing", "usability", "phase2"]
---

# Story 0024: Add test_server convenience function

## Description

Add a single convenience function that comprehensively tests an MCP server by connecting, discovering all capabilities, and optionally testing basic functionality. This reduces the number of manual steps needed to validate a server and provides a quick health check.

## User Feedback Context

From Claude Desktop user testing:
> "No Direct 'Test Everything' Function - A convenience function like test_server that automatically lists all capabilities and runs a simple test of each would be handy for quick validation."

## Acceptance Criteria

- [ ] New `test_server()` tool function
- [ ] Accepts `url` parameter (server URL to test)
- [ ] Accepts optional `quick_test: bool = True` parameter
- [ ] When `quick_test=True`:
  - Connect to server
  - List all tools with schemas
  - List all resources
  - List all prompts
  - Return structured summary
- [ ] When `quick_test=False`:
  - All of the above, plus:
  - Attempt to call safe utility tools (ping, echo, health_check if available)
  - Test read access to resources (first resource only)
  - Test prompt rendering (first prompt only, with empty args if optional)
  - Report success/failure for each test
- [ ] Structured response format:
  ```python
  {
      "success": bool,
      "server_url": str,
      "connection": {...},
      "capabilities": {
          "tools": {"count": int, "names": [...]},
          "resources": {"count": int, "uris": [...]},
          "prompts": {"count": int, "names": [...]}
      },
      "tests": {...}  # Only if quick_test=False
  }
  ```
- [ ] Proper error handling if connection fails
- [ ] Clean disconnect after testing
- [ ] Documentation with examples
- [ ] Unit tests for both quick and full test modes

## Technical Notes

**Implementation approach:**

```python
@mcp.tool()
async def test_server(
    url: Annotated[str, "Server URL to test"],
    quick_test: Annotated[bool, "If True, only list capabilities. If False, test functionality"] = True,
    ctx: Context
) -> dict[str, Any]:
    """
    Comprehensive MCP server test: connect, discover capabilities, optionally test tools.

    This convenience function replaces the need to manually call:
    - connect_to_server
    - list_tools
    - list_resources
    - list_prompts
    - (optionally) call_tool, read_resource, get_prompt
    - disconnect

    Returns:
        Comprehensive test report with server capabilities and test results
    """
    start_time = time.perf_counter()
    results = {
        "success": False,
        "server_url": url,
        "connection": None,
        "capabilities": {},
        "tests": {} if not quick_test else None,
        "metadata": {}
    }

    try:
        # 1. Connect
        await ctx.info(f"Testing server at {url}")
        conn_result = await connect_to_server(url, ctx)
        results["connection"] = conn_result.get("connection")

        # 2. List capabilities
        tools_result = await list_tools(ctx)
        resources_result = await list_resources(ctx)
        prompts_result = await list_prompts(ctx)

        results["capabilities"] = {
            "tools": {
                "count": len(tools_result.get("tools", [])),
                "names": [t["name"] for t in tools_result.get("tools", [])]
            },
            "resources": {
                "count": len(resources_result.get("resources", [])),
                "uris": [r["uri"] for r in resources_result.get("resources", [])]
            },
            "prompts": {
                "count": len(prompts_result.get("prompts", [])),
                "names": [p["name"] for p in prompts_result.get("prompts", [])]
            }
        }

        # 3. Run tests if requested
        if not quick_test:
            results["tests"] = await _run_functionality_tests(ctx, results["capabilities"])

        results["success"] = True

    except Exception as e:
        results["error"] = str(e)
        await ctx.error(f"Server test failed: {str(e)}")

    finally:
        # Always disconnect
        await disconnect(ctx)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    results["metadata"]["total_time_ms"] = round(elapsed_ms, 2)

    return results


async def _run_functionality_tests(ctx: Context, capabilities: dict) -> dict:
    """Run basic functionality tests on server capabilities."""
    tests = {
        "tools": [],
        "resources": [],
        "prompts": []
    }

    # Test safe utility tools if available
    safe_tools = ["ping", "echo", "health_check", "add"]
    for tool_name in capabilities["tools"]["names"]:
        if tool_name in safe_tools:
            try:
                # Attempt to call with safe default args
                if tool_name == "add":
                    result = await call_tool(tool_name, {"a": 1, "b": 1}, ctx)
                elif tool_name == "echo":
                    result = await call_tool(tool_name, {"message": "test"}, ctx)
                else:
                    result = await call_tool(tool_name, {}, ctx)

                tests["tools"].append({
                    "name": tool_name,
                    "success": result.get("success", False),
                    "result": result.get("tool_call", {}).get("result")
                })
            except Exception as e:
                tests["tools"].append({
                    "name": tool_name,
                    "success": False,
                    "error": str(e)
                })

    # Test first resource if available
    if capabilities["resources"]["uris"]:
        first_uri = capabilities["resources"]["uris"][0]
        try:
            result = await read_resource(first_uri, ctx)
            tests["resources"].append({
                "uri": first_uri,
                "success": result.get("success", False)
            })
        except Exception as e:
            tests["resources"].append({
                "uri": first_uri,
                "success": False,
                "error": str(e)
            })

    # Test first prompt if available
    if capabilities["prompts"]["names"]:
        first_prompt = capabilities["prompts"]["names"][0]
        try:
            result = await get_prompt(first_prompt, {}, ctx)
            tests["prompts"].append({
                "name": first_prompt,
                "success": result.get("success", False)
            })
        except Exception as e:
            tests["prompts"].append({
                "name": first_prompt,
                "success": False,
                "error": str(e)
            })

    return tests
```

## Usage Examples

**Quick capability check:**
```python
# AI: "Test the server at http://localhost:8000"
result = await test_server("http://localhost:8000", quick_test=True)
# Returns: connection info + counts of tools/resources/prompts
```

**Full functionality test:**
```python
# AI: "Do a full test of the server including running tools"
result = await test_server("http://localhost:8000", quick_test=False)
# Returns: everything above + test results for each capability
```

## AI Directives

**IMPORTANT**: Mark checklist items as complete `[x]` as you finish them. Update the `status` field in frontmatter when moving between stages.

Be conservative with functionality tests - only test tools that are clearly safe (no side effects). For resources and prompts, test only the first one to avoid overwhelming the target server.

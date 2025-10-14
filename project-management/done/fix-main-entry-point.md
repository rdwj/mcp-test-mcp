---
status: done
created_date: 2025-10-14T02:40:43Z
updated_date: 2025-10-14T02:40:43Z
history:
  - status: done
    timestamp: 2025-10-14T02:40:43Z
---

# Fix __main__.py Entry Point

## Type
Bug Fix

## Priority
Medium

## Description
The `__main__.py` file does not export a `main()` function, but `pyproject.toml` line 44 expects `mcp_test_mcp.__main__:main` as the console script entry point.

## Current Behavior
When running `mcp-test-mcp` from the command line, the following error occurs:
```
ImportError: cannot import name 'main' from 'mcp_test_mcp.__main__'
```

## Expected Behavior
The `mcp-test-mcp` CLI command should start the FastMCP server successfully.

## Technical Details

### Current Code (`src/mcp_test_mcp/__main__.py`)
```python
from mcp_test_mcp.server import mcp

if __name__ == "__main__":
    # Uses stdio transport by default
    mcp.run()
```

### Required Fix
Export a `main()` function that can be called by the console script:
```python
from mcp_test_mcp.server import mcp

def main():
    """Entry point for mcp-test-mcp CLI."""
    mcp.run()

if __name__ == "__main__":
    main()
```

## Files to Modify
- `src/mcp_test_mcp/__main__.py` - Add `main()` function

## Acceptance Criteria
- [x] `main()` function is exported from `__main__.py`
- [x] Running `mcp-test-mcp` from CLI works without ImportError
- [x] Server starts correctly using stdio transport
- [x] Running `python -m mcp_test_mcp` still works

## Resolution Notes (2025-10-13)
Fixed as part of v0.1.3 release during Claude Desktop integration testing. Added proper `main()` function with type hints and docstring to `src/mcp_test_mcp/__main__.py`:

```python
def main() -> None:
    """Main entry point for the MCP server."""
    # Uses stdio transport by default
    mcp.run()
```

Verified working through npm wrapper (`npx -y mcp-test-mcp@0.1.5`) and direct Python execution.

## Impact
Low - This only affects the CLI entry point. The MCP server works fine when integrated with Claude Code or other MCP clients.

## Related Issues
None

## Created
2025-10-09

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
- [ ] `main()` function is exported from `__main__.py`
- [ ] Running `mcp-test-mcp` from CLI works without ImportError
- [ ] Server starts correctly using stdio transport
- [ ] Running `python -m mcp_test_mcp` still works

## Impact
Low - This only affects the CLI entry point. The MCP server works fine when integrated with Claude Code or other MCP clients.

## Related Issues
None

## Created
2025-10-09

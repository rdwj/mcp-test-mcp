# Project Management Workflow

This project uses a file-based project management system. **ALL work MUST follow this workflow.**

## Critical Rules for Claude Code

### Before Starting Any Work

1. Check `project-management/backlog/` for work items
2. When starting work on an item, you MUST run:
   ```bash
   ./project-management/scripts/promote.sh [filename] in-progress
   ```

### During Work

1. If you encounter a blocker, you MUST immediately run:
   ```bash
   ./project-management/scripts/promote.sh [filename] blocked
   ```
2. Add a note to the work item explaining what's blocking progress

### After Completing Work

1. When work is complete, you MUST run:
   ```bash
   ./project-management/scripts/promote.sh [filename] ready-for-review
   ```
2. **DO NOT consider a task complete until the file is in `ready-for-review/`**

### Workflow States

- `backlog/` - Identified work not yet started
- `in-progress/` - Currently working on
- `blocked/` - Cannot proceed due to dependencies or issues
- `ready-for-review/` - Complete, awaiting approval
- `done/` - Approved and completed

### State Transitions You Must Execute

- Starting work: `backlog` → `in-progress`
- Hit blocker: `in-progress` → `blocked`
- Complete work: `in-progress` → `ready-for-review`
- Unblocked: `blocked` → `in-progress`

### Finding Work Items

Before asking the user what to work on, check these locations:
1. `project-management/in-progress/` - Any items here need completion
2. `project-management/blocked/` - Check if you can now unblock any items
3. `project-management/backlog/` - New work to start

### Complete Documentation

Read `project-management/PROJECT-MANAGEMENT-RULES.md` for the full workflow specification.

## Reminder

**YOU MUST USE THE PROMOTION SCRIPT** at the appropriate points. The human is relying on you to manage file locations correctly. Forgetting to promote files breaks the workflow.

## MCP Server Development Best Practices

### CRITICAL: STDOUT vs STDERR

**NEVER write logs, debug output, or any non-protocol data to stdout when building MCP servers.**

MCP uses STDIO transport for JSON-RPC communication:
- **STDOUT** = JSON-RPC protocol messages ONLY
- **STDERR** = Logging, debugging, user messages

#### Why This Matters

Any output to stdout (print statements, logging to stdout, error messages) will corrupt the JSON-RPC protocol and cause Zod validation errors in Claude Desktop or other MCP clients.

#### Correct Logging Configuration

```python
import logging
import sys

# ALWAYS configure logging to use stderr
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(JsonFormatter())

root_logger = logging.getLogger()
root_logger.handlers.clear()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)
```

#### Common Mistakes to Avoid

❌ **DON'T DO THIS:**
```python
print("Server starting...")  # Goes to stdout!
logging.info("Server ready")  # If not configured, goes to stdout!
logger.info("Tool called")    # During module import, can go to stdout!
```

✅ **DO THIS INSTEAD:**
```python
# Configure logging to stderr first
setup_logging_to_stderr()

# Then use logging
logger = logging.getLogger(__name__)
logger.info("Server ready")  # Goes to stderr

# Or use FastMCP's context logging
async def my_tool(ctx: Context):
    await ctx.info("Tool called")  # Handles stderr automatically
```

#### Testing for Stdout Cleanliness

Always test your MCP server by checking stdout/stderr separately:

```bash
# Good output: stdout is empty or only JSON-RPC
(npx -y your-mcp-server > stdout.log 2> stderr.log &)
sleep 3
pkill -f "your-mcp-server"

# Check - stdout should be clean!
cat stdout.log  # Should be empty or only protocol JSON
cat stderr.log  # Logs should be here
```

### NPM Wrapper Architecture

This project uses an npm wrapper around Python FastMCP:

**Components:**
- `node-wrapper/index.js` - Node wrapper that spawns Python
- `node-wrapper/scripts/postinstall.js` - Creates venv and installs Python package
- `node-wrapper/python-src/` - Bundled Python source code

**How It Works:**
1. User runs `npx mcp-test-mcp`
2. Postinstall creates `.venv/` and installs Python package
3. `index.js` runs `.venv/bin/python -m mcp_test_mcp`
4. Python server communicates via stdio

**Publishing Updates:**
1. Update `pyproject.toml` version
2. Update `node-wrapper/package.json` version
3. Copy updated Python source to `node-wrapper/python-src/`:
   ```bash
   rm -rf node-wrapper/python-src/*
   cp -r src node-wrapper/python-src/
   cp pyproject.toml node-wrapper/python-src/
   cp README.md node-wrapper/python-src/
   ```
4. Build Python package: `python -m build`
5. Publish npm: `npm publish node-wrapper/ --otp=<code>`

**Why Virtual Environment?**
- Dependency isolation (no system Python pollution)
- Each package version has its own dependencies
- Works consistently across environments
- Proper for production npm packages wrapping Python

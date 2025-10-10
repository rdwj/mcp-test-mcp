# Tool Verbosity Example - What AI Should See

## Example: context7 resolve-library-id tool

This is what I (Claude) can see about the `mcp__context7__resolve-library-id` tool:

**Name:** `mcp__context7__resolve-library-id`

**Description:**
```
Resolves a package/product name to a Context7-compatible library ID and returns a list of matching libraries.

You MUST call this function before 'get-library-docs' to obtain a valid Context7-compatible library ID UNLESS the user explicitly provides a library ID in the format '/org/project' or '/org/project/version' in their query.

Selection Process:
1. Analyze the query to understand what library/package the user is looking for
2. Return the most relevant match based on:
   - Name similarity to the query (exact matches prioritized)
   - Description relevance to the query's intent
   - Documentation coverage (prioritize libraries with higher Code Snippet counts)
   - Trust score (consider libraries with scores of 7-10 more authoritative)

Response Format:
- Return the selected library ID in a clearly marked section
- Provide a brief explanation for why this library was chosen
- If multiple good matches exist, acknowledge this but proceed with the most relevant one
- If no good matches exist, clearly state this and suggest query refinements

For ambiguous queries, request clarification before proceeding with a best-guess match.
```

**Parameters:**
```json
{
  "type": "object",
  "properties": {
    "libraryName": {
      "type": "string",
      "description": "Library name to search for and retrieve a Context7-compatible library ID."
    }
  },
  "required": ["libraryName"]
}
```

**What This Shows Me:**
- Input: Takes a single string parameter `libraryName` (required)
- Output: Returns library IDs and matching information
- Purpose: Search for libraries and resolve to Context7 IDs
- Behavior: Detailed selection process and response format expectations

## This is the Verbosity We Want

When mcp-test-mcp returns tool information, it should provide:

1. **Full tool name** (including any prefixes)
2. **Complete description** (everything the server advertised)
3. **Input schema** (exact JSON schema with all properties, types, descriptions)
4. **Required vs optional parameters** (clearly marked)
5. **Output expectations** (if the server provides them)

## Why This Matters

**I can verify this is real** because:
- The description is detailed and specific
- The schema shows exact parameter requirements
- I can see it's actually configured (not hallucinated)
- I can explain to the user exactly what this tool does

**I can use it correctly** because:
- I know the parameter name (`libraryName`)
- I know it's required (not optional)
- I know it expects a string
- I know what it returns

## What mcp-test-mcp Should Return

When you call `list_tools()` on a test server, it should return this level of detail for EVERY tool:

```json
{
  "success": true,
  "connection": {
    "server": "context7",
    "transport": "configured",
    "connected_at": "2025-10-09T10:15:00Z"
  },
  "tools": [
    {
      "name": "resolve-library-id",
      "description": "Resolves a package/product name to a Context7-compatible library ID...",
      "input_schema": {
        "type": "object",
        "properties": {
          "libraryName": {
            "type": "string",
            "description": "Library name to search for..."
          }
        },
        "required": ["libraryName"]
      }
    },
    {
      "name": "get-library-docs",
      "description": "Fetches up-to-date documentation for a library...",
      "input_schema": { /* ... */ }
    }
  ],
  "metadata": {
    "total_tools": 2,
    "server_name": "context7",
    "retrieved_at": "2025-10-09T10:15:00Z"
  }
}
```

This way I can tell you:
> "I found 2 tools from the context7 server:
> 1. **resolve-library-id** - Resolves package names to Context7 library IDs
>    - Required: libraryName (string)
> 2. **get-library-docs** - Fetches documentation for libraries
>    - Required: context7CompatibleLibraryID (string)
>    - Optional: tokens (number), topic (string)
>
> Retrieved at 2025-10-09T10:15:00Z"

And you can verify I actually got this from the server, not made it up.

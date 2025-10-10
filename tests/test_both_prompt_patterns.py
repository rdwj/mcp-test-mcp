#!/usr/bin/env python3
"""Test script demonstrating both prompt patterns with execute_prompt_with_llm.

This script shows:
1. Standard MCP prompts: where arguments are passed to the server
2. Template variable filling: where {variables} are manually filled

Both patterns use the same execute_prompt_with_llm tool.
"""

import asyncio
import json
from mcp_test_mcp.connection import ConnectionManager
from mcp_test_mcp.tools.llm import execute_prompt_with_llm


async def test_template_variable_pattern():
    """Test prompts with template variables that need manual filling."""
    print("=" * 80)
    print("TEST 1: Template Variable Pattern")
    print("=" * 80)
    print()

    # Connect to weather MCP server
    await ConnectionManager.connect(
        "https://mcp-server-weather-mcp.apps.cluster-sdzgj.sdzgj.sandbox319.opentlc.com/mcp/"
    )

    # Get weather data first (this would be from a tool call in real usage)
    weather_data = {
        "location": "Boston, MA",
        "temperature": "48.2°F (9.0°C)",
        "conditions": "Clear",
        "forecast": "Clear, with a low around 39. Northwest wind around 6 mph.",
        "humidity": "42.8%",
        "wind": "9.2 mph from 330°",
    }

    print("Weather data to use:")
    print(json.dumps(weather_data, indent=2))
    print()

    # Execute prompt with template variable filling
    print("Executing 'weather_report' prompt with fill_variables...")
    print()

    result = await execute_prompt_with_llm(
        prompt_name="weather_report",
        prompt_arguments={},  # No MCP arguments needed
        fill_variables={
            "weather_data": weather_data,  # Will be JSON-serialized
            "output_format": "JSON"  # Simple string
        },
    )

    if result["success"]:
        print("✓ Prompt executed successfully")
        print()
        print("LLM Response:")
        print("-" * 80)
        # Show first 500 chars
        response_text = result["llm_response"]["text"]
        if len(response_text) > 500:
            print(response_text[:500] + "...\n[truncated]")
        else:
            print(response_text)
        print("-" * 80)
        print()

        if result["parsed_response"]:
            print("✓ Successfully parsed JSON response")
            print(f"  Has 'summary': {'summary' in result['parsed_response']}")
            print(f"  Has 'temperature': {'temperature' in result['parsed_response']}")
            print(f"  Has 'recommendations': {'recommendations' in result['parsed_response']}")
        print()

        print("Metadata:")
        print(f"  Prompt retrieval: {result['metadata']['prompt_retrieval_ms']:.2f}ms")
        print(f"  LLM execution: {result['metadata']['llm_execution_ms']:.2f}ms")
        print(f"  Total time: {result['metadata']['total_time_ms']:.2f}ms")
    else:
        print(f"✗ Error: {result['error']['message']}")

    print()


async def test_standard_mcp_pattern():
    """Test standard MCP prompts with server-side argument substitution.

    Note: This would work if the weather MCP had prompts that accept arguments.
    For demonstration, we'll show what the call would look like.
    """
    print("=" * 80)
    print("TEST 2: Standard MCP Pattern (Demonstration)")
    print("=" * 80)
    print()

    print("For a prompt like 'user_greeting' that accepts 'name' and 'role':")
    print()
    print("  result = await execute_prompt_with_llm(")
    print("      prompt_name='user_greeting',")
    print("      prompt_arguments={")
    print("          'name': 'Alice',")
    print("          'role': 'administrator'")
    print("      }")
    print("  )")
    print()
    print("The MCP server handles variable substitution automatically.")
    print("No fill_variables needed!")
    print()


async def main():
    """Run both tests."""
    try:
        # Test 1: Template variable pattern (with actual execution)
        await test_template_variable_pattern()

        # Test 2: Standard MCP pattern (demonstration only)
        await test_standard_mcp_pattern()

        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("The execute_prompt_with_llm tool supports both patterns:")
        print()
        print("1. Standard MCP prompts:")
        print("   - Pass arguments via prompt_arguments")
        print("   - Server handles substitution")
        print("   - No fill_variables needed")
        print()
        print("2. Template variable prompts:")
        print("   - Pass variables via fill_variables")
        print("   - Client-side {variable} replacement")
        print("   - Works with any prompt that has {placeholders}")
        print()

    finally:
        # Cleanup
        await ConnectionManager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

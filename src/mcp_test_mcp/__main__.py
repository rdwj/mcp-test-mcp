"""
Entry point for running mcp-test-mcp as a module.

This module is executed when running:
    python -m mcp_test_mcp

or when using the installed console script:
    mcp-test-mcp

Supports multiple transports via CLI arguments and environment variables:
    - stdio (default): Standard input/output for Claude Desktop/Code integration
    - streamable-http: HTTP transport for web deployments
    - sse: Server-Sent Events (legacy, for backward compatibility)

Examples:
    mcp-test-mcp                                    # default: stdio
    mcp-test-mcp --transport stdio                  # explicit stdio
    mcp-test-mcp --transport streamable-http        # HTTP server
    mcp-test-mcp --transport streamable-http --host 0.0.0.0 --port 8080
    mcp-test-mcp --transport sse --port 9000        # legacy SSE

Environment Variables (CLI args take precedence):
    MCP_TEST_TRANSPORT: Transport type (stdio, streamable-http, sse)
    MCP_TEST_HOST: Host for HTTP transports (default: 127.0.0.1)
    MCP_TEST_PORT: Port for HTTP transports (default: 8000)
"""

import argparse
import os
import sys
from typing import Optional

# Valid transport types
VALID_TRANSPORTS = ("stdio", "streamable-http", "sse")

# Default values
DEFAULT_TRANSPORT = "stdio"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def get_config_value(
    cli_value: Optional[str],
    env_var: str,
    default: str,
) -> str:
    """Get configuration value with priority: CLI > env var > default.

    Args:
        cli_value: Value from command line argument (None if not provided)
        env_var: Environment variable name to check
        default: Default value if neither CLI nor env var is set

    Returns:
        The resolved configuration value
    """
    if cli_value is not None:
        return cli_value
    env_value = os.environ.get(env_var)
    if env_value is not None:
        return env_value
    return default


def get_port_value(
    cli_value: Optional[int],
    env_var: str,
    default: int,
) -> int:
    """Get port configuration with priority: CLI > env var > default.

    Args:
        cli_value: Value from command line argument (None if not provided)
        env_var: Environment variable name to check
        default: Default value if neither CLI nor env var is set

    Returns:
        The resolved port value
    """
    if cli_value is not None:
        return cli_value
    env_value = os.environ.get(env_var)
    if env_value is not None:
        try:
            return int(env_value)
        except ValueError:
            print(
                f"Warning: Invalid {env_var} value '{env_value}', using default {default}",
                file=sys.stderr,
            )
            return default
    return default


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="mcp-test-mcp",
        description="MCP testing server for testing other MCP servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  MCP_TEST_TRANSPORT    Transport type (stdio, streamable-http, sse)
  MCP_TEST_HOST         Host for HTTP transports (default: 127.0.0.1)
  MCP_TEST_PORT         Port for HTTP transports (default: 8000)

Priority: CLI arguments > environment variables > defaults

Examples:
  %(prog)s                                    # Use stdio transport (default)
  %(prog)s --transport streamable-http        # HTTP server on 127.0.0.1:8000
  %(prog)s --transport streamable-http --host 0.0.0.0 --port 8080
  %(prog)s --transport sse --port 9000        # Legacy SSE transport
""",
    )

    parser.add_argument(
        "--transport",
        "-t",
        choices=VALID_TRANSPORTS,
        default=None,
        help="Transport protocol to use (default: stdio, or MCP_TEST_TRANSPORT env var)",
    )

    parser.add_argument(
        "--host",
        "-H",
        default=None,
        help="Host to bind for HTTP transports (default: 127.0.0.1, or MCP_TEST_HOST env var)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=None,
        help="Port to bind for HTTP transports (default: 8000, or MCP_TEST_PORT env var)",
    )

    return parser.parse_args(args)


def resolve_config(args: argparse.Namespace) -> dict:
    """Resolve final configuration from CLI args and environment variables.

    Args:
        args: Parsed command line arguments

    Returns:
        Dictionary with resolved transport, host, and port values
    """
    transport = get_config_value(args.transport, "MCP_TEST_TRANSPORT", DEFAULT_TRANSPORT)

    # Validate transport
    if transport not in VALID_TRANSPORTS:
        valid_opts = ", ".join(VALID_TRANSPORTS)
        print(
            f"Error: Invalid transport '{transport}'. Must be one of: {valid_opts}",
            file=sys.stderr,
        )
        sys.exit(1)

    host = get_config_value(args.host, "MCP_TEST_HOST", DEFAULT_HOST)
    port = get_port_value(args.port, "MCP_TEST_PORT", DEFAULT_PORT)

    return {
        "transport": transport,
        "host": host,
        "port": port,
    }


def main(args: Optional[list[str]] = None) -> None:
    """Main entry point for the MCP server.

    Args:
        args: Optional list of arguments (for testing). Defaults to sys.argv[1:].
    """
    parsed_args = parse_args(args)
    config = resolve_config(parsed_args)

    # Import mcp here to avoid import-time side effects
    # This ensures logging is properly configured before server starts
    from mcp_test_mcp.server import mcp

    transport = config["transport"]

    if transport == "stdio":
        # STDIO transport - default for Claude Desktop/Code
        mcp.run()
    elif transport == "streamable-http":
        # Streamable HTTP transport - FastMCP uses "http" internally
        mcp.run(transport="http", host=config["host"], port=config["port"])
    elif transport == "sse":
        # Legacy SSE transport
        mcp.run(transport="sse", host=config["host"], port=config["port"])


if __name__ == "__main__":
    main()

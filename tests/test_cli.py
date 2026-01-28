"""Tests for CLI argument parsing and configuration resolution.

This module tests the command-line interface for mcp-test-mcp, including:
- Argument parsing for --transport, --host, --port
- Environment variable handling (MCP_TEST_TRANSPORT, MCP_TEST_HOST, MCP_TEST_PORT)
- Priority resolution (CLI > env var > default)
"""

import os
from unittest import mock

import pytest

from mcp_test_mcp.__main__ import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TRANSPORT,
    VALID_TRANSPORTS,
    get_config_value,
    get_port_value,
    parse_args,
    resolve_config,
)


class TestParseArgs:
    """Tests for parse_args function."""

    def test_no_args_returns_defaults(self):
        """With no arguments, all values should be None (to allow env var fallback)."""
        args = parse_args([])
        assert args.transport is None
        assert args.host is None
        assert args.port is None

    def test_transport_stdio(self):
        """--transport stdio should be accepted."""
        args = parse_args(["--transport", "stdio"])
        assert args.transport == "stdio"

    def test_transport_streamable_http(self):
        """--transport streamable-http should be accepted."""
        args = parse_args(["--transport", "streamable-http"])
        assert args.transport == "streamable-http"

    def test_transport_sse(self):
        """--transport sse should be accepted."""
        args = parse_args(["--transport", "sse"])
        assert args.transport == "sse"

    def test_transport_short_flag(self):
        """Short flag -t should work for transport."""
        args = parse_args(["-t", "streamable-http"])
        assert args.transport == "streamable-http"

    def test_invalid_transport_exits(self):
        """Invalid transport should cause argparse to exit."""
        with pytest.raises(SystemExit):
            parse_args(["--transport", "invalid"])

    def test_host_argument(self):
        """--host should set the host value."""
        args = parse_args(["--host", "0.0.0.0"])
        assert args.host == "0.0.0.0"

    def test_host_short_flag(self):
        """Short flag -H should work for host."""
        args = parse_args(["-H", "192.168.1.1"])
        assert args.host == "192.168.1.1"

    def test_port_argument(self):
        """--port should set the port value as integer."""
        args = parse_args(["--port", "9000"])
        assert args.port == 9000
        assert isinstance(args.port, int)

    def test_port_short_flag(self):
        """Short flag -p should work for port."""
        args = parse_args(["-p", "8080"])
        assert args.port == 8080

    def test_invalid_port_exits(self):
        """Non-integer port should cause argparse to exit."""
        with pytest.raises(SystemExit):
            parse_args(["--port", "not-a-number"])

    def test_all_arguments_combined(self):
        """All arguments should work together."""
        args = parse_args([
            "--transport", "streamable-http",
            "--host", "0.0.0.0",
            "--port", "8080"
        ])
        assert args.transport == "streamable-http"
        assert args.host == "0.0.0.0"
        assert args.port == 8080


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_cli_value_takes_precedence(self):
        """CLI value should take precedence over env var and default."""
        with mock.patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            result = get_config_value("cli_value", "TEST_VAR", "default_value")
            assert result == "cli_value"

    def test_env_var_used_when_no_cli(self):
        """Env var should be used when CLI value is None."""
        with mock.patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            result = get_config_value(None, "TEST_VAR", "default_value")
            assert result == "env_value"

    def test_default_used_when_no_cli_or_env(self):
        """Default should be used when CLI and env var are not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Ensure the env var is not set
            os.environ.pop("TEST_VAR", None)
            result = get_config_value(None, "TEST_VAR", "default_value")
            assert result == "default_value"

    def test_empty_string_cli_value_is_used(self):
        """Empty string CLI value should be used (not fallback to env)."""
        with mock.patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            result = get_config_value("", "TEST_VAR", "default_value")
            assert result == ""


class TestGetPortValue:
    """Tests for get_port_value function."""

    def test_cli_value_takes_precedence(self):
        """CLI port value should take precedence over env var and default."""
        with mock.patch.dict(os.environ, {"TEST_PORT": "9000"}):
            result = get_port_value(8080, "TEST_PORT", 8000)
            assert result == 8080

    def test_env_var_used_when_no_cli(self):
        """Env var should be used when CLI value is None."""
        with mock.patch.dict(os.environ, {"TEST_PORT": "9000"}):
            result = get_port_value(None, "TEST_PORT", 8000)
            assert result == 9000

    def test_default_used_when_no_cli_or_env(self):
        """Default should be used when CLI and env var are not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TEST_PORT", None)
            result = get_port_value(None, "TEST_PORT", 8000)
            assert result == 8000

    def test_invalid_env_var_returns_default(self, capsys):
        """Invalid env var port should fall back to default with warning."""
        with mock.patch.dict(os.environ, {"TEST_PORT": "not-a-number"}):
            result = get_port_value(None, "TEST_PORT", 8000)
            assert result == 8000

            # Check warning was printed
            captured = capsys.readouterr()
            assert "Warning" in captured.err
            assert "not-a-number" in captured.err


class TestResolveConfig:
    """Tests for resolve_config function."""

    def test_all_defaults(self):
        """With no CLI args or env vars, defaults should be used."""
        # Clear relevant environment variables
        env_patch = {
            k: v for k, v in os.environ.items()
            if not k.startswith("MCP_TEST_")
        }
        with mock.patch.dict(os.environ, env_patch, clear=True):
            args = parse_args([])
            config = resolve_config(args)

            assert config["transport"] == DEFAULT_TRANSPORT
            assert config["host"] == DEFAULT_HOST
            assert config["port"] == DEFAULT_PORT

    def test_cli_args_take_precedence(self):
        """CLI args should override env vars."""
        with mock.patch.dict(os.environ, {
            "MCP_TEST_TRANSPORT": "sse",
            "MCP_TEST_HOST": "10.0.0.1",
            "MCP_TEST_PORT": "7000"
        }):
            args = parse_args([
                "--transport", "streamable-http",
                "--host", "0.0.0.0",
                "--port", "8080"
            ])
            config = resolve_config(args)

            assert config["transport"] == "streamable-http"
            assert config["host"] == "0.0.0.0"
            assert config["port"] == 8080

    def test_env_vars_used_when_no_cli(self):
        """Env vars should be used when CLI args not provided."""
        with mock.patch.dict(os.environ, {
            "MCP_TEST_TRANSPORT": "streamable-http",
            "MCP_TEST_HOST": "192.168.1.100",
            "MCP_TEST_PORT": "9000"
        }):
            args = parse_args([])
            config = resolve_config(args)

            assert config["transport"] == "streamable-http"
            assert config["host"] == "192.168.1.100"
            assert config["port"] == 9000

    def test_invalid_transport_from_env_exits(self):
        """Invalid transport from env var should cause exit."""
        with mock.patch.dict(os.environ, {"MCP_TEST_TRANSPORT": "invalid"}):
            args = parse_args([])
            with pytest.raises(SystemExit):
                resolve_config(args)

    def test_mixed_cli_and_env(self):
        """CLI and env vars can be mixed."""
        with mock.patch.dict(os.environ, {
            "MCP_TEST_HOST": "10.0.0.1",
            "MCP_TEST_PORT": "7000"
        }):
            args = parse_args(["--transport", "streamable-http"])
            config = resolve_config(args)

            assert config["transport"] == "streamable-http"  # From CLI
            assert config["host"] == "10.0.0.1"  # From env
            assert config["port"] == 7000  # From env


class TestValidTransports:
    """Tests to ensure all documented transports are valid."""

    def test_stdio_is_valid(self):
        """stdio should be a valid transport."""
        assert "stdio" in VALID_TRANSPORTS

    def test_streamable_http_is_valid(self):
        """streamable-http should be a valid transport."""
        assert "streamable-http" in VALID_TRANSPORTS

    def test_sse_is_valid(self):
        """sse should be a valid transport."""
        assert "sse" in VALID_TRANSPORTS

    def test_default_is_stdio(self):
        """Default transport should be stdio."""
        assert DEFAULT_TRANSPORT == "stdio"

    def test_default_host(self):
        """Default host should be localhost."""
        assert DEFAULT_HOST == "127.0.0.1"

    def test_default_port(self):
        """Default port should be 8000."""
        assert DEFAULT_PORT == 8000

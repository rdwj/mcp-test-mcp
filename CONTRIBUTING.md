# Contributing to mcp-test-mcp

Thank you for your interest in contributing to mcp-test-mcp! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)

## Code of Conduct

This project and everyone participating in it is governed by respect and professionalism. Be kind, constructive, and welcoming to all contributors.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [issue tracker](https://github.com/rdwj/mcp-test-mcp/issues) to avoid duplicates.

When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Node version)
- **Error messages** and logs if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **Include examples** of how it would work

### Pull Requests

- Fill in the pull request template
- Follow the [style guidelines](#style-guidelines)
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 16 or higher (for npm wrapper)
- Git

### Initial Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/mcp-test-mcp.git
cd mcp-test-mcp
```

2. **Set up Python development environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

3. **Set up Node wrapper (optional)**

```bash
cd node-wrapper
npm install
```

### Development Tools

The project uses several tools for code quality:

- **pytest** - Testing framework
- **black** - Code formatting
- **ruff** - Fast linting
- **mypy** - Type checking

Install all tools with:
```bash
pip install -e ".[dev]"
```

## Making Changes

### Branch Strategy

1. Create a feature branch from `main`:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes in logical commits

3. Keep commits focused and atomic

### Commit Messages

Write clear commit messages:

```
Add tool for listing MCP resources

- Implement list_resources tool
- Add tests for resource listing
- Update documentation

Closes #123
```

Format:
- **First line**: Brief summary (50 chars or less)
- **Body**: Detailed explanation of what and why
- **Footer**: Reference related issues

## Submitting Changes

### Before Submitting

1. **Run tests**
```bash
pytest
```

2. **Check code formatting**
```bash
black src/ tests/
```

3. **Run linter**
```bash
ruff check src/ tests/
```

4. **Type check**
```bash
mypy src/
```

5. **Ensure coverage**
```bash
pytest --cov=mcp_test_mcp --cov-report=term-missing
```

Target: 80%+ code coverage

### Creating Pull Request

1. Push your branch to GitHub
2. Open a pull request against `main`
3. Fill out the PR template completely
4. Link related issues
5. Wait for CI checks to pass
6. Address review comments

## Style Guidelines

### Python Style

Follow PEP 8 and these additional guidelines:

**Code Formatting**
- Line length: 100 characters
- Use `black` for automatic formatting
- Use type hints for all functions

**Naming Conventions**
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

**Example**
```python
from typing import Dict, Any

class ConnectionManager:
    """Manages MCP server connections."""

    DEFAULT_TIMEOUT: float = 30.0

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    async def connect_to_server(self, url: str) -> Dict[str, Any]:
        """Connect to an MCP server.

        Args:
            url: Server URL (file path or HTTP endpoint)

        Returns:
            Connection state dictionary
        """
        # Implementation
        pass
```

### JavaScript/Node Style

For the npm wrapper:

- Use ES6+ features
- Semicolons required
- 2-space indentation
- Clear variable names
- Comments for complex logic

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep README up to date
- Document all public APIs
- Use docstrings for all functions/classes

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_test_mcp --cov-report=html

# Run specific test file
pytest tests/test_connection.py -v

# Run specific test
pytest tests/test_connection.py::test_connect_stdio -v
```

### Writing Tests

- Test both success and failure cases
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Aim for 80%+ coverage

**Example**
```python
import pytest
from mcp_test_mcp.connection import ConnectionManager

@pytest.mark.asyncio
async def test_connect_to_stdio_server_success():
    """Test successful connection to STDIO server."""
    # Arrange
    manager = ConnectionManager()
    server_path = "/path/to/server"

    # Act
    result = await manager.connect_to_server(server_path)

    # Assert
    assert result["success"] is True
    assert result["connection"]["transport"] == "stdio"
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_connection.py       # Connection tests
├── test_tools/
│   ├── test_connection.py   # Tool tests
│   └── test_llm.py
└── test_integration.py      # Integration tests
```

## Project Structure

```
mcp-test-mcp/
├── src/
│   └── mcp_test_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py          # FastMCP server
│       ├── connection.py      # Connection manager
│       ├── models.py          # Data models
│       └── tools/             # Tool implementations
├── tests/                     # Test suite
├── node-wrapper/              # npm package wrapper
│   ├── index.js
│   ├── package.json
│   └── scripts/
├── docs/                      # Documentation
├── pyproject.toml            # Python project config
└── README.md
```

## Release Process

### For Maintainers

1. Update version in `pyproject.toml` and `node-wrapper/package.json`
2. Update CHANGELOG.md
3. Create release commit
4. Tag release: `git tag v0.1.1`
5. Push to GitHub: `git push && git push --tags`
6. Publish to npm: `cd node-wrapper && npm publish`
7. Create GitHub release with notes

## Getting Help

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Email**: Contact the maintainer directly

## Recognition

Contributors will be recognized in:
- README.md acknowledgments
- Release notes
- GitHub contributors page

Thank you for contributing to mcp-test-mcp! 🎉

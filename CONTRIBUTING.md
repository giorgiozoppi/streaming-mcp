# Contributing to Langchain Streaming MCP

Thank you for your interest in contributing to Langchain Streaming MCP! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic knowledge of FastAPI, LangChain, and async programming

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/streaming-mcp.git
   cd streaming-mcp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation**
   ```bash
   langchain-streaming-mcp --help
   pytest
   ```

## 🔧 Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Critical fixes

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

2. **Make your changes**
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest

   # Check code style
   black src/ tests/
   ruff check src/ tests/ --fix

   # Type checking
   mypy src/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/amazing-new-feature
   ```

## 📝 Coding Standards

### Python Style

We follow Google Python Style Guide with these tools:

- **Black** for code formatting (88 character line length)
- **Ruff** for linting with extensive rules
- **MyPy** for static type checking (strict mode)

### Code Quality Requirements

- **Type Hints**: All functions must have type hints
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Test Coverage**: Aim for >90% test coverage for new code
- **No Breaking Changes**: Maintain backward compatibility

### Example Function

```python
def process_text(text: str, operation: str = "uppercase") -> str:
    """Process text with the specified operation.

    Args:
        text: The input text to process.
        operation: The operation to perform. Defaults to "uppercase".

    Returns:
        The processed text.

    Raises:
        ValueError: If the operation is not supported.
    """
    operations = {
        "uppercase": str.upper,
        "lowercase": str.lower,
    }

    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")

    return operations[operation](text)
```

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/langchain_streaming_mcp --cov-report=html

# Specific test file
pytest tests/test_tools.py

# Specific test function
pytest tests/test_tools.py::test_text_processor
```

### Writing Tests

- Use `pytest` fixtures for setup/teardown
- Test both sync and async functions
- Include edge cases and error conditions
- Use descriptive test names

Example test:

```python
import pytest
from langchain_streaming_mcp.tools import TextProcessorTool

@pytest.mark.asyncio
async def test_text_processor_uppercase():
    """Test text processor with uppercase operation."""
    tool = TextProcessorTool()
    result = await tool._arun("hello world", "uppercase")
    assert "HELLO WORLD" in result

def test_text_processor_invalid_operation():
    """Test text processor with invalid operation."""
    tool = TextProcessorTool()
    with pytest.raises(ValueError, match="Unknown operation"):
        tool._run("test", "invalid_operation")
```

## 🛠️ Adding New Features

### Adding a New Tool

1. **Create the tool class** in `src/langchain_streaming_mcp/tools.py`:

```python
class MyNewToolInput(BaseModel):
    param: str = Field(..., description="Parameter description")

class MyNewTool(BaseTool):
    name: str = "my_new_tool"
    description: str = "Description of what the tool does"
    args_schema: Type[BaseModel] = MyNewToolInput

    def _run(self, param: str) -> str:
        """Synchronous implementation."""
        return f"Processed: {param}"

    async def _arun(self, param: str) -> str:
        """Asynchronous implementation."""
        return self._run(param)
```

2. **Add to available tools** in `get_available_tools()` function

3. **Write tests** in `tests/test_tools.py`

4. **Update documentation** in README.md

### Adding New API Endpoints

1. **Add endpoint** in `src/langchain_streaming_mcp/server.py`
2. **Add Pydantic models** if needed in `models.py`
3. **Write tests** for the new endpoint
4. **Update API documentation**

## 📚 Documentation

### Updating Documentation

- Keep README.md current with new features
- Update docstrings for all changes
- Add examples for complex features
- Update API documentation

### Documentation Style

- Use clear, concise language
- Include code examples
- Use proper Markdown formatting
- Add emojis for visual appeal 🎉

## 🚢 Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Creating a Release

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a PR for review
4. After merge, create a Git tag
5. GitHub Actions will handle the release

## 🐛 Bug Reports

### Before Submitting

- Check existing issues
- Verify the bug with the latest version
- Gather relevant information

### Bug Report Template

```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Package Version: [e.g., 0.1.0]

**Additional Context**
Any other context about the problem.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
How you envision this feature working.

**Alternatives**
Any alternative solutions you've considered.

**Additional Context**
Any other context or screenshots.
```

## ❓ Questions and Support

- **Documentation**: Check README.md and `/docs` endpoint
- **Issues**: Create a GitHub issue for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our community chat (if available)

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Special thanks in documentation

Thank you for contributing to Langchain Streaming MCP! 🎉
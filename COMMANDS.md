# pystreaming Development Commands

This guide shows how to use UV, Ruff, and type checking tools with pystreaming.

## Prerequisites

Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

### Install the package in development mode
```bash
uv pip install -e .
```

### Install with dev dependencies
```bash
uv pip install -e ".[dev]"
```

## Testing

### Run all tests
```bash
uv run pytest
```

### Run tests with coverage
```bash
uv run pytest --cov=pystreaming --cov-report=term-missing
```

### Run a specific test file
```bash
uv run pytest tests/test_datstructures.py
```

## Linting & Formatting (Ruff)

### Check for linting issues
```bash
uv run ruff check .
```

### Auto-fix linting issues
```bash
uv run ruff check --fix .
```

### Format code
```bash
uv run ruff format .
```

### Check and format in one command
```bash
uv run ruff check . && uv run ruff format .
```

## Type Checking (ty via uvx)

### Run type checker (main library only)
```bash
uvx ty check pystreaming
```

### Type check with more verbose output
```bash
uvx ty check pystreaming --verbose
```

### Type check specific file
```bash
uvx ty check pystreaming/video/enc.py
```

**Note**: 
- `ty` is a standalone type checker from Astral (same team as Ruff/UV). It doesn't need to be installed as a dependency - `uvx` will automatically download and run it.
- We check only the `pystreaming` directory, excluding `manual_tests` and `docs` which have optional dependencies.

## Building & Publishing

### Build the package
```bash
uv build
```

### Install from built wheel
```bash
uv pip install dist/pystreaming-*.whl
```

## Quick Workflow

### Before committing (run all checks):
```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Type check
uvx ty check pystreaming

# Run tests
uv run pytest
```

### One-liner for pre-commit checks:
```bash
uv run ruff format . && uv run ruff check . && uvx ty check pystreaming && uv run pytest
```

## CI/CD Integration

For GitHub Actions, you can use:

```yaml
- name: Install UV
  uses: astral-sh/setup-uv@v1
  
- name: Install dependencies
  run: uv pip install -e ".[dev]"
  
- name: Format check
  run: uv run ruff format --check .
  
- name: Lint
  run: uv run ruff check .
  
- name: Type check
  run: uvx ty check pystreaming
  
- name: Test
  run: uv run pytest
```


# GitHub Actions CI/CD Pipeline

This repository uses GitHub Actions for continuous integration. The pipeline ensures code quality and functionality across multiple Python versions.

## Workflow Overview

### `ci.yml` - Main CI Pipeline

The main workflow runs on:
- **Push** to `main` and `develop` branches
- **Pull requests** to `main` and `develop` branches

## Pipeline Jobs

### 1. **Test Suite** (`test`)
- **Multi-version testing**: Python 3.9, 3.10, 3.11, 3.12
- **pytest** with coverage reporting
- **Coverage XML** generated for Codecov
- **Codecov integration** for coverage tracking (Python 3.9 only)

### 2. **Code Quality & Linting** (`lint`)
- **flake8** - Code linting and style checking
  - Error checking: E9, F63, F7, F82
  - Complexity checking: max complexity 10
  - Line length: max 100 characters
- **Black** - Code formatting validation
- **isort** - Import sorting validation
- **mypy** - Static type checking (allowed to fail)

## Configuration Files

### Core Configuration
- **`pyproject.toml`** - Project metadata, dependencies, tool configuration

## Tool Configuration

### **Black** (Code Formatting)
```toml
[tool.black]
line-length = 100
target-version = ['py39']
```

### **isort** (Import Sorting)
```toml
[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["prunarr"]
```

### **mypy** (Type Checking)
```toml
[tool.mypy]
python_version = "3.9"
disallow_untyped_defs = true
warn_return_any = true
```

### **pytest** (Testing)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--cov=prunarr", "--cov-report=xml", "--cov-report=term-missing"]
```

## Quality Gates

### **Code Quality Requirements**
- ✅ Black formatting compliance
- ✅ isort import organization
- ✅ flake8 linting (max complexity: 10, max line length: 100)
- ⚠️ mypy type checking (allowed to fail)

### **Test Requirements**
- ✅ All tests pass on Python 3.9, 3.10, 3.11, 3.12
- ✅ Coverage reporting uploaded to Codecov

## Development Workflow

### **Local Development**
```bash
# Set up development environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=prunarr --cov-report=xml --cov-report=term-missing

# Run linting checks
flake8 prunarr/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 prunarr/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

# Check code formatting
black --check prunarr/ tests/

# Fix code formatting
black prunarr/ tests/

# Check import sorting
isort --check-only prunarr/ tests/

# Fix import sorting
isort prunarr/ tests/

# Run type checking
mypy prunarr/
```

## Continuous Integration Features

### **Parallel Execution**
- Tests run in parallel across Python 3.9, 3.10, 3.11, 3.12
- Independent linting and test jobs

### **Coverage Tracking**
- **Codecov integration** for coverage history
- Coverage XML uploaded from Python 3.9 test run
- Coverage reports available in CI output

## Status Badges

Add these badges to your README.md:

```markdown
![CI](https://github.com/haijeploeg/prunarr/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/haijeploeg/prunarr/branch/main/graph/badge.svg)](https://codecov.io/gh/haijeploeg/prunarr)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
```
# GitHub Actions CI/CD Pipeline

This repository uses GitHub Actions for continuous integration and deployment. The pipeline ensures code quality, security, and functionality across multiple Python versions and operating systems.

## Workflow Overview

### `ci.yml` - Main CI/CD Pipeline

The main workflow runs on:
- **Push** to `main` and `develop` branches
- **Pull requests** to `main` and `develop` branches
- **Manual trigger** via workflow_dispatch

## Pipeline Jobs

### 1. **Code Quality & Linting** (`lint`)
- **Black** - Code formatting validation
- **isort** - Import sorting validation
- **flake8** - Code linting and style checking
- **mypy** - Static type checking
- **bandit** - Security vulnerability scanning

### 2. **Test Suite** (`test`)
- **Multi-version testing**: Python 3.9, 3.10, 3.11, 3.12
- **pytest** with coverage reporting
- **Coverage requirement**: Minimum 80%
- **Codecov integration** for coverage tracking
- **JUnit XML** test results

### 3. **Integration Tests** (`integration-test`)
- **CLI installation** verification
- **Configuration validation** testing
- **End-to-end** functionality tests
- **Real-world usage** scenarios

### 4. **Security Scanning** (`security`)
- **Trivy** vulnerability scanner
- **Safety** dependency vulnerability check
- **SARIF reports** uploaded to GitHub Security
- **Automated security alerts**

### 5. **Build & Package** (`build`)
- **Package building** with setuptools
- **Distribution validation** with twine
- **Artifact uploads** for deployment
- **Package integrity** verification

### 6. **Documentation** (`docs`)
- **README link validation**
- **Docstring completeness** checking
- **Documentation structure** validation
- **API documentation** verification

### 7. **Performance Tests** (`performance`)
- **Configuration loading** benchmarks
- **Memory usage** monitoring
- **Performance regression** detection
- **Speed requirements** validation

### 8. **Compatibility Tests** (`compatibility`)
- **Multi-OS testing**: Ubuntu, Windows, macOS
- **Python version compatibility**
- **Cross-platform** functionality
- **Installation verification**

### 9. **Release** (`release`)
- **Automated releases** on `[release]` commit message
- **Artifact publishing** to GitHub Releases
- **Version tagging** and release notes
- **Distribution uploads**

### 10. **Notification** (`notify`)
- **Success/failure** notifications
- **Pipeline status** reporting
- **Error alerting**

## Configuration Files

### Core Configuration
- **`pyproject.toml`** - Project metadata, dependencies, tool configuration
- **`.flake8`** - Linting rules and exclusions
- **`.pre-commit-config.yaml`** - Pre-commit hooks configuration
- **`pytest.ini`** - Test configuration (alternative to pyproject.toml)

### Development Tools
- **`Makefile`** - Development command shortcuts
- **`.bandit`** - Security scanning configuration
- **`.github/dependabot.yml`** - Dependency update automation

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
addopts = ["--cov=prunarr", "--cov-fail-under=80"]
```

## Quality Gates

### **Code Quality Requirements**
- ✅ Black formatting compliance
- ✅ isort import organization
- ✅ flake8 linting (max complexity: 10)
- ✅ mypy type checking
- ✅ No security vulnerabilities (bandit)

### **Test Requirements**
- ✅ All tests pass on Python 3.9+
- ✅ Minimum 80% code coverage
- ✅ Integration tests pass
- ✅ CLI functionality verified

### **Security Requirements**
- ✅ No high/critical vulnerabilities (Trivy)
- ✅ No known vulnerable dependencies (Safety)
- ✅ Security best practices (Bandit)

### **Compatibility Requirements**
- ✅ Works on Ubuntu, Windows, macOS
- ✅ Compatible with Python 3.9-3.12
- ✅ Package builds successfully
- ✅ Installation works correctly

## Development Workflow

### **Local Development**
```bash
# Set up development environment
make dev-setup
source .venv/bin/activate

# Run all checks locally
make check-all

# Run specific checks
make lint
make test
make security
```

### **Pre-commit Hooks**
```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### **Manual Testing**
```bash
# Run tests with coverage
make test

# Run specific test categories
make test-unit
make test-integration
make test-cli
```

## Continuous Integration Features

### **Parallel Execution**
- Tests run in parallel across Python versions
- Multiple OS compatibility tests
- Independent security and quality checks

### **Caching**
- **Dependency caching** for faster builds
- **Virtual environment caching**
- **Tool installation caching**

### **Artifact Management**
- **Test results** uploaded for debugging
- **Coverage reports** stored and tracked
- **Security scan results** archived
- **Build artifacts** ready for release

### **Error Handling**
- **Detailed failure reporting**
- **Artifact uploads on failure**
- **Debug information collection**
- **Clear error messages**

## Release Process

### **Automated Release Triggers**
1. Push to `main` branch with `[release]` in commit message
2. All quality gates must pass
3. Automated version tagging
4. GitHub Release creation with artifacts

### **Manual Release Steps**
```bash
# Prepare for release
make release-check

# Tag version (triggers release)
git tag v2.0.0
git push origin v2.0.0
```

## Monitoring & Alerts

### **Coverage Tracking**
- **Codecov integration** for coverage history
- **Coverage requirements** enforced
- **Regression detection**

### **Security Monitoring**
- **Automated vulnerability scanning**
- **Dependency update notifications**
- **Security advisory alerts**

### **Performance Monitoring**
- **Build time tracking**
- **Test execution time**
- **Performance regression alerts**

## Status Badges

Add these badges to your README.md:

```markdown
![CI](https://github.com/hploeg/prunarr/workflows/CI%2FCD%20Pipeline/badge.svg)
[![codecov](https://codecov.io/gh/hploeg/prunarr/branch/main/graph/badge.svg)](https://codecov.io/gh/hploeg/prunarr)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue)](https://mypy.readthedocs.io/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
```
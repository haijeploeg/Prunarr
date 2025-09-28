# PrunArr Development Makefile

.PHONY: help install dev-install test lint format type-check security clean build docs pre-commit

help: ## Show this help message
	@echo "PrunArr Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests with coverage
	pytest --cov=prunarr --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	pytest -x -v

test-watch: ## Run tests in watch mode
	pytest -f

lint: ## Run all linting checks
	black --check prunarr/ tests/
	isort --check-only prunarr/ tests/
	flake8 prunarr/ tests/
	mypy prunarr/
	bandit -r prunarr/

format: ## Format code with black and isort
	black prunarr/ tests/
	isort prunarr/ tests/

type-check: ## Run type checking with mypy
	mypy prunarr/

security: ## Run security checks
	bandit -r prunarr/
	safety check

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build

docs: ## Generate documentation
	@echo "Documentation is in README.md and tests/README.md"
	@echo "API documentation is available in docstrings"

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

check-all: lint test security ## Run all checks (lint, test, security)

ci: ## Run full CI pipeline locally
	make clean
	make lint
	make test
	make security
	make build
	@echo "✅ All CI checks passed!"

release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	make clean
	make lint
	make test
	make security
	make build
	twine check dist/*
	@echo "✅ Ready for release!"

# Development helpers
dev-setup: ## Set up development environment
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/pre-commit install
	@echo "✅ Development environment set up!"
	@echo "Activate with: source .venv/bin/activate"

requirements: ## Generate requirements.txt from pyproject.toml
	pip-compile pyproject.toml

update-deps: ## Update all dependencies
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"

# Testing variants
test-unit: ## Run only unit tests
	pytest -m unit

test-integration: ## Run only integration tests
	pytest -m integration

test-cli: ## Run only CLI tests
	pytest -m cli

test-api: ## Run only API tests
	pytest -m api

# Coverage variants
coverage: ## Generate coverage report
	pytest --cov=prunarr --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml: ## Generate XML coverage report
	pytest --cov=prunarr --cov-report=xml

# Local development
run-help: ## Show CLI help (requires installation)
	prunarr --help

run-example: ## Run example command (requires configuration)
	@echo "Example usage (requires valid config.yaml):"
	@echo "prunarr --config config.yaml movies list"
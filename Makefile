# PrunArr Development Makefile

.PHONY: help install dev-install test lint format clean

help: ## Show this help message
	@echo "PrunArr Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"

test: ## Run tests with coverage
	pytest --cov=prunarr --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	pytest -x -v

lint: ## Run all linting checks
	flake8 prunarr/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 prunarr/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	autoflake --check --remove-all-unused-imports --remove-unused-variables -r prunarr/ tests/
	black --check prunarr/ tests/
	isort --check-only prunarr/ tests/

format: ## Format code with black, isort, and autoflake
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables -r prunarr/ tests/
	isort prunarr/ tests/
	black prunarr/ tests/

clean: ## Clean build artifacts and cache
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage .pytest_cache/ .mypy_cache/
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build
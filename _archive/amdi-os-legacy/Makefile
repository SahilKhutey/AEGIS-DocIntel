.PHONY: help install dev test lint run docker-up docker-down clean

help:
	@echo "AEGIS-AMDI-OS Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-20s %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev: ## Install with dev extras
	pip install -e ".[dev,embeddings]"
	cd dashboard && npm install

test: ## Run all tests
	python -m pytest tests/ -v --tb=short -q

test-unit: ## Unit tests only
	python -m pytest tests/unit -v --tb=short

test-integration: ## Integration tests
	python -m pytest tests/integration -v --tb=short

lint: ## Lint
	ruff check src/ tests/

format: ## Format
	ruff format src/ tests/

run: ## Start API server
	uvicorn src.api.api_server:app --host 0.0.0.0 --port 8000 --reload

dashboard: ## Start React dashboard
	cd dashboard && npm run dev

docker-up: ## Start full stack
	docker-compose up -d

docker-down: ## Stop full stack
	docker-compose down

docker-logs: ## Tail logs
	docker-compose logs -f api

clean: ## Clean artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

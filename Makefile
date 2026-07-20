.PHONY: help smoke test lint hello-world-test hello-world-lint hello-world-build hello-world-run docker-build docker-up docker-down clean

SERVICE := hello-world

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# --- Top-level targets -------------------------------------------------------

smoke: hello-world-test hello-world-lint hello-world-build ## Run the full smoke suite (test + lint + build) for the sample service.

test: hello-world-test ## Run all unit tests.

lint: hello-world-lint ## Run all linters.

# --- hello-world --------------------------------------------------------------

hello-world-test: ## Run hello-world unit tests.
	cd services/hello-world && python -m pytest app/ -v

hello-world-lint: ## Lint hello-world.
	cd services/hello-world && python -m ruff check app/

hello-world-build: ## Build the hello-world Docker image.
	docker build -t ventureminer/hello-world:dev services/hello-world/

hello-world-run: ## Run hello-world locally on :8000.
	cd services/hello-world && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# --- Local Docker Compose ---------------------------------------------------

docker-build: ## Build all local images.
	docker compose build

docker-up: ## Bring up the local stack.
	docker compose up -d

docker-down: ## Tear down the local stack.
	docker compose down

# --- Housekeeping ------------------------------------------------------------

clean: ## Remove caches and build artifacts.
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +

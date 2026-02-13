.PHONY: install test lint format typecheck sync run run-http clean all

install:                   ## Install dependencies (including dev)
	uv sync

test:                      ## Run tests
	uv run pytest tests/ -v

lint:                      ## Run linter
	uv run ruff check src/ tests/

format:                    ## Format code
	uv run ruff format src/ tests/

typecheck:                 ## Run type checker
	uv run mypy src/

sync:                      ## Sync API spec from developer.yclients.com
	uv run python scripts/sync_spec.py

sync-dry:                  ## Check for spec changes (no update)
	uv run python scripts/sync_spec.py --dry-run

run:                       ## Run MCP server (stdio mode)
	uv run yclients-mcp-server

run-http:                  ## Run MCP server (HTTP mode on port 8000)
	MCP_TRANSPORT=http uv run yclients-mcp-server

clean:                     ## Clean build artifacts
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

all: lint typecheck test   ## Run all checks

help:                      ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

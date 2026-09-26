.PHONY: help install dev infra-up infra-down migrate index test lint format clean

help:
	@echo "Available commands:"
	@echo "  install      - Install all dependencies"
	@echo "  dev          - Start development servers (backend + frontend)"
	@echo "  infra-up     - Start infrastructure (PostgreSQL, Qdrant)"
	@echo "  infra-down   - Stop infrastructure"
	@echo "  migrate      - Run database migrations"
	@echo "  index        - Run indexing"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linters"
	@echo "  format       - Format code"
	@echo "  clean        - Clean build artifacts"

# Backend
install-backend:
	cd backend && uv pip install -e .[dev]

# Frontend
install-frontend:
	cd frontend && pnpm install

install: install-backend install-frontend

# Development
dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && pnpm dev

dev: infra-up
	@echo "Starting backend and frontend..."
	@make -j2 dev-backend dev-frontend

# Infrastructure
infra-up:
	docker compose up -d

infra-down:
	docker compose down

infra-logs:
	docker compose logs -f

# Database
migrate:
	cd backend && uv run alembic upgrade head

migrate-create:
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

# Indexing
index:
	cd backend && uv run python -m app.domain.indexing.cli

# Testing
test-backend:
	cd backend && uv run pytest -v

test-frontend:
	cd frontend && pnpm test

test: test-backend test-frontend

# Linting
lint-backend:
	cd backend && uv run ruff check .

lint-frontend:
	cd frontend && pnpm lint

lint: lint-backend lint-frontend

# Formatting
format-backend:
	cd backend && uv run ruff format .

format-frontend:
	cd frontend && pnpm format

format: format-backend format-frontend

# Clean
clean:
	cd backend && rm -rf .pytest_cache __pycache__ .ruff_cache
	cd frontend && rm -rf .next node_modules
	docker compose down -v
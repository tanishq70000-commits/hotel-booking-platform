.PHONY: help up down restart logs ps build test test-concurrency lint format seed backup restore restore-drill rollback rollback-drill failure-drill scan clean

PYTHON := $(shell which python3 2>/dev/null || which python 2>/dev/null || echo python)
VENV_PYTHON := .venv/bin/python
ifeq ($(OS),Windows_NT)
    VENV_PYTHON := .venv/Scripts/python.exe
endif

ifneq ("$(wildcard $(VENV_PYTHON))","")
    PYTHON := $(VENV_PYTHON)
endif

COMPOSE_FILE := deploy/docker-compose.yml
COMPOSE_PROD_FILE := deploy/docker-compose.prod.yml

help: ## Show this help message
	@echo "Available commands in Hotel Reservation API Makefile:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images locally
	docker compose -f $(COMPOSE_FILE) build

up: ## Start orchestrated application, database and Caddy reverse proxy
	docker compose -f $(COMPOSE_FILE) up -d --build
	@echo "Waiting for services to become healthy..."
	@sleep 5
	docker compose -f $(COMPOSE_FILE) ps

down: ## Stop and remove containers and network volumes
	docker compose -f $(COMPOSE_FILE) down -v

restart: ## Restart all running containers
	docker compose -f $(COMPOSE_FILE) restart

logs: ## Tail aggregated structured JSON logs from all containers
	docker compose -f $(COMPOSE_FILE) logs -f

ps: ## Check status and health of all stack containers
	docker compose -f $(COMPOSE_FILE) ps

lint: ## Run ruff lint, ruff format check, and mypy static type checking
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m mypy app scripts

format: ## Automatically format and fix code using ruff
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

test: ## Run complete test suite and capture output to evidence/test-output.txt
	@mkdir -p evidence
	$(PYTHON) -m pytest --cov=app --cov-report=term-missing --cov-report=html:evidence/coverage_html | tee evidence/test-output.txt

test-concurrency: ## Run concurrency race condition tests (acceptance test #1)
	$(PYTHON) -m pytest tests/test_concurrency.py -v -s

seed: ## Populate database inventory and sample reservations idempotently
	$(PYTHON) -m scripts.seed

backup: ## Create a timestamped, checksummed database backup
	bash scripts/backup.sh

restore: ## Restore database from latest backup file
	bash scripts/restore.sh

restore-drill: ## Execute point-in-time data recovery drill and verify integrity
	bash scripts/restore_drill.sh

rollback: ## Roll back deployment to previous stable image tag
	bash scripts/rollback.sh $$(IMAGE_TAG)

rollback-drill: ## Demonstrate deployment release rollback with verification
	bash scripts/rollback_drill.sh

failure-drill: ## Execute automated database outage and process crash recovery drills
	bash scripts/failure_drill.sh

concurrency-demo: ## Execute live concurrency demo against reservation endpoint
	bash scripts/concurrency_demo.sh

scan: ## Run pip-audit vulnerability scan on dependencies
	$(PYTHON) -m pip_audit -r requirements.txt || true

clean: ## Clean up temporary files, build artifacts and test databases
	rm -rf .pytest_cache .coverage htmlcov evidence/coverage_html *.db* build dist *.egg-info


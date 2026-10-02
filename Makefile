# AERIS — Makefile
# All required workflow targets for the predictive maintenance platform.
SHELL := /bin/bash
.DEFAULT_GOAL := help

# ── Variables ───────────────────────────────────────────────────────
COMPOSE := docker compose
BACKEND_EXEC := $(COMPOSE) exec -T backend
FRONTEND_EXEC := $(COMPOSE) exec -T frontend

# ── Primary Targets ─────────────────────────────────────────────────

.PHONY: help
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: secrets certs build ## Generate secrets + certs, build all images
	@echo "[+] Setup complete. Run 'make up' to start services."

.PHONY: secrets
secrets: ## Generate secrets into ./secrets/
	@bash scripts/gen_secrets.sh

.PHONY: certs
certs: ## Generate self-signed TLS certificates
	@bash scripts/gen_certs.sh

.PHONY: build
build: ## Build all Docker images
	$(COMPOSE) build

.PHONY: up
up: ## Start all services
	$(COMPOSE) up -d
	@echo "[+] AERIS running at https://localhost:8443"
	@echo "[+] Waiting for services to be healthy..."
	@sleep 10
	@$(COMPOSE) ps

.PHONY: down
down: ## Stop all services
	$(COMPOSE) down

.PHONY: seed
seed: migrate generate-data ingest train score recommend create-demo-users ## Full seed: migrate + data + ingest + train + score + recommend + users
	@echo "[+] Seed complete."

.PHONY: migrate
migrate: ## Run Alembic migrations
	$(BACKEND_EXEC) python -m alembic upgrade head
	$(BACKEND_EXEC) python -c "from app.db.session import get_engine; from sqlalchemy import text; e=get_engine(); c=e.connect(); c.execute(text('SELECT protect_immutable_tables()')); c.commit(); c.close()"
	@echo "[+] Migrations applied and immutable table protections enabled."

.PHONY: generate-data
generate-data: ## Generate synthetic data
	$(BACKEND_EXEC) python -m data_gen.generate_synthetic
	@echo "[+] Synthetic data generated."

.PHONY: ingest
ingest: ## Ingest synthetic data into database
	$(BACKEND_EXEC) python -m app.db.seed --ingest
	@echo "[+] Data ingested."

.PHONY: train
train: ## Train ML models
	$(BACKEND_EXEC) python -m app.ml.train
	@echo "[+] Models trained."

.PHONY: score
score: ## Run scoring on fleet
	$(BACKEND_EXEC) python -m app.services.scoring --run
	@echo "[+] Scoring complete."

.PHONY: recommend
recommend: ## Generate recommendations
	$(BACKEND_EXEC) python -m app.services.planner --run
	@echo "[+] Recommendations generated."

.PHONY: create-demo-users
create-demo-users: ## Create demo users from secrets/demo_credentials.txt
	$(BACKEND_EXEC) python -m app.db.seed --users
	@echo "[+] Demo users created."

.PHONY: test
test: ## Run all tests
	$(BACKEND_EXEC) python -m pytest tests/ -v --tb=short
	@echo "[+] Tests complete."

.PHONY: lint
lint: ## Run linters (ruff + mypy)
	$(BACKEND_EXEC) python -m ruff check app/
	$(BACKEND_EXEC) python -m mypy app/ --ignore-missing-imports
	@echo "[+] Lint complete."

.PHONY: security-scan
security-scan: ## Run security scanning tools
	@bash scripts/security_scan.sh

.PHONY: demo-reset
demo-reset: ## Full reset to clean demo state
	@bash scripts/demo_reset.sh

.PHONY: tamper-demo
tamper-demo: ## Demonstrate tamper detection (modifies a health reading)
	$(BACKEND_EXEC) python -m scripts.tamper_demo
	@echo "[+] Tamper demo executed. Check Evidence Passport verification."

.PHONY: logs
logs: ## Show service logs
	$(COMPOSE) logs -f --tail=100

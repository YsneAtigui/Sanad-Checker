# ==============================================================================
# MAKEFILE FOR SANAD AEO AUDITOR
# Simplifies Docker operations and development workflow
# ==============================================================================

.PHONY: help build up down restart logs shell test clean migrate

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

## help: Show this help message
help:
	@echo ""
	@echo "$(BLUE)Sanad AEO Auditor - Available Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make setup          - Initial project setup (copy .env, build, start)"
	@echo "  make build          - Build Docker images"
	@echo "  make pull-model     - Download Ollama AI model"
	@echo ""
	@echo "$(GREEN)Service Management:$(NC)"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make ps             - Show service status"
	@echo "  make logs           - Show logs (all services)"
	@echo "  make logs-api       - Show API logs"
	@echo "  make logs-worker    - Show Celery worker logs"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev            - Start in development mode with monitoring"
	@echo "  make shell          - Open shell in API container"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make test           - Run tests"
	@echo "  make format         - Format code with black"
	@echo "  make lint           - Lint code with ruff"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make migrate-down   - Rollback last migration"
	@echo "  make db-backup      - Backup database"
	@echo "  make db-restore     - Restore database from backup"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-all      - Stop, remove containers and volumes (⚠️  deletes data)"
	@echo "  make prune          - Clean up Docker system"
	@echo ""

## setup: Initial project setup
setup:
	@echo "$(BLUE)Setting up Sanad AEO Auditor...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created. Please review and update values!$(NC)"; \
	else \
		echo "$(YELLOW).env already exists, skipping...$(NC)"; \
	fi
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build
	@echo "$(BLUE)Starting services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Run: make pull-model"
	@echo "  2. Visit: http://localhost:8000/docs"

## build: Build Docker images
build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

## up: Start all services
up:
	@echo "$(BLUE)Starting services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@make ps

## down: Stop all services
down:
	@echo "$(BLUE)Stopping services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

## restart: Restart all services
restart:
	@echo "$(BLUE)Restarting services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

## ps: Show service status
ps:
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

## logs: Show logs for all services
logs:
	@docker-compose logs -f

## logs-api: Show API logs
logs-api:
	@docker-compose logs -f api

## logs-worker: Show Celery worker logs
logs-worker:
	@docker-compose logs -f celery-worker

## dev: Start in development mode
dev:
	@echo "$(BLUE)Starting in development mode...$(NC)"
	@BUILD_TARGET=development VOLUME_MODE=rw UVICORN_RELOAD=--reload \
		docker-compose --profile with-monitoring up -d
	@echo "$(GREEN)✓ Development mode started$(NC)"
	@echo "$(YELLOW)Monitoring URLs:$(NC)"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Flower:   http://localhost:5555"

## shell: Open shell in API container
shell:
	@echo "$(BLUE)Opening shell in API container...$(NC)"
	@docker-compose exec api sh

## shell-db: Open PostgreSQL shell
shell-db:
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	@docker-compose exec postgres psql -U sanad_user -d sanad_db

## test: Run tests
test:
	@echo "$(BLUE)Running tests...$(NC)"
	@docker-compose exec api pytest tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

## format: Format code with black
format:
	@echo "$(BLUE)Formatting code...$(NC)"
	@docker-compose exec api black app/
	@echo "$(GREEN)✓ Code formatted$(NC)"

## lint: Lint code with ruff
lint:
	@echo "$(BLUE)Linting code...$(NC)"
	@docker-compose exec api ruff check app/
	@echo "$(GREEN)✓ Linting complete$(NC)"

## migrate: Run database migrations
migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	@docker-compose exec api alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

## migrate-create: Create new migration
migrate-create:
	@read -p "Migration description: " desc; \
	echo "$(BLUE)Creating migration: $$desc$(NC)"; \
	docker-compose exec api alembic revision --autogenerate -m "$$desc"
	@echo "$(GREEN)✓ Migration created$(NC)"

## migrate-down: Rollback last migration
migrate-down:
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	@docker-compose exec api alembic downgrade -1
	@echo "$(GREEN)✓ Rollback complete$(NC)"

## pull-model: Download Ollama AI model
pull-model:
	@echo "$(BLUE)Downloading Ollama model (this may take several minutes)...$(NC)"
	@docker-compose exec ollama ollama pull qwen2.5:7b
	@echo "$(GREEN)✓ Model downloaded$(NC)"
	@docker-compose exec ollama ollama list

## db-backup: Backup database
db-backup:
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U sanad_user sanad_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backed up to backups/$(NC)"

## db-restore: Restore database from backup
db-restore:
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -1 backups/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " file; \
	if [ -f "$$file" ]; then \
		echo "$(BLUE)Restoring from $$file...$(NC)"; \
		docker-compose exec -T postgres psql -U sanad_user sanad_db < "$$file"; \
		echo "$(GREEN)✓ Database restored$(NC)"; \
	else \
		echo "$(RED)Backup file not found$(NC)"; \
	fi

## clean: Stop and remove containers
clean:
	@echo "$(YELLOW)Cleaning up containers...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

## clean-all: Stop and remove containers and volumes
clean-all:
	@echo "$(RED)⚠️  WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "$(YELLOW)Removing containers and volumes...$(NC)"; \
		docker-compose down -v; \
		echo "$(GREEN)✓ All data removed$(NC)"; \
	else \
		echo "$(BLUE)Cancelled$(NC)"; \
	fi

## prune: Clean up Docker system
prune:
	@echo "$(BLUE)Cleaning up Docker system...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✓ Docker system cleaned$(NC)"

## health: Check service health
health:
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo ""
	@echo "$(YELLOW)API Health:$(NC)"
	@curl -s http://localhost:8000/health | jq . || echo "$(RED)API not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker-compose exec postgres pg_isready -U sanad_user || echo "$(RED)PostgreSQL not ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose exec redis redis-cli ping || echo "$(RED)Redis not responding$(NC)"
	@echo ""

## stats: Show container resource usage
stats:
	@echo "$(BLUE)Container Resource Usage:$(NC)"
	@docker stats --no-stream sanad_api sanad_celery_worker sanad_postgres sanad_redis sanad_ollama

# Power Outage Monitor - Makefile
# Management commands for development and production

.PHONY: help up down logs migrate shell bash createadmin up-prod down-prod logs-prod migrate-prod createadmin-prod build clean

# Default target
help:
	@echo "Power Outage Monitor - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make up              - Start all services (local)"
	@echo "  make down            - Stop all services (local)"
	@echo "  make logs            - View logs (follow mode)"
	@echo "  make build           - Rebuild containers"
	@echo "  make migrate         - Run database migrations"
	@echo "  make makemigrations  - Create new migrations"
	@echo "  make shell           - Django shell"
	@echo "  make bash            - Shell into app container"
	@echo "  make createadmin     - Create admin user from env vars"
	@echo ""
	@echo "Production:"
	@echo "  make up-prod              - Start all services (production)"
	@echo "  make down-prod            - Stop all services (production)"
	@echo "  make logs-prod            - View production logs"
	@echo "  make migrate-prod         - Run production migrations"
	@echo "  make createadmin-prod     - Create production admin user"
	@echo ""
	@echo "Utility:"
	@echo "  make clean           - Remove all containers and volumes"

# ============================================
# Development Commands
# ============================================

recreate:
	docker-compose -f docker-compose.local.yml down -v --remove-orphans
	docker-compose -f docker-compose.local.yml up -d --build
up:
	docker-compose -f docker-compose.local.yml up -d

down:
	docker-compose -f docker-compose.local.yml down

logs:
	docker-compose -f docker-compose.local.yml logs -f

logs-app:
	docker-compose -f docker-compose.local.yml logs -f app

logs-worker:
	docker-compose -f docker-compose.local.yml logs -f worker

build:
	docker-compose -f docker-compose.local.yml up -d --build

migrate:
	docker-compose -f docker-compose.local.yml exec app python src/manage.py migrate

makemigrations:
	docker-compose -f docker-compose.local.yml exec app python src/manage.py makemigrations

shell:
	docker-compose -f docker-compose.local.yml exec app python src/manage.py shell

bash:
	docker-compose -f docker-compose.local.yml exec app /bin/bash

createadmin:
	docker-compose -f docker-compose.local.yml exec app python src/manage.py createadmin

# ============================================
# Production Commands
# ============================================

up-prod:
	docker-compose -f docker-compose.prod.yml up -d

down-prod:
	docker-compose -f docker-compose.prod.yml down

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f

migrate-prod:
	docker-compose -f docker-compose.prod.yml exec app python src/manage.py migrate

createadmin-prod:
	docker-compose -f docker-compose.prod.yml exec app python src/manage.py createadmin

# ============================================
# Utility Commands
# ============================================

clean:
	docker-compose -f docker-compose.local.yml down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans

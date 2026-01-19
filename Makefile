.PHONY: help up down build logs test lint migrate

help:
	@echo "Available commands:"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make build      - Build all containers"
	@echo "  make logs       - Show logs"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make migrate    - Run database migrations"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Start development environment"

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

test:
	docker-compose exec backend pytest tests/ -v

lint:
	docker-compose exec backend ruff check backend/
	docker-compose exec backend mypy backend/

migrate:
	docker-compose exec backend python -c "from db.migrations import run_migrations; import asyncio; asyncio.run(run_migrations())"

install:
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker-compose up -d backend mongo mongo-express
	cd frontend && npm run dev

stop:
	docker-compose stop

restart: down up

clean:
	docker-compose down -v
	docker system prune -af

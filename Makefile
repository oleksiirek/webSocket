# WebSocket Notification Server Makefile

.PHONY: help install dev prod test lint format clean docker-build docker-run docker-dev docker-stop logs

# Default target
help:
	@echo "WebSocket Notification Server - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     Install dependencies"
	@echo "  dev         Run development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo ""
	@echo "Production:"
	@echo "  prod        Run production server"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    Build Docker image"
	@echo "  docker-run      Run with Docker Compose"
	@echo "  docker-dev      Run development with Docker Compose"
	@echo "  docker-stop     Stop Docker containers"
	@echo "  logs            Show Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       Clean up temporary files"
	@echo "  deps-check  Check dependencies"

# Development commands
install:
	pip install -r requirements.txt
	pip install -e .

dev:
	python main.py --dev

prod:
	python main.py --prod

test:
	pytest tests/ -v --cov=websocket_server --cov-report=html --cov-report=term

lint:
	ruff check websocket_server/ tests/
	mypy websocket_server/

format:
	black websocket_server/ tests/ main.py
	ruff --fix websocket_server/ tests/

# Docker commands
docker-build:
	docker build -t webSocket .

docker-run:
	docker-compose up -d

docker-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

docker-stop:
	docker-compose down

docker-clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

logs:
	docker-compose logs -f websocket-server

# Monitoring
docker-monitoring:
	docker-compose --profile monitoring up -d

# Production deployment
docker-prod:
	docker-compose --profile production up -d

# Utility commands
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

deps-check:
	python main.py --check-deps

info:
	python main.py --info

# Health checks
health:
	curl -f http://localhost:8000/health || echo "Server not responding"

metrics:
	curl -s http://localhost:8000/metrics | jq .

# Load testing (requires wrk or similar tool)
load-test:
	@echo "Running basic load test..."
	@echo "Install wrk for load testing: https://github.com/wg/wrk"
	# wrk -t12 -c400 -d30s http://localhost:8000/health

# Setup development environment
setup-dev: install
	pre-commit install
	@echo "Development environment setup complete!"

# Build and push Docker image (for CI/CD)
docker-release: docker-build
	docker tag webSocket:latest webSocket:$(VERSION)
	# docker push webSocket:$(VERSION)
	# docker push webSocket:latest
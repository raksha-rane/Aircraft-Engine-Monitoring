# Makefile for Aircraft Engine Monitoring Project

.PHONY: help install test lint format clean docker-up docker-down health-check

# Default target
help:
	@echo "Aircraft Engine Monitoring - Available Commands:"
	@echo ""
	@echo "  install      Install Python dependencies"
	@echo "  test         Run all tests"
	@echo "  test-unit    Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  lint         Run code linting"
	@echo "  format       Format code with black"
	@echo "  health-check Run system health checks"
	@echo "  docker-up    Start all Docker services"
	@echo "  docker-down  Stop all Docker services"
	@echo "  docker-test  Start test environment"
	@echo "  clean        Clean up temporary files"
	@echo "  setup-env    Setup development environment"

# Python environment setup
install:
	pip install -r requirements.txt

setup-env:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Environment setup complete. Activate with: source venv/bin/activate"

# Testing
test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/ -v -m "unit"

test-integration:
	python -m pytest tests/ -v -m "integration"

test-ml:
	python -m pytest tests/ -v -m "ml"

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 src/ tests/
	@echo "Linting complete"

format:
	black src/ tests/ scripts/
	@echo "Code formatting complete"

# Docker operations
docker-up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	sleep 10
	@make health-check

docker-down:
	docker-compose down

docker-test:
	docker-compose -f docker-compose.test.yml up -d
	@echo "Test environment started"

docker-clean:
	docker-compose down -v
	docker system prune -f

# Health checks
health-check:
	python scripts/health_check.py

# Data operations
generate-data:
	python src/data_simulator.py

train-models:
	python src/ml_models.py

# Service operations
start-producer:
	python src/kafka_producer.py

start-consumer:
	python src/kafka_consumer.py

start-dashboard:
	streamlit run src/dashboard.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# CI/CD related
ci-setup:
	@make install
	@make docker-up

ci-test:
	@make test
	@make health-check

ci-deploy:
	@echo "Deployment steps would go here"

# Development helpers
dev-setup: setup-env docker-up
	@echo "Development environment ready!"
	@echo "Run 'make start-producer' in one terminal"
	@echo "Run 'make start-consumer' in another terminal"
	@echo "Run 'make start-dashboard' to view the dashboard"

quick-start: docker-up generate-data train-models
	@echo "Quick start complete! System is ready for use."

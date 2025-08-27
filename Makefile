.PHONY: help install lint format clean run build docker-build docker-run docker-stop encrypt test-encryption

# Default target
help:
	@echo "Affixio Engine - Available commands:"
	@echo "  install         - Install dependencies"
	@echo "  lint            - Run linting"
	@echo "  format          - Format code"
	@echo "  clean           - Clean build artifacts"
	@echo "  run             - Run the application"
	@echo "  build           - Build Docker image"
	@echo "  docker-run      - Run with Docker Compose"
	@echo "  docker-stop     - Stop Docker Compose"
	@echo "  docker-clean    - Clean Docker containers and images"
	@echo "  encrypt         - Encrypt all source files"
	@echo "  test-encryption - Test encryption system"

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev: install
	pip install black isort flake8 mypy

# Run linting
lint:
	flake8 src/
	mypy src/

# Format code
format:
	black src/
	isort src/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf logs/
	rm -f *.log

# Run the application
run:
	export AFFIXIO_JWT_SECRET="your-super-secret-jwt-key-that-is-at-least-32-characters-long" && \
	export AFFIXIO_HOST="0.0.0.0" && \
	export AFFIXIO_PORT="8000" && \
	python launcher.py

# Build Docker image
build:
	docker build -f docker/Dockerfile -t affixio-engine .

# Run with Docker Compose
docker-run:
	docker-compose -f docker/docker-compose.yml up --build

# Run with Docker Compose in background
docker-run-bg:
	docker-compose -f docker/docker-compose.yml up --build -d

# Stop Docker Compose
docker-stop:
	docker-compose -f docker/docker-compose.yml down

# Clean Docker containers and images
docker-clean:
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f
	docker image prune -f

# Security scan
security-scan:
	bandit -r src/
	safety check

# Generate documentation
docs:
	pydoc-markdown --render-toc --output-file README_API.md src/

# Check dependencies for updates
check-updates:
	pip list --outdated

# Update dependencies
update-deps:
	pip install --upgrade -r requirements.txt

# Create virtual environment
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Setup development environment
setup-dev: venv
	@echo "Activating virtual environment and installing dependencies..."
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Development environment setup complete!"

# Encrypt source code
encrypt:
	@echo "Encrypting source code..."
	python encrypt_source.py

# Test encryption system
test-encryption:
	@echo "Testing encryption system..."
	python test_encryption.py

# Production deployment check
prod-check:
	@echo "Checking production readiness..."
	@echo "✓ Running linting..."
	make lint
	@echo "✓ Running security scan..."
	make security-scan
	@echo "✓ Testing encryption system..."
	make test-encryption
	@echo "✓ Building Docker image..."
	make build
	@echo "✓ Production check complete!"

# Quick start (install, run)
quick-start: install run

# Development workflow
dev: format lint run

# Secure deployment (encrypt and run)
secure-deploy: encrypt run


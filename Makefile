.PHONY: install dev run migrate seed test lint format clean

# Install dependencies
install:
	pip install -r requirements.txt

# Install dev dependencies
dev:
	pip install -r requirements.txt
	pip install black ruff mypy pytest pytest-asyncio

# Run development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
run-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Database migrations
migrate:
	alembic upgrade head

# Create new migration
migration:
	alembic revision --autogenerate -m "$(m)"

# Seed database
seed:
	python -m scripts.seed_data

# Run tests
test:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=html

# Lint code
lint:
	ruff check app/

# Format code
format:
	black app/
	ruff check app/ --fix

# Type check
typecheck:
	mypy app/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".ruff_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf htmlcov/

# Docker commands
docker-build:
	docker build -t avto-laif-backend .

docker-run:
	docker run -p 8000:8000 avto-laif-backend

# Database reset (development only!)
db-reset:
	dropdb avto_laif --if-exists
	createdb avto_laif
	alembic upgrade head
	python -m scripts.seed_data

# Generate OpenAPI schema
openapi:
	python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json


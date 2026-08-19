.PHONY: dev test lint clean docker-up docker-down install

# Local development
install:
	pip install -r backend/requirements.txt
	pip install -r backend/requirements-dev.txt

dev:
	docker-compose up -d neo4j
	uvicorn backend.app.main:app --reload --port 8000

test:
	pytest backend/tests/ -v

lint:
	ruff check backend/
	ruff format --check backend/

format:
	ruff format backend/

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

# Utilities
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

health:
	curl -s http://localhost:8000/health | python -m json.tool

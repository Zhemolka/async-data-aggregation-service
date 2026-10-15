.PHONY: up down logs test lint

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f app worker

test:
	pytest -q

lint:
	ruff check .

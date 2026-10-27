.PHONY: install run test lint format docker

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt

run:
	python app.py

test:
	pytest --cov

lint:
	ruff check . && ruff format --check .

format:
	ruff check . --fix && ruff format .

docker:
	docker compose up --build

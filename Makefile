.PHONY: up down logs health run

up:            ## start redis + api
	docker compose up -d --build

down:          ## stop everything
	docker compose down -v

logs:
	docker compose logs -f

health:
	@curl -fsS http://localhost:8000/health && echo

run:           ## one happy-path run, report to stdout
	docker compose exec api python -m scripts.run_pipeline

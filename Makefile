.PHONY: up down logs health

up:            ## start redis + api
	docker compose up -d --build

down:          ## stop everything
	docker compose down -v

logs:
	docker compose logs -f

health:
	@curl -fsS http://localhost:8000/health && echo

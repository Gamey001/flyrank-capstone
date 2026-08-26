.PHONY: up down logs health sandbox clean

up:            ## start redis + api
	docker compose up -d --build

down:          ## stop everything
	docker compose down -v

logs:
	docker compose logs -f

health:
	@curl -fsS http://localhost:8000/health && echo

sandbox:       ## build the sealed box the generated code runs in
	docker build -f docker/sandbox.Dockerfile -t flyrank-sandbox:latest .

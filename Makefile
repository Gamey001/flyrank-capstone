HOST_PY := /usr/bin/python3
VENV    := .venv-host

.PHONY: up down logs health sandbox host-venv worker run crash swallowed trace quarantine test clean

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

host-venv:     ## the host observer's dependencies — deliberately tiny
	$(HOST_PY) -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -r requirements-host.txt

worker: host-venv sandbox   ## run the host observer, ON THE HOST, not in a container
	$(VENV)/bin/python -m app.worker.main

run:           ## a healthy run
	@$(HOST_PY) scripts/run.py --scenario healthy

crash:         ## a run that dies with 137, to prove the host catches it
	@$(HOST_PY) scripts/run.py --scenario oom

swallowed:     ## a run that exits 0 and ships nothing — caught by the gate
	@$(HOST_PY) scripts/run.py --scenario swallowed

trace:         ## paste one id: make trace ID=<trace-id>
	@$(HOST_PY) scripts/trace.py $(ID)

quarantine:    ## what is being held back
	@curl -fsS http://localhost:8000/quarantine

test:          ## unit tests + the real 137
	@$(VENV)/bin/python -m pytest tests/ -q

clean:
	rm -rf $(VENV)

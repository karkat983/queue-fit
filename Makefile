# Common tasks. Run `make help` for a list.
PYTHON ?= python3
WORKERS ?= 4

.PHONY: help setup up down health sweep lint test clean

help:            ## list targets
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

setup:           ## create .venv and install Python dependencies
	$(PYTHON) -m venv .venv && .venv/bin/pip install -r requirements.txt

up:              ## build and start the target service with $(WORKERS) workers
	WORKERS=$(WORKERS) docker compose up -d --build
	scripts/healthcheck.sh

down:            ## stop the target service
	docker compose down

health:          ## check the service answers
	scripts/healthcheck.sh

sweep: health    ## run the k6 rate sweep from config.yaml
	$(PYTHON) scripts/sweep.py

lint:            ## ruff lint
	$(PYTHON) -m ruff check .

test:            ## run unit tests
	$(PYTHON) -m pytest -q

clean:           ## delete raw run outputs
	rm -rf results/raw

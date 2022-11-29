include .env
export

CASES ?= .
MIG_MESSAGE ?=
DOCKER_PROJECT_ROOT_FROM_CTX ?= ../Deluge-Control
DOCKER_CTX_FROM_PYTHON_DOCKER ?= ..
DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT ?= ../Python-Docker
ifndef WATCH_DOCKER
WATCH_DOCKER = -d
endif

# Alembic
migrations: import-env-vars
	cd src;	alembic revision --autogenerate -m "$(MIG_MESSAGE)"

migrate: import-env-vars
	cd src; alembic upgrade head

# Docker
	cd $(DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT); DOCKER_REGISTRY=$(DOCKER_REGISTRY) make build-base-image




import-env-vars:
	set -a
	. ./.env
	set +a


# Python
run: import-env-vars
	cd src; python3 main.py

test: import-env-vars
	pytest $(CASES) 
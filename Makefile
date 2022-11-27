include .env
export

CASES ?= .
MIG_MESSAGE ?=
DOCKER_TAG_VERSION ?=
ifndef WATCH_DOCKER
WATCH_DOCKER = -d
endif

# Alembic
migrations: import-env-vars
	cd src;	alembic revision --autogenerate -m "$(MIG_MESSAGE)"

migrate: import-env-vars
	cd src; alembic upgrade head

# Docker
build-docker-base:
	DOCKER_BUILDKIT=1 docker build -t docker.funkybrows.com/deluge-control:$(DOCKER_TAG_VERSION) --ssh default=$(HOME)/.ssh/id_rsa -f src/config/docker/Dockerfile.base .
deploy-docker-base:
	docker compose -f src/config/docker/docker-compose.base.yaml up $(WATCH_DOCKER)
teardown-docker-base:
	docker compose -f src/config/docker/docker-compose.base.yaml down




import-env-vars:
	set -a
	. ./.env
	set +a


# Python
run: import-env-vars
	cd src; python3 main.py

test: import-env-vars
	pytest $(CASES) 
CASES ?= .
MIG_MESSAGE ?=
DOCKER_TAG_VERSION ?= 1.0.0
ifndef WATCH_DOCKER
WATCH_DOCKER = -d
endif
DOCKER_NAMESPACE ?= production
DOCKER_BASE_IMG ?= docker.funkybrows.com/deluge-control/base:$(DOCKER_TAG_VERSION)

# Alembic
migrations: import-env-vars
	cd src;	alembic revision --autogenerate -m "$(MIG_MESSAGE)"

migrate: import-env-vars
	cd src; alembic upgrade head

# Docker
build-docker:
	DOCKER_BUILDKIT=1 docker build --build-arg BASE_IMG=$(DOCKER_BASE_IMG) -t docker.funkybrows.com/deluge-control/$(DOCKER_NAMESPACE):$(DOCKER_TAG_VERSION) --ssh default=$(HOME)/.ssh/id_rsa -f src/config/docker/Dockerfile.$(DOCKER_NAMESPACE) .
deploy-docker:
	docker compose -f src/config/docker/docker-compose.$(DOCKER_NAMESPACE).yaml up $(WATCH_DOCKER)
teardown-docker:
	docker compose -f src/config/docker/docker-compose.$(DOCKER_NAMESPACE).yaml down



# Python
run:
	cd src; python3 main.py

test:
	pytest $(CASES) 
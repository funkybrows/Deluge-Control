include .env
export

CASES ?= .
MIG_MESSAGE ?=
DOCKER_APP_DEST ?= /app
DOCKER_PROJECT_ROOT_FROM_CTX ?= ../Deluge-Control
DOCKER_CTX_FROM_PYTHON_DOCKER ?= ..
DOCKER_TAG_VERSION ?= latest
DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT ?= ../Python-Docker
ifndef WATCH_DOCKER
DOCKER_NO_WATCH = -d
endif
DOCKER_REGISTRY ?=
NAMESPACE ?=
PROJECT_NAME ?=

# Alembic
migrations: import-env-vars
	cd src;	alembic revision --autogenerate -m "$(MIG_MESSAGE)"

migrate: import-env-vars
	cd src; alembic upgrade head

# Docker
build-base-image:
	cd $(DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT); DOCKER_REGISTRY=$(DOCKER_REGISTRY) make build-base-image

build-project:
	cd $(DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT); \
		DOCKER_APP_DEST=$(DOCKER_APP_DEST) \
		DOCKER_APP_SOURCE_FROM_CTX=$(DOCKER_PROJECT_ROOT_FROM_CTX) \
		DOCKER_COMMON_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/.env \
		DOCKER_CTX=$(DOCKER_CTX_FROM_PYTHON_DOCKER) \
		DOCKER_PROJECT_ROOT_FROM_CTX=$(DOCKER_PROJECT_ROOT_FROM_CTX) \
		DOCKER_SPECIFIC_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/$(NAMESPACE).env \
		DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
		NAMESPACE=$(NAMESPACE) \
		PROJECT_NAME=$(PROJECT_NAME) \
		make build-project

deploy-project:
	cd $(DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT); \
		DOCKER_APP_DEST=$(DOCKER_APP_DEST) \
		DOCKER_COMMON_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/.env \
		DOCKER_NO_WATCH=$(DOCKER_NO_WATCH) \
		DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
		DOCKER_PROJECT_ROOT_FROM_CTX=$(DOCKER_PROJECT_ROOT_FROM_CTX) \
		DOCKER_SPECIFIC_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/$(NAMESPACE).env \
		DOCKER_TAG_VERSION=$(DOCKER_TAG_VERSION) \
		NAMESPACE=$(NAMESPACE) \
		PROJECT_NAME=$(PROJECT_NAME) \
	make deploy-project

teardown-project:
	cd $(DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT); \
		DOCKER_COMMON_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/.env \
		DOCKER_SPECIFIC_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/$(NAMESPACE).env \
		make teardown-project


# Python
run:
	cd src; python3 main.py

test:
	pytest $(CASES) 
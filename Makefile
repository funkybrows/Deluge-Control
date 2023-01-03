ifdef DOCKER_COMMON_ENV_PATH
include $(DOCKER_COMMON_ENV_PATH)
endif

ifdef DOCKER_SPECIFIC_ENV_PATH
include $(DOCKER_SPECIFIC_ENV_PATH)
endif
export

CASES ?= .
MIG_MESSAGE ?=
CONFIG_FOLDER_PATH ?=
DOCKER_APP_DEST ?= /app
DOCKER_APP_SOURCE_FROM_COMPOSE ?=
DOCKER_CTX_FROM_PYTHON_DOCKER ?= ..
DOCKER_LOCAL_CMD ?= /bin/bash
DOCKER_PROJECT_ROOT_FROM_CTX ?= ../Deluge-Control
DOCKER_TAG_VERSION ?= latest
DOCKER_POSTGRES_SCRIPTS_PATH_FROM_COMPOSE ?= ../scripts/postgres/base
DOCKER_PYTHON_DOCKER_FROM_PROJECT_ROOT ?= ../Python-Docker
ifndef DOCKER_WATCH
DOCKER_NO_WATCH = -d
endif
DOCKER_REGISTRY ?=
NAMESPACE ?=
PROJECT_NAME ?= deluge_control
RABBIT_EXCHANGE ?=

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
		CONFIG_FOLDER_PATH=${CONFIG_FOLDER_PATH} \
		DOCKER_APP_DEST=$(DOCKER_APP_DEST) \
		DOCKER_COMMON_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/.env \
		DOCKER_NO_WATCH=$(DOCKER_NO_WATCH) \
		DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
		DOCKER_POSTGRES_SCRIPTS_PATH_FROM_COMPOSE=$(DOCKER_POSTGRES_SCRIPTS_PATH_FROM_COMPOSE) \
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

launch-local-project:
	CONFIG_FOLDER_PATH=${CONFIG_FOLDER_PATH} \
	DOCKER_APP_DEST=${DOCKER_APP_DEST} \
	DOCKER_APP_SOURCE_FROM_COMPOSE=$(DOCKER_APP_SOURCE_FROM_COMPOSE) \
	DOCKER_POSTGRES_SCRIPTS_PATH_FROM_COMPOSE=$(DOCKER_POSTGRES_SCRIPTS_PATH_FROM_COMPOSE) \
	DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
	DOCKER_TAG_VERSION=$(DOCKER_TAG_VERSION) \
	DOCKER_USER_CONFIG_PATH_FROM_COMPOSE=$(DOCKER_USER_CONFIG_PATH_FROM_COMPOSE) \
	NAMESPACE=$(NAMESPACE) \
	PROJECT_NAME=$(PROJECT_NAME) \
	RABBIT_EXCHANGE=$(RABBIT_EXCHANGE) \
	docker compose \
		-f config/docker/compose/docker-compose.local.yaml \
		run -it deluge-control $(DOCKER_LOCAL_CMD)

# Python
run:
	cd src; python3 main.py

test:
	pytest $(CASES)

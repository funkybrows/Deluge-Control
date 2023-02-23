ifdef DOCKER_COMMON_ENV_PATH
include $(DOCKER_COMMON_ENV_PATH)
endif

ifdef DOCKER_SPECIFIC_ENV_PATH
include $(DOCKER_SPECIFIC_ENV_PATH)
endif
export


DOCKER_APP_DEST ?= /app
DOCKER_CTX_FROM_COMPOSE ?= ../../../..
DOCKER_CTX_FROM_PROJECT_ROOT ?=..
DOCKER_CTX_FROM_PYTHON_DOCKER ?= ..
DOCKER_ENTRYPOINT_DEST ?= /entrypoint.sh
DOCKER_LOCAL_CMD ?= /bin/bash
DOCKER_LOG_FOLDER_PATH ?= /root/.$(PROJECT_NAME)/logs
DOCKER_NO_CACHE ?=
DOCKER_POSTGRES_SCRIPTS_PATH_FROM_CTX ?= ../Deluge-Control/docker/config/scripts/postgres
DOCKER_PROJECT_ROOT_FROM_CTX ?= ../Deluge-Control
DOCKER_PROJECT_SERVICE_NAME ?= my-project
DOCKER_PYTHON_DOCKER_FROM_CTX ?= Python-Docker
DOCKER_REGISTRY ?= docker.example.com
DOCKER_TAG_VERSION ?= latest
DOCKER_WATCH ?= # Define with any value to display background deployment

DOCKER_APP_SOURCE_FROM_COMPOSE ?= $(DOCKER_CTX_FROM_COMPOSE)/$(DOCKER_PROJECT_ROOT_FROM_CTX)
DOCKER_COMPOSE_FILE ?= $(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/config/docker/compose/docker-compose.$(NAMESPACE).yaml
DOCKER_CONFIG_FOLDER_PATH ?= /root/.$(DOCKER_PROJECT_SERVICE_NAME)/config
DOCKER_ENTRYPOINT_SOURCE_FROM_CTX ?= $(DOCKER_PROJECT_ROOT_FROM_CTX)/config/docker/scripts/$(NAMESPACE)-entrypoint.sh
DOCKER_USER_CONFIG_PATH_FROM_CTX ?= $(DOCKER_PROJECT_ROOT_FROM_CTX)/config
DOCKER_USER_LOCAL_LOG_PATH_FROM_CTX ?= $(DOCKER_PROJECT_ROOT_FROM_CTX)/logs

CASES ?= .
CONFIG_FOLDER_PATH ?= config
DOCKER_CONFIG_FOLDER_PATH ?= /root/.$(PROJECT_NAME)/config
DEFAULT_DELUGE_HOST ?= 10.0.0.0
DEFAULT_DELUGE_PASSWORD ?= password
DEFAULT_DELUGE_PORT ?= 18000
DEFAULT_DELUGE_USERNAME ?= user
DELUGE_REMOTE_TESTS_ROOT_DIR ?= /home/my_user/tests
NAMESPACE ?=
PROJECT_NAME ?= deluge_control

MIG_MESSAGE ?=
PG_NAME ?= deluge_control
PG_USER ?= deluge_control_user
PG_PORT ?= 50001

AMQP_PORT ?= 50000
RABBIT_EXCHANGE ?= dev-rabbit
RABBITMQ_HOST ?= deluge-control-rabbitmq
RABBITMQ_USER ?= rabbit
REMOTE_BASE_DIR ?= /
REMOTE_SFTP_HOST ?= 10.0.0.1
REMOTE_SFTP_USER=user

# Alembic
migrations: import-env-vars
	cd src;	alembic revision --autogenerate -m "$(MIG_MESSAGE)"

migrate: import-env-vars
	cd src; alembic upgrade head

# Docker
build-base-image:
	cd $(DOCKER_CTX_FROM_PROJECT_ROOT)/$(DOCKER_PYTHON_DOCKER_FROM_CTX); DOCKER_REGISTRY=$(DOCKER_REGISTRY) make build-base-image

build-project:
	cd $(DOCKER_CTX_FROM_PROJECT_ROOT)/$(DOCKER_PYTHON_DOCKER_FROM_CTX); \
		DOCKER_APP_DEST=$(DOCKER_APP_DEST) \
		DOCKER_CONFIG_FOLDER_PATH=$(DOCKER_CONFIG_FOLDER_PATH) \
		DOCKER_CTX_FROM_PYTHON_DOCKER=$(DOCKER_CTX_FROM_PYTHON_DOCKER) \
		DOCKER_ENTRYPOINT_DEST=$(DOCKER_ENTRYPOINT_DEST) \
		DOCKER_ENTRYPOINT_SOURCE_FROM_CTX=$(DOCKER_ENTRYPOINT_SOURCE_FROM_CTX) \
		DOCKER_LOG_FOLDER_PATH=$(DOCKER_LOG_FOLDER_PATH) \
		DOCKER_NO_CACHE=$(DOCKER_NO_CACHE) \
		DOCKER_PROJECT_ROOT_FROM_CTX=$(DOCKER_PROJECT_ROOT_FROM_CTX) \
		DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
		DOCKER_TAG_VERSION=$(DOCKER_TAG_VERSION) \
		DOCKER_USER_CONFIG_PATH_FROM_CTX=$(DOCKER_USER_CONFIG_PATH_FROM_CTX) \
		NAMESPACE=$(NAMESPACE) \
		PROJECT_NAME=$(PROJECT_NAME) \
		make build-project

deploy-project:
	cd $(DOCKER_CTX_FROM_PROJECT_ROOT)/$(DOCKER_PYTHON_DOCKER_FROM_CTX); \
		CONFIG_FOLDER_PATH=${CONFIG_FOLDER_PATH} \
		DOCKER_APP_DEST=$(DOCKER_APP_DEST) \
		DOCKER_COMMON_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/.env \
		DOCKER_NO_WATCH=$(DOCKER_NO_WATCH) \
		DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
		DOCKER_POSTGRES_SCRIPTS_PATH_FROM_CTX=$(DOCKER_POSTGRES_SCRIPTS_PATH_FROM_CTX=$(DOCKER_POSTGRES_SCRIPTS_PATH_FROM_CTX)) \
		DOCKER_PROJECT_ROOT_FROM_CTX=$(DOCKER_PROJECT_ROOT_FROM_CTX) \
		DOCKER_SPECIFIC_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/$(NAMESPACE).env \
		DOCKER_TAG_VERSION=$(DOCKER_TAG_VERSION) \
		NAMESPACE=$(NAMESPACE) \
		PROJECT_NAME=$(PROJECT_NAME) \
	make deploy-project

teardown-project:
	cd $(DOCKER_CTX_FROM_PROJECT_ROOT)/$(DOCKER_PYTHON_DOCKER_FROM_CTX); \
		DOCKER_COMMON_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/.env \
		DOCKER_SPECIFIC_ENV_PATH=$(DOCKER_CTX_FROM_PYTHON_DOCKER)/$(DOCKER_PROJECT_ROOT_FROM_CTX)/src/config/docker/env/$(NAMESPACE).env \
		make teardown-project

launch-local-project:
	DOCKER_APP_DEST=${DOCKER_APP_DEST} \
	DOCKER_APP_SOURCE_FROM_COMPOSE=$(DOCKER_APP_SOURCE_FROM_COMPOSE) \
	DOCKER_CONFIG_FOLDER_PATH=$(DOCKER_CONFIG_FOLDER_PATH) \
	DOCKER_CTX_FROM_COMPOSE=$(DOCKER_CTX_FROM_COMPOSE) \
	DOCKER_POSTGRES_SCRIPTS_PATH_FROM_CTX=$(DOCKER_POSTGRES_SCRIPTS_PATH_FROM_CTX)
	DOCKER_LOG_FOLDER_PATH=$(DOCKER_LOG_FOLDER_PATH) \
	DOCKER_REGISTRY=$(DOCKER_REGISTRY) \
	DOCKER_TAG_VERSION=$(DOCKER_TAG_VERSION) \
	DOCKER_USER_CONFIG_PATH_FROM_CTX=${DOCKER_USER_CONFIG_PATH_FROM_CTX} \
	DOCKER_USER_LOCAL_LOG_PATH_FROM_CTX=${DOCKER_USER_LOCAL_LOG_PATH_FROM_CTX} \
	NAMESPACE=$(NAMESPACE) \
	PROJECT_NAME=$(PROJECT_NAME) \
	docker compose \
		-f config/docker/compose/docker-compose.local.yaml \
		run -it ${DOCKER_PROJECT_SERVICE_NAME} $(DOCKER_LOCAL_CMD)

# Python
run:
	cd src; python3 main.py

test:
	pytest $(CASES) 

# SSH
create-known-hosts:
	rm -f $(CONFIG_FOLDER_PATH)/.ssh/known_hosts
	mkdir -p $(CONFIG_FOLDER_PATH)/.ssh
	ssh-keyscan -H $(REMOTE_SFTP_HOST) >> $(CONFIG_FOLDER_PATH)/.ssh/known_hosts

copy-rsa-key:
	mkdir -p $(CONFIG_FOLDER_PATH)/.ssh
	if ! [ -r $(CONFIG_FOLDER_PATH)/.ssh/id_rsa ]; then \
		ssh-keygen -f $(CONFIG_FOLDER_PATH)/.ssh/id_rsa; \
	fi
	ssh-copy-id -i $(CONFIG_FOLDER_PATH)/.ssh/id_rsa $(REMOTE_SFTP_USER)@$(REMOTE_SFTP_HOST)

include .env
export

CASES ?= .
MIG_MESSAGE ?=
# Alembic
migrations: import-env-vars
	cd src;	alembic revision --autogenerate -m "$(MIG_MESSAGE)"

migrate: import-env-vars
	cd src; alembic upgrade head





import-env-vars:
	set -a
	. ./.env
	set +a


# Python
run: import-env-vars
	cd src; python3 main.py

test: import-env-vars
	pytest $(CASES) 
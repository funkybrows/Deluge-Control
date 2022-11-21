include .env
export

CASES ?= .

create-db-user:
	sudo adduser $(PG_USER); \
 	echo "\
		CREATE DATABASE $(PG_USER); \
		CREATE USER $(PG_USER); \
		ALTER USER $(PG_USER) password '$(PG_PASSWORD)'; \
		ALTER USER $(PG_USER) CREATEDB;" | sudo -u postgres psql;

create-test-db-user:
	sudo adduser $(PG_TEST_USER); \
	echo "\
		CREATE DATABASE $(PG_TEST_USER); \
		CREATE USER $(PG_TEST_USER); \
		ALTER USER $(PG_TEST_USER) password '$(PG_TEST_PASSWORD)'; \
		ALTER USER $(PG_TEST_USER) CREATEDB;" | sudo -u postgres psql;

create-postgres-db:
	echo "\
		CREATE DATABASE $(PG_NAME) \
			with OWNER = $(PG_USER);" | sudo -u postgres psql;

create-test-postgres-db:
	echo "\
		CREATE DATABASE $(PG_TEST_NAME) \
			with OWNER = $(PG_TEST_USER);" | sudo -u postgres psql;

drop-postgres-db:
	echo "DROP DATABASE IF EXISTS $(PG_NAME);" | sudo -u postgres psql;

drop-test-postgres-db:
	echo "DROP DATABASE IF EXISTS $(PG_TEST_NAME);" | sudo -u postgres psql;

reset-postgres: drop-postgres-db create-postgres-db

reset-test-postgres: drop-test-postgres-db create-test-postgres-db

test:
	set -a;
	. ./.env
	set +a
	pytest $(CASES) 
#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	CREATE DATABASE "test-${PG_NAME}" \
        with OWNER=$POSTGRES_USER;
EOSQL

#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 --username "$PG_USER" <<-EOSQL
	CREATE DATABASE deluge_control \
        with OWNER=$PG_USER;
EOSQL

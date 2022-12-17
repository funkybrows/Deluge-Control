#!/bin/bash
set -eu

cd /app/src;
alembic upgrade head;
cd /app;
poetry install;

exec "$@"

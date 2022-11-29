#!/bin/bash
set -eu

cd /app/src;
alembic upgrade head;

exec "$@"

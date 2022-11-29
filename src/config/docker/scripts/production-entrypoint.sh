#!/bin/bash

set -eu
exec "$@"

cd /app/src;
alembic upgrade head;
python main.py
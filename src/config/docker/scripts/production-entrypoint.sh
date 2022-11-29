#!/bin/bash

cd /app/src;
alembic upgrade head;
python main.py
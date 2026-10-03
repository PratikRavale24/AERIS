#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || true

echo "Seeding the database with synthetic data..."
python -m app.db.seed --all || true

echo "Starting FastAPI backend server..."
exec "$@"

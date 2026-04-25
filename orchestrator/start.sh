#!/bin/bash
set -e

echo "--- Orchestrator Startup ---"

# 1. Wait for Postgres (Adjust DB_HOST as needed in docker-compose)
echo "Waiting for Database..."
while ! nc -z $DB_HOST 5432; do
  sleep 0.5
done
echo "Database is ready!"

# 2. Run Migrations
echo "Applying database migrations..."
uv run alembic upgrade head

# 3. Launch the Service
# Use 'python -m' to ensure imports work correctly in the monorepo
echo "Launching Orchestrator..."
exec uv run python -m orchestrator.main
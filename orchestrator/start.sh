#!/bin/bash
set -e

echo "--- Orchestrator Startup ---"

# 1. Wait for Postgres
echo "Waiting for Database at $DB_HOST:$DB_PORT..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done
echo "✓ Database is ready!"

# 2. Wait for Redis (required for Pub/Sub and result processing)
echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 0.5
done
echo "✓ Redis is ready!"

# 3. Run Migrations
echo "Applying database migrations to $POSTGRES_DB..."
uv run alembic -c orchestrator/alembic.ini upgrade head

# 4. Launch the Service
echo "Launching Orchestrator on port $PORT..."
exec uv run python -m orchestrator.main

#!/bin/bash
set -e

echo "--- Auth Startup ---"

# 1. Wait for Postgres
echo "Waiting for Database at $DB_HOST:$DB_PORT..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done
echo "✓ Database is ready!"

# 2. Run Migrations
echo "Applying database migrations to $POSTGRES_DB..."
uv run alembic -c auth/alembic.ini upgrade head

# 3. Launch the Service
echo "Launching Auth service on port $PORT..."
exec uv run python -m auth.main

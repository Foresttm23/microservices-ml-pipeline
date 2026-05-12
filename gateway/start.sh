#!/bin/bash
set -e

echo "--- Gateway Startup ---"

# 1. Wait for Redis (required for WebSocket pub/sub bridge)
echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 0.5
done
echo "✓ Redis is ready!"

# 2. Launch the Service
echo "Launching Gateway on port $PORT..."
exec uv run python -m gateway.main

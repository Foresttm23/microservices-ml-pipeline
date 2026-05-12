#!/bin/bash
set -e

echo "--- ML Worker Startup ---"

# 1. Wait for Message Broker (e.g., Redis on 6379)
echo "Waiting for Message Broker at $REDIS_HOST:$REDIS_PORT..."
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 0.5
done
echo "✓ Message Broker is ready!"

# 2. Launch the Worker
echo "Launching ML Worker (DRY_RUN=$ML_WORKER_DRY_RUN)..."
exec uv run python -m ml_worker.main

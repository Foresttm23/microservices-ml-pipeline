#!/bin/bash
set -e

echo "--- ML Worker Startup ---"

# 1. Wait for Message Broker (e.g., Redis on 6379)
echo "Waiting for Message Broker..."
while ! nc -z $REDIS_HOST 6379; do
  sleep 0.5
done
echo "Broker is ready!"

# 2. Launch the Worker
echo "Launching ML Worker..."
exec uv run python -m ml_worker.main
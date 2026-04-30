#!/bin/bash
set -e

echo "--- Gateway Startup ---"

# Gateway usually doesn't wait for anything, but you could
# add a check here to ensure the Orchestrator is up first.

echo "Launching Gateway..."
exec uv run python -m gateway.main

#!/bin/sh
set -e

# We can optionally wait for gateway if we want, but since this is just static serving, it's fine.
echo "Starting frontend server..."
uv run python -m frontend.main

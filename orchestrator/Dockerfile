# --- Stage 1: Builder ---
FROM ghcr.io/astral-sh/uv:0.10.9 AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY orchestrator/ ./orchestrator/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Stage 2: Runtime ---
FROM python:3.12-slim
# Install 'netcat' so start.sh can ping the DB/Queue
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy orchestrator code and start script
COPY orchestrator/ ./orchestrator/
RUN chmod +x orchestrator/start.sh

# Entrypoint uses the script
ENTRYPOINT ["orchestrator/start.sh"]
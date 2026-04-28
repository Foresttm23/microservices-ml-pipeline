# --- Stage 1: Builder ---
FROM ghcr.io/astral-sh/uv:0.10.9 AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY gateway/pyproject.toml ./gateway/pyproject.toml
COPY ml_worker/pyproject.toml ./ml_worker/pyproject.toml
COPY orchestrator/pyproject.toml ./orchestrator/pyproject.toml
COPY shared/pyproject.toml ./shared/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-packages --no-install-project --no-dev

COPY ml_worker/ ./ml_worker/
COPY shared/ ./shared/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-packages --no-dev && \
    uv pip install -e ./shared

# --- Stage 2: Runtime ---
FROM python:3.13.5-slim

# ML libraries often need libgomp for parallel processing
RUN apt-get update && apt-get install -y libgomp1 netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the worker code and models
COPY ml_worker/ ./ml_worker/
COPY shared/ ./shared/
RUN chmod +x ml_worker/start.sh

ENTRYPOINT ["ml_worker/start.sh"]
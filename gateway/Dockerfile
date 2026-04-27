# --- Stage 1: Build the environment ---
FROM ghcr.io/astral-sh/uv:0.10.9 AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Copy workspace dependency files
COPY pyproject.toml uv.lock ./
COPY gateway/pyproject.toml ./gateway/pyproject.toml
COPY ml_worker/pyproject.toml ./ml_worker/pyproject.toml
COPY orchestrator/pyproject.toml ./orchestrator/pyproject.toml
COPY shared/pyproject.toml ./shared/pyproject.toml
# Install dependencies (cached)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-packages --no-install-project --no-dev

# Copy workspace code needed to install and run the gateway
COPY gateway/ ./gateway/
COPY shared/ ./shared/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-packages --no-dev

# --- Stage 2: Runtime ---
FROM python:3.13.5-slim

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the actual gateway code
COPY gateway/ ./gateway/
COPY shared/ ./shared/

RUN chmod +x gateway/start.sh

ENTRYPOINT ["gateway/start.sh"]
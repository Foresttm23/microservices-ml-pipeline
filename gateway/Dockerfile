# --- Stage 1: Build the environment ---
FROM ghcr.io/astral-sh/uv:0.10.9 AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Copy root dependency files
COPY pyproject.toml uv.lock ./
# Install dependencies (cached)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy gateway-specific code
COPY gateway/ ./gateway/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Stage 2: Runtime ---
FROM python:3.13.5-slim

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the actual gateway code
COPY gateway/ ./gateway/

RUN chmod +x gateway/start.sh

ENTRYPOINT ["gateway/start.sh"]
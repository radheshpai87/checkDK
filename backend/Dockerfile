# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for better layer caching
COPY pyproject.toml .
COPY checkdk/__init__.py checkdk/__init__.py

# Install all dependencies (core + api + ml)
RUN pip install --no-cache-dir --upgrade pip \
        && pip install --no-cache-dir ".[api,ml]"

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy full application source
COPY checkdk/ checkdk/

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser \
        && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check so docker-compose / orchestrators know when the API is ready
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
        CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "checkdk.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

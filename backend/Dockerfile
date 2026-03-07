# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for better layer caching
# Build context must be the repo root (docker build -f backend/Dockerfile .)
COPY backend/pyproject.toml .
COPY backend/checkdk/__init__.py checkdk/__init__.py

# Install all dependencies (core + api + ml)
RUN pip install --no-cache-dir --upgrade pip \
        && pip install --no-cache-dir ".[api,ml]"

# ── Stage 1b: train ML model (separate layer so dataset isn't in final image) ──
FROM builder AS trainer

COPY ml-models/datasets/pod_failure_dataset.csv /tmp/dataset.csv
COPY backend/checkdk/ checkdk/

RUN CHECKDK_DATASET=/tmp/dataset.csv python -m checkdk.ml.train

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy full application source
COPY backend/checkdk/ checkdk/

# Bake trained model artifacts into the image (no dataset included)
COPY --from=trainer /app/checkdk/ml/artifacts/ checkdk/ml/artifacts/

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser \
        && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check so docker-compose / orchestrators know when the API is ready
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
        CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "checkdk.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

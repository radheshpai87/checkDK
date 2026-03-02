# ============================================================
# Pod Failure Detection – ML Models
# ============================================================
# Multi-stage Dockerfile with two named targets:
#
#   train  – installs deps and runs train_all.py
#   api    – serves the FastAPI inference server
#
# Usage (see docker-compose.yml for the easy path):
#   docker build --target train -t pod-failure-train .
#   docker build --target api   -t pod-failure-api   .
# ============================================================

# --------------- base stage ---------------------------------
FROM python:3.11-slim AS base

# Build arg: set to https://download.pytorch.org/whl/cu121 for CUDA GPUs
#            or  https://download.pytorch.org/whl/cu118 for older CUDA
#            defaults to CPU-only (small image)
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install torch first with the correct backend, then the rest of deps
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url ${TORCH_INDEX_URL} \
 && pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# --------------- train stage --------------------------------
FROM base AS train

# Models are saved via bind-mount volumes (see docker-compose.yml).
# Run train_all.py then compare_models.py to produce comparison charts.
CMD ["python", "train_all.py"]

# --------------- api stage ----------------------------------
FROM base AS api

# Default port
EXPOSE 8000

# Entrypoint: start Uvicorn
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]

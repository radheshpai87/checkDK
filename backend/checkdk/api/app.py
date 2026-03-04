"""FastAPI application for checkDK."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.analyze import router as analyze_router
from .routes.predict import router as predict_router

app = FastAPI(
    title="checkDK API",
    description=(
        "AI-powered Docker/Kubernetes issue detector and pod failure predictor. "
        "Exposes the same analysis engine used by the checkdk CLI as a REST API."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_origins = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(analyze_router, prefix="/analyze", tags=["Analysis"])
app.include_router(predict_router, tags=["Prediction"])


@app.get("/health", tags=["Health"])
async def health():
    """Liveness probe – returns 200 when the service is up."""
    return {"status": "ok"}

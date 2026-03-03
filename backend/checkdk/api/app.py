"""FastAPI application for checkDK."""

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
# In production, replace "*" with your frontend origin, e.g.
# allow_origins=["https://checkdk.example.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

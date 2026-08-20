from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine

from app.api.matches import router as matches_router
from app.api.teams import router as teams_router
from app.api.leagues import router as leagues_router
from app.api.analytics import router as analytics_router
import app.models
from app.api.admin import router as admin_router

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)
from app.api.ml_analytics import (
    router as ml_analytics_router,
)
from app.routes.value_analytics import (
    router as value_analytics_router,
)

from fastapi.middleware.cors import CORSMiddleware
from app.api.analitiko import router as analitiko_router
# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Analitiko API",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CORS
# ============================================================




# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    matches_router
)

app.include_router(
    teams_router
)

app.include_router(
    leagues_router
)
app.include_router(analytics_router)

app.include_router(admin_router)

app.include_router(
    ml_analytics_router
)
app.include_router(
    value_analytics_router
)
app.include_router(
    analitiko_router
)
# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "app": "Analitiko",
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
    }
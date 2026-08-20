from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import (
    Base,
    engine,
)

# ============================================================
# IMPORT MODELS
#
# Important:
# Models must be imported before create_all()
# so SQLAlchemy knows all tables.
# ============================================================

import app.models


# ============================================================
# ROUTERS
# ============================================================

from app.api.matches import (
    router as matches_router,
)

from app.api.teams import (
    router as teams_router,
)

from app.api.leagues import (
    router as leagues_router,
)

from app.api.analytics import (
    router as analytics_router,
)

from app.api.admin import (
    router as admin_router,
)

from app.api.ml_analytics import (
    router as ml_analytics_router,
)

from app.routes.value_analytics import (
    router as value_analytics_router,
)

from app.api.analitiko import (
    router as analitiko_router,
)

from app.api.database_import import (
    router as database_import_router,
)


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
    description=(
        "Football intelligence, prediction, "
        "market analysis and ticket optimization API."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        # Vercel production URL will be
        # added here after frontend deployment.
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


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

app.include_router(
    analytics_router
)

app.include_router(
    admin_router
)

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
# TEMPORARY DATABASE IMPORT ROUTER
#
# REMOVE AFTER SQLITE -> POSTGRESQL MIGRATION.
# ============================================================

app.include_router(
    database_import_router,
    prefix="/api",
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "app":
            "Analitiko",

        "status":
            "running",

        "version":
            "0.1.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status":
            "ok",
    }
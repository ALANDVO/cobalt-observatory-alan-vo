"""
Cobalt Observatory - AI/ML Agent Trace Correlation Platform
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import health, ocsf_events, agents, evaluations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Cobalt Observatory",
        description="AI/ML Agent Trace Correlation and Evaluation Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(ocsf_events.router, prefix="/api/v1/ocsf", tags=["ocsf-events"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["evaluations"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
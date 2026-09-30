"""
FastAPI application entry point.

Registers all routers, configures CORS, exception handlers, and lifespan.
NLP models are NOT loaded at startup — they are lazy-loaded on first use.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    logger = get_logger("app.main")
    settings = get_settings()
    logger.info(
        "application_starting",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
    )

    # ---------------------------------------------------------
    # Auto-fix missing schema columns safely (bypass Alembic)
    # ---------------------------------------------------------
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE sentiment_results ADD COLUMN IF NOT EXISTS analysis_id INTEGER;"))
            await conn.execute(text("ALTER TABLE insights ADD COLUMN IF NOT EXISTS analysis_id INTEGER;"))
            await conn.execute(text("ALTER TABLE market_metrics ADD COLUMN IF NOT EXISTS analysis_id INTEGER;"))
        logger.info("schema_verified", message="Ensured analysis_id columns exist.")
    except Exception as e:
        logger.warning("schema_verification_failed", error=str(e))
    # ---------------------------------------------------------

    # Start scheduler in production
    if settings.is_production:
        from app.services.ingestion.scheduler import setup_scheduler, start_scheduler
        setup_scheduler()
        start_scheduler()

    yield

    # Shutdown
    logger.info("application_shutting_down")
    try:
        from app.services.ingestion.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="AI-Powered Competitive Intelligence Platform",
        description="Market trend prediction and competitive intelligence API",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger = get_logger("app.error")
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Register routes
    from app.api.routes.health import router as health_router
    from app.api.routes.companies import router as companies_router
    from app.api.routes.sources import router as sources_router
    from app.api.routes.competitors import router as competitors_router
    from app.api.routes.documents import router as documents_router
    from app.api.routes.analytics import router as analytics_router
    from app.api.routes.predictions import router as predictions_router
    from app.api.routes.insights import router as insights_router
    from app.api.routes.ingestion import router as ingestion_router
    from app.api.routes.system import router as system_router
    from app.api.routes.analysis import router as analysis_router
    from app.api.routes.reviews import router as reviews_router

    app.include_router(health_router, tags=["health"])
    app.include_router(companies_router)
    app.include_router(sources_router)
    app.include_router(competitors_router)
    app.include_router(documents_router)
    app.include_router(analytics_router)
    app.include_router(predictions_router)
    app.include_router(insights_router)
    app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["ingestion"])
    app.include_router(system_router)
    app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(reviews_router, prefix="/api/v1/reviews", tags=["reviews"])

    return app


app = create_app()

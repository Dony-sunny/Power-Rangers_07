import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.api.routes import router
from backend.api.intake import router as intake_router
from backend.api.optimization import router as optimization_router
from backend.api.operations import router as operations_router
from backend.api.demo import router as demo_router
from backend.api.providers import router as provider_router
from backend.api.scheduling import router as scheduling_router
from backend.api.evidence import router as evidence_router
from backend.api.admin import router as admin_router
from backend.api.analytics import router as analytics_router
from backend.api.judge import router as judge_router
from data.seed.network import initialize

logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app = FastAPI(
    title="Jalayatra AI",
    description="Agentic inland freight exchange. Demo operational data is simulated.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Demo-Role", "X-Demo-User"],
)
app.include_router(router)
app.include_router(intake_router)
app.include_router(optimization_router)
app.include_router(operations_router)
app.include_router(demo_router)
app.include_router(provider_router)
app.include_router(scheduling_router)
app.include_router(evidence_router)
app.include_router(admin_router)
app.include_router(analytics_router)
app.include_router(judge_router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, error: Exception):
    logging.getLogger("jalayatra").error(
        "Unhandled request failure: %s", type(error).__name__
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "The request could not be completed. Check server logs and retry."
        },
    )

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from forenchain.config import get_settings
from forenchain.infrastructure.api.middleware.request_id import RequestIDMiddleware
from forenchain.infrastructure.api.middleware.security_headers import SecurityHeadersMiddleware
from forenchain.infrastructure.api.v1.routers import health, evidence


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate secrets at startup — fails fast in production if defaults are set
    settings = get_settings()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ForenChain",
        description="Open forensic evidence chain-of-custody platform for Indian state agencies",
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Middleware — order matters: outer to inner
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Routers
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(evidence.router, prefix=prefix)

    return app


app = create_app()

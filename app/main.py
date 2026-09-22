"""
Ponto de entrada da aplicação FastAPI.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import app.db.models  # noqa: F401
from app.api.routes_admin import router as admin_router
from app.api.routes_auth import router as auth_router
from app.api.routes_dce import router as dce_router
from app.api.routes_login import router as login_router
from app.api.routes_sefaz import router as sefaz_router
from app.api.routes_web import router as web_router
from app.auth.db import init_auth_db
from app.auth.middleware import AuthMiddleware
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.base import Base
from app.db.session import get_engine

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("Tabelas do banco de dados verificadas/criadas com sucesso.")
    except Exception as exc:
        logger.warning("Não foi possível criar tabelas automaticamente via create_all: %s", exc)
    init_auth_db()
    yield


settings = get_settings()

app = FastAPI(
    title="Opendce",
    description=(
        "Sistema de emissão de Declaração de Conteúdo Eletrônica (modelo 99) — "
        "ASSOCIAÇÃO HOSPITAL DE CARIDADE IJUI"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(login_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(web_router)
app.include_router(dce_router)
app.include_router(sefaz_router)

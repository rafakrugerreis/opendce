"""
Middleware Starlette que protege rotas web redirecionando para login quando necessário.
"""

from __future__ import annotations

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.auth.security import decode_token

_EXCLUDED_EXACT = {
    "/login",
    "/logout",
    "/force-change-password",
    "/admin/login",
    "/admin/change-password",
}
_EXCLUDED_PREFIX = ("/api/", "/auth/", "/static/", "/docs", "/redoc", "/openapi.json", "/favicon")


def _valid_access_token(token: str | None, require_admin: bool = False) -> bool:
    if not token:
        return False
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return False
        if require_admin and not payload.get("is_admin"):
            return False
        return True
    except jwt.PyJWTError:
        return False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        path = request.url.path

        if any(path.startswith(p) for p in _EXCLUDED_PREFIX) or path in _EXCLUDED_EXACT:
            return await call_next(request)  # type: ignore[operator]

        # API calls (Bearer header or JSON accept) → let route deps handle auth
        if request.headers.get("authorization") or "application/json" in request.headers.get(
            "accept", ""
        ):
            return await call_next(request)  # type: ignore[operator]

        if path.startswith("/admin"):
            token = request.cookies.get("admin_token") or request.cookies.get("access_token")
            if not _valid_access_token(token, require_admin=True):
                return RedirectResponse("/admin/login", status_code=302)
            return await call_next(request)  # type: ignore[operator]

        token = request.cookies.get("access_token")
        if not _valid_access_token(token):
            return RedirectResponse("/login", status_code=302)
        return await call_next(request)  # type: ignore[operator]

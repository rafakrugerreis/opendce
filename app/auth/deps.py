"""
Dependências FastAPI para extração e validação de usuário autenticado.
"""

from __future__ import annotations

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.db import get_auth_db
from app.auth.models import Usuario
from app.auth.repository import UsuarioRepository
from app.auth.security import decode_token


def _extract_token(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
    admin_token: str | None = Cookie(default=None),
) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ")
    return access_token or admin_token


def get_current_user(
    db: Session = Depends(get_auth_db),
    token: str | None = Depends(_extract_token),
) -> Usuario:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("wrong type")
        user_id: int = payload["user_id"]
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = UsuarioRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")
    return user


def get_optional_current_user(
    db: Session = Depends(get_auth_db),
    token: str | None = Depends(_extract_token),
) -> Usuario | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id: int = payload["user_id"]
        user = UsuarioRepository(db).get_by_id(user_id)
        if user and user.is_active:
            return user
    except Exception:
        pass
    return None


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito")
    return user

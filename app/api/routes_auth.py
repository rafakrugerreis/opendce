"""
Endpoints REST de autenticação: login JSON, refresh de token e perfil.
"""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.db import get_auth_db
from app.auth.deps import get_current_user
from app.auth.models import Usuario
from app.auth.repository import UsuarioRepository
from app.auth.security import create_access_token, create_refresh_token, decode_token, user_payload
from app.auth.service import UsuarioService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    cracha: str
    senha: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    password_changed: bool = True


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_auth_db)):
    user = UsuarioService(db).authenticate(body.cracha, body.senha)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas"
        )
    return TokenResponse(
        access_token=create_access_token(user_payload(user)),
        refresh_token=create_refresh_token(user.id),
        password_changed=user.password_changed,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_auth_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id: int = payload["user_id"]
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido"
        )
    user = UsuarioRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado"
        )
    return TokenResponse(
        access_token=create_access_token(user_payload(user)),
        refresh_token=create_refresh_token(user.id),
        password_changed=user.password_changed,
    )


@router.get("/me")
def me(user: Usuario = Depends(get_current_user)):
    return {
        "id": user.id,
        "nome": user.nome,
        "cracha": user.cracha,
        "email": user.email,
        "is_admin": user.is_admin,
        "password_changed": user.password_changed,
    }

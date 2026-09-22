"""
Emissão e validação de tokens JWT com PyJWT (HS256).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from app.auth.models import Usuario
from app.core.config import get_settings


def user_payload(user: Usuario) -> dict:
    return {
        "user_id": user.id,
        "user_name": user.nome,
        "user_email": user.email or "",
        "is_admin": user.is_admin,
    }


def create_access_token(payload: dict) -> str:
    s = get_settings()
    data = {
        **payload,
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=s.auth_access_token_expire_minutes),
    }
    return jwt.encode(data, s.auth_secret_key, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    s = get_settings()
    data = {
        "user_id": user_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=s.auth_refresh_token_expire_days),
    }
    return jwt.encode(data, s.auth_secret_key, algorithm="HS256")


def create_password_reset_token(user_id: int) -> str:
    s = get_settings()
    data = {
        "user_id": user_id,
        "type": "password_reset",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return jwt.encode(data, s.auth_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().auth_secret_key, algorithms=["HS256"])

"""
Rotas do painel administrativo: login, dashboard HTML e CRUD JSON de usuários.
"""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.db import get_auth_db
from app.auth.deps import require_admin
from app.auth.models import Usuario
from app.auth.security import create_access_token, create_refresh_token, decode_token, user_payload
from app.auth.service import UsuarioService

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

_COOKIE_MAX_AGE = 60 * 15


# ── Login administrativo ─────────────────────────────────────────────────────


class AdminLoginRequest(BaseModel):
    cracha: str
    senha: str


class AdminPasswordRequest(BaseModel):
    nova_senha: str
    confirmar_senha: str
    refresh_token: str


@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin/login.html", context={})


@router.post("/login")
def admin_login(body: AdminLoginRequest, db: Session = Depends(get_auth_db)):
    user = UsuarioService(db).authenticate(body.cracha, body.senha)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou sem permissão admin",
        )
    access_token = create_access_token(user_payload(user))
    response = JSONResponse(
        {
            "access_token": access_token,
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
            "password_changed": user.password_changed,
        }
    )
    response.set_cookie(
        "admin_token", access_token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    response.set_cookie(
        "access_token", access_token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    return response


@router.post("/change-password")
def admin_change_password(body: AdminPasswordRequest, db: Session = Depends(get_auth_db)):
    if len(body.nova_senha) < 8:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 8 caracteres")
    if body.nova_senha != body.confirmar_senha:
        raise HTTPException(status_code=400, detail="Senhas não coincidem")
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") not in ("refresh", "password_reset"):
            raise ValueError("wrong token type")
        user_id: int = payload["user_id"]
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    svc = UsuarioService(db)
    user = svc.get_by_id(user_id)
    if not user or not user.is_admin or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso não autorizado"
        )
    svc.change_password(user_id, body.nova_senha)
    user = svc.get_by_id(user_id)
    access_token = create_access_token(user_payload(user))
    response = JSONResponse(
        {
            "access_token": access_token,
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        "admin_token", access_token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    response.set_cookie(
        "access_token", access_token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    return response


# ── Dashboard ────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, admin: Usuario = Depends(require_admin)):
    return templates.TemplateResponse(
        request=request, name="admin/users.html", context={"admin": admin}
    )


# ── CRUD de usuários (JSON) ───────────────────────────────────────────────────


class CreateUserRequest(BaseModel):
    nome: str
    cracha: str
    senha: str
    email: str | None = None
    is_admin: bool = False


class UpdateUserRequest(BaseModel):
    nome: str | None = None
    email: str | None = None
    senha: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None


class ResetPasswordRequest(BaseModel):
    nova_senha: str


@router.get("/users")
def list_users(
    page: int = 1,
    limit: int = 20,
    search: str = "",
    status: str = "",
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_auth_db),
):
    offset = (page - 1) * limit
    users, total = UsuarioService(db).get_all(
        search=search, status=status, offset=offset, limit=limit
    )
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, -(-total // limit)),
        "items": [
            {
                "id": u.id,
                "nome": u.nome,
                "cracha": u.cracha,
                "email": u.email,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "password_changed": u.password_changed,
            }
            for u in users
        ],
    }


@router.post("/users", status_code=201)
def create_user(
    body: CreateUserRequest,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_auth_db),
):
    svc = UsuarioService(db)
    if not body.cracha.strip().isdigit():
        raise HTTPException(status_code=400, detail="Crachá deve conter apenas números")
    user = svc.create_user(body.nome, body.cracha, body.senha, body.email, body.is_admin)
    if not user:
        raise HTTPException(status_code=409, detail="Crachá já cadastrado")
    return {"id": user.id, "nome": user.nome, "cracha": user.cracha}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_auth_db),
):
    svc = UsuarioService(db)
    updates: dict = {}
    if body.nome is not None:
        updates["nome"] = body.nome
    if body.email is not None:
        updates["email"] = body.email
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if body.is_admin is not None:
        updates["is_admin"] = body.is_admin
    if body.senha:
        svc.change_password(user_id, body.senha)
    user = svc.update_user(user_id, **updates) if updates else svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {
        "id": user.id,
        "nome": user.nome,
        "cracha": user.cracha,
        "email": user.email,
        "is_active": user.is_active,
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    confirm: bool = False,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_auth_db),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Não é possível excluir o próprio usuário")
    if not confirm:
        raise HTTPException(status_code=400, detail="Passe confirm=true para confirmar exclusão")
    if not UsuarioService(db).delete_user(user_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_auth_db),
):
    if not UsuarioService(db).reset_password(user_id, body.nova_senha):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"ok": True, "message": "Senha resetada. Usuário deverá trocar no próximo login."}

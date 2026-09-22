"""
Rotas web de login/logout e troca forçada de senha (form HTML + cookie httponly).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.db import get_auth_db
from app.auth.security import (
    create_access_token,
    create_password_reset_token,
    decode_token,
    user_payload,
)
from app.auth.service import UsuarioService

router = APIRouter(tags=["login"])
templates = Jinja2Templates(directory="app/templates")

_COOKIE_MAX_AGE = 60 * 15


def _set_access_cookie(response: RedirectResponse, user: object) -> None:
    token = create_access_token(user_payload(user))  # type: ignore[arg-type]
    response.set_cookie(
        "access_token", token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    if user.is_admin:  # type: ignore[attr-defined]
        response.set_cookie(
            "admin_token", token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
        )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    cracha: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_auth_db),
):
    svc = UsuarioService(db)
    user = svc.authenticate(cracha, senha)
    if not user:
        return templates.TemplateResponse(
            request=request, name="login.html", context={"error": "Crachá ou senha inválidos."}
        )
    if not user.password_changed:
        resp = RedirectResponse("/force-change-password", status_code=302)
        token = create_password_reset_token(user.id)
        resp.set_cookie("reset_token", token, max_age=300, httponly=True, samesite="lax")
        return resp
    resp = RedirectResponse("/", status_code=302)
    _set_access_cookie(resp, user)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("access_token")
    resp.delete_cookie("admin_token")
    resp.delete_cookie("reset_token")
    return resp


@router.get("/force-change-password", response_class=HTMLResponse)
def force_change_page(request: Request):
    token = request.cookies.get("reset_token")
    if not token:
        return RedirectResponse("/login", status_code=302)
    try:
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            return RedirectResponse("/login", status_code=302)
    except Exception:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        request=request, name="force_change_password.html", context={"error": None}
    )


@router.post("/force-change-password", response_class=HTMLResponse)
def force_change_submit(
    request: Request,
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_auth_db),
):
    token = request.cookies.get("reset_token")
    if not token:
        return RedirectResponse("/login", status_code=302)
    try:
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            return RedirectResponse("/login", status_code=302)
        user_id = int(payload["user_id"])
    except Exception:
        return RedirectResponse("/login", status_code=302)

    error = None
    if len(nova_senha) < 8:
        error = "A senha deve ter pelo menos 8 caracteres."
    elif nova_senha != confirmar_senha:
        error = "As senhas não coincidem."

    if error:
        return templates.TemplateResponse(
            request=request, name="force_change_password.html", context={"error": error}
        )

    svc = UsuarioService(db)
    svc.change_password(user_id, nova_senha)
    user = svc.get_by_id(user_id)

    resp = RedirectResponse("/", status_code=302)
    resp.delete_cookie("reset_token")
    _set_access_cookie(resp, user)
    return resp

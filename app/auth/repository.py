"""
Repositório de persistência de usuários via SQLAlchemy (SQLite).
"""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.models import Usuario


class UsuarioRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> Usuario | None:
        return self._db.get(Usuario, user_id)

    def get_by_nome_ou_cracha(self, value: str) -> Usuario | None:
        return (
            self._db.query(Usuario)
            .filter(or_(Usuario.nome == value, Usuario.cracha == value))
            .first()
        )

    def get_all(
        self,
        search: str = "",
        status: str = "",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Usuario], int]:
        q = self._db.query(Usuario)
        if search:
            q = q.filter(
                or_(Usuario.nome.ilike(f"%{search}%"), Usuario.cracha.ilike(f"%{search}%"))
            )
        if status == "ativo":
            q = q.filter(Usuario.is_active == True)  # noqa: E712
        elif status == "inativo":
            q = q.filter(Usuario.is_active == False)  # noqa: E712
        total = q.count()
        return q.offset(offset).limit(limit).all(), total

    def create(self, usuario: Usuario) -> Usuario:
        self._db.add(usuario)
        self._db.commit()
        self._db.refresh(usuario)
        return usuario

    def update_password(self, user_id: int, senha_hash: str, password_changed: bool) -> bool:
        u = self._db.get(Usuario, user_id)
        if not u:
            return False
        u.senha_hash = senha_hash
        u.password_changed = password_changed
        self._db.commit()
        return True

    def update(self, user_id: int, **kwargs: object) -> Usuario | None:
        u = self._db.get(Usuario, user_id)
        if not u:
            return None
        for k, v in kwargs.items():
            setattr(u, k, v)
        self._db.commit()
        self._db.refresh(u)
        return u

    def delete(self, user_id: int) -> bool:
        u = self._db.get(Usuario, user_id)
        if not u:
            return False
        self._db.delete(u)
        self._db.commit()
        return True

    def cracha_exists(self, cracha: str, exclude_id: int | None = None) -> bool:
        q = self._db.query(Usuario).filter(Usuario.cracha == cracha)
        if exclude_id is not None:
            q = q.filter(Usuario.id != exclude_id)
        return q.first() is not None

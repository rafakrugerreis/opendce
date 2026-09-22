"""
Regras de negócio de autenticação: hash bcrypt, criação e alteração de usuários.
"""

from __future__ import annotations

import bcrypt
from sqlalchemy.orm import Session

from app.auth.models import Usuario
from app.auth.repository import UsuarioRepository


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self._repo = UsuarioRepository(db)

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

    def verify_password(self, password: str, senha_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), senha_hash.encode())
        except Exception:
            return False

    def authenticate(self, nome_ou_cracha: str, password: str) -> Usuario | None:
        u = self._repo.get_by_nome_ou_cracha(nome_ou_cracha)
        if u and u.is_active and self.verify_password(password, u.senha_hash):
            return u
        return None

    def create_user(
        self,
        nome: str,
        cracha: str,
        password: str,
        email: str | None = None,
        is_admin: bool = False,
    ) -> Usuario | None:
        if self._repo.cracha_exists(cracha):
            return None
        u = Usuario(
            nome=nome,
            cracha=cracha,
            senha_hash=self.hash_password(password),
            email=email,
            is_admin=is_admin,
            password_changed=False,
        )
        return self._repo.create(u)

    def change_password(self, user_id: int, new_password: str) -> bool:
        return self._repo.update_password(user_id, self.hash_password(new_password), True)

    def reset_password(self, user_id: int, temp_password: str) -> bool:
        return self._repo.update_password(user_id, self.hash_password(temp_password), False)

    def get_by_id(self, user_id: int) -> Usuario | None:
        return self._repo.get_by_id(user_id)

    def get_all(self, **kwargs: object) -> tuple[list[Usuario], int]:
        return self._repo.get_all(**kwargs)  # type: ignore[arg-type]

    def update_user(self, user_id: int, **kwargs: object) -> Usuario | None:
        return self._repo.update(user_id, **kwargs)

    def delete_user(self, user_id: int) -> bool:
        return self._repo.delete(user_id)

    def cracha_exists(self, cracha: str, exclude_id: int | None = None) -> bool:
        return self._repo.cracha_exists(cracha, exclude_id)

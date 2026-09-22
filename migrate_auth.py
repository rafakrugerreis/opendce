"""
Script de criação das tabelas de autenticação no PostgreSQL e seed do administrador padrão.
"""

from __future__ import annotations

import bcrypt

from app.auth.db import get_auth_db, init_auth_db
from app.auth.models import Usuario
from app.core.config import get_settings
from app.db.session import get_engine


def run() -> None:
    settings = get_settings()
    init_auth_db()
    db = next(get_auth_db())

    try:
        admin = db.query(Usuario).filter(Usuario.cracha == "0001").first()
        if not admin:
            senha_hash = bcrypt.hashpw(
                settings.auth_default_admin_password.encode(), bcrypt.gensalt(rounds=12)
            ).decode()
            admin = Usuario(
                nome="Admin",
                cracha="0001",
                senha_hash=senha_hash,
                email="admin@empresa.com",
                is_active=True,
                is_admin=True,
                password_changed=True,
            )
            db.add(admin)
            db.commit()
            print(
                f"[OK] Admin criado - cracha: 0001 | senha: {settings.auth_default_admin_password}"
            )
        else:
            print("[INFO] Admin ja existe, nenhuma alteracao feita.")
    finally:
        db.close()
        get_engine().dispose()

    print(f"[OK] Banco de autenticacao pronto em: {settings.database_url}")


if __name__ == "__main__":
    run()

"""
Sessão de banco para autenticação (mesmo PostgreSQL da aplicação).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.auth.models import AuthBase
from app.db.session import get_engine

_AuthSession: sessionmaker[Session] | None = None


def init_auth_db() -> None:
    AuthBase.metadata.create_all(bind=get_engine())


def get_auth_db() -> Generator[Session, None, None]:
    global _AuthSession
    if _AuthSession is None:
        _AuthSession = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    db = _AuthSession()
    try:
        yield db
    finally:
        db.close()

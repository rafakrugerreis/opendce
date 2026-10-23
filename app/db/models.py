"""
Modelos ORM do banco de dados PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StatusDCe(StrEnum):
    GERADA = "GERADA"
    ASSINADA = "ASSINADA"
    PRONTA_PARA_TRANSMISSAO = "PRONTA_PARA_TRANSMISSAO"
    TRANSMITINDO = "TRANSMITINDO"
    AUTORIZADA = "AUTORIZADA"
    REJEITADA = "REJEITADA"
    CANCELADA = "CANCELADA"
    ERRO_TRANSMISSAO = "ERRO_TRANSMISSAO"


class DceDocument(Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    serie: Mapped[int] = mapped_column(Integer, nullable=False)
    chave: Mapped[str] = mapped_column(String(44), nullable=False, unique=True)
    usuario: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=StatusDCe.GERADA)
    c_stat: Mapped[str | None] = mapped_column(String(10), nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    protocolo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    xml_assinado: Mapped[str | None] = mapped_column(Text, nullable=True)
    xml_original: Mapped[str | None] = mapped_column(Text, nullable=True)
    retorno_xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    transmitido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

"""
Repositório de acesso a dados para DC-e.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DceDocument


class DceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def proximo_numero(self, start: int = 1) -> int:
        stmt = select(DceDocument.numero).order_by(DceDocument.numero.desc()).limit(1)
        ultimo = self._db.scalar(stmt)
        return (ultimo + 1) if ultimo is not None else start

    def salvar(self, doc: DceDocument) -> DceDocument:
        self._db.add(doc)
        self._db.commit()
        self._db.refresh(doc)
        return doc

    def buscar_por_id(self, doc_id: int) -> DceDocument | None:
        return self._db.get(DceDocument, doc_id)

    def buscar_por_chave(self, chave: str) -> DceDocument | None:
        return self._db.scalar(select(DceDocument).where(DceDocument.chave == chave))

    def buscar_por_numero(self, numero: int) -> DceDocument | None:
        return self._db.scalar(select(DceDocument).where(DceDocument.numero == numero))

    def listar(
        self,
        status: str | None = None,
        numero: int | None = None,
        chave: str | None = None,
        de: datetime | None = None,
        ate: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DceDocument]:
        stmt = select(DceDocument).order_by(DceDocument.numero.desc())
        if status:
            stmt = stmt.where(DceDocument.status == status)
        if numero:
            stmt = stmt.where(DceDocument.numero == numero)
        if chave:
            stmt = stmt.where(DceDocument.chave == chave)
        if de:
            stmt = stmt.where(DceDocument.criado_em >= de)
        if ate:
            stmt = stmt.where(DceDocument.criado_em <= ate)
        return list(self._db.scalars(stmt.offset(offset).limit(limit)))

    def atualizar_status(
        self,
        doc: DceDocument,
        status: str,
        c_stat: str | None = None,
        motivo: str | None = None,
        protocolo: str | None = None,
        retorno_xml: str | None = None,
        transmitido_em: datetime | None = None,
    ) -> DceDocument:
        doc.status = status
        if c_stat is not None:
            doc.c_stat = c_stat
        if motivo is not None:
            doc.motivo = motivo
        if protocolo is not None:
            doc.protocolo = protocolo
        if retorno_xml is not None:
            doc.retorno_xml = retorno_xml
        if transmitido_em is not None:
            doc.transmitido_em = transmitido_em
        doc.atualizado_em = datetime.utcnow()
        self._db.commit()
        self._db.refresh(doc)
        return doc

    def contagem_por_status(self) -> dict[str, int]:
        from sqlalchemy import func

        rows = self._db.execute(
            select(DceDocument.status, func.count()).group_by(DceDocument.status)
        ).all()
        return {row[0]: row[1] for row in rows}

"""
Schemas de resposta padronizados da API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DceDocumentResponse(BaseModel):
    id: int
    numero: int
    serie: int
    chave: str
    usuario: str | None = None
    status: str
    c_stat: str | None = None
    motivo: str | None = None
    protocolo: str | None = None
    criado_em: datetime
    atualizado_em: datetime
    transmitido_em: datetime | None = None

    model_config = {"from_attributes": True}


class SefazStatusResponse(BaseModel):
    c_stat: str
    x_motivo: str
    tp_amb: str
    xml_bruto: str | None = None
    http_status: int

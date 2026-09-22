"""
Orquestração do ciclo de vida da DC-e: gerar, assinar, transmitir, consultar.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.db.models import DceDocument, StatusDCe
from app.repositories.dce_repository import DceRepository
from app.schemas.dce import DceInput
from app.services.certificate_service import CertificateService
from app.services.dce_xml_service import gerar_xml
from app.services.key_service import gerar_chave
from app.services.schema_validation_service import SchemaValidationService
from app.services.sefaz_client import SefazClient
from app.services.xml_signer_service import XmlSignerService

logger = get_logger(__name__)
FUSO_BRASILIA = timezone(timedelta(hours=-3))


class DceService:
    def __init__(
        self,
        settings: Settings,
        db: Session,
        cert_service: CertificateService,
    ) -> None:
        self._settings = settings
        self._repo = DceRepository(db)
        self._cert_service = cert_service
        self._validator = SchemaValidationService(settings)
        self._signer = XmlSignerService(cert_service)
        self._sefaz = SefazClient(settings, cert_service)

    def criar(self, dados: DceInput, usuario: str | None = None) -> DceDocument:
        agora = datetime.now(FUSO_BRASILIA)
        numero = self._repo.proximo_numero(self._settings.dce_start_number)

        logger.info("Criando DC-e número %d (usuário: %s)", numero, usuario or "anônimo")
        t0 = time.monotonic()

        chave, cdc = gerar_chave(
            c_uf=self._settings.dce_cuf,
            cnpj=self._settings.dce_cnpj,
            serie=self._settings.dce_serie,
            numero=numero,
            tp_emis=1,
            tp_emit=2,
            n_site_autoriz=0,
            data_emissao=agora,
        )

        if self._repo.buscar_por_chave(chave):
            raise ValueError(f"DC-e com chave {chave} já existe (DUPLICATE_DOCUMENT)")

        xml_bytes = gerar_xml(self._settings, dados, chave, cdc, numero, agora)
        xml_original = xml_bytes.decode("utf-8")
        self._cert_service.carregar()
        xml_assinado_bytes = self._signer.assinar(xml_bytes, chave)
        self._validator.validar(xml_assinado_bytes)

        doc = DceDocument(
            numero=numero,
            serie=self._settings.dce_serie,
            chave=chave,
            usuario=usuario,
            status=StatusDCe.ASSINADA,
            xml_original=xml_original,
            xml_assinado=xml_assinado_bytes.decode("utf-8"),
            criado_em=agora,
            atualizado_em=agora,
        )
        doc = self._repo.salvar(doc)
        logger.info("DC-e id=%s chave=%s criada em %.2fs", doc.id, chave, time.monotonic() - t0)
        return doc

    def transmitir(self, doc_id: int) -> DceDocument:
        doc = self._repo.buscar_por_id(doc_id)
        if doc is None:
            raise LookupError(f"Documento {doc_id} não encontrado (DOCUMENT_NOT_FOUND)")
        if not doc.xml_assinado:
            raise ValueError("Documento não possui XML assinado")

        self._repo.atualizar_status(doc, StatusDCe.TRANSMITINDO)
        try:
            resultado = self._sefaz.autorizar(doc.xml_assinado.encode("utf-8"))
        except Exception as exc:
            self._repo.atualizar_status(doc, StatusDCe.ERRO_TRANSMISSAO, motivo=str(exc))
            raise

        c_stat = resultado.get("c_stat", "")
        motivo = resultado.get("x_motivo", "")
        protocolo = resultado.get("protocolo")
        xml_bruto = resultado.get("xml_bruto", "")

        novo_status = StatusDCe.AUTORIZADA if c_stat == "100" else StatusDCe.REJEITADA
        return self._repo.atualizar_status(
            doc,
            novo_status,
            c_stat=c_stat,
            motivo=motivo,
            protocolo=protocolo,
            retorno_xml=xml_bruto,
            transmitido_em=datetime.utcnow(),
        )

    def consultar_sefaz(self, doc_id: int) -> DceDocument:
        doc = self._repo.buscar_por_id(doc_id)
        if doc is None:
            raise LookupError(f"Documento {doc_id} não encontrado")
        resultado = self._sefaz.consultar_protocolo(doc.chave)
        c_stat = resultado.get("c_stat", "")
        motivo = resultado.get("x_motivo", "")
        protocolo = resultado.get("protocolo")
        xml_bruto = resultado.get("xml_bruto", "")

        novo_status = StatusDCe.AUTORIZADA if c_stat in ("100", "101") else doc.status
        return self._repo.atualizar_status(
            doc,
            novo_status,
            c_stat=c_stat,
            motivo=motivo,
            protocolo=protocolo,
            retorno_xml=xml_bruto,
        )

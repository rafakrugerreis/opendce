"""
Rotas SEFAZ: status do serviço.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_user
from app.auth.models import Usuario
from app.core.config import Settings, get_settings
from app.schemas.responses import SefazStatusResponse
from app.services.certificate_service import CertificateService
from app.services.sefaz_client import SefazClient

router = APIRouter(prefix="/api", tags=["sefaz"])


@router.get("/status-sefaz", response_model=SefazStatusResponse)
def status_sefaz(
    current_user: Usuario = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    try:
        settings.require_status_url()
    except ValueError as exc:
        raise HTTPException(
            422,
            detail={"code": "CONFIGURATION_ERROR", "message": str(exc)},
        ) from exc
    cert_service = CertificateService(settings)
    client = SefazClient(settings, cert_service=cert_service)
    try:
        resultado = client.consultar_status()
    except Exception as exc:
        raise HTTPException(
            502,
            detail={"code": "SOAP_ERROR", "message": f"Falha ao consultar SEFAZ: {exc}"},
        ) from exc
    return SefazStatusResponse(
        c_stat=resultado.get("c_stat", ""),
        x_motivo=resultado.get("x_motivo", ""),
        tp_amb=str(settings.tp_amb),
        xml_bruto=resultado.get("xml_bruto"),
        http_status=resultado.get("http_status", 0),
    )

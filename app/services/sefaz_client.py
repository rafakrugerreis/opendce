"""
SOAP 1.2 client para os Web Services da DC-e com mTLS ICP-Brasil.
"""

from __future__ import annotations

import time

import httpx
from lxml import etree

from app.core.config import Settings
from app.core.logging import get_logger
from app.services.certificate_service import CertificateService

logger = get_logger(__name__)

_SOAP_CONTENT_TYPE = "application/soap+xml; charset=UTF-8"
_NS_DCE = "http://www.portalfiscal.inf.br/dce"
_TIMEOUT = 30.0


def _envelope_soap(action: str, payload_xml: str) -> str:
    return (
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
        "<soap12:Header>"
        f'<dceCabecMsg xmlns="{_NS_DCE}">'
        "<cUF>43</cUF>"
        "<versaoDados>1.00</versaoDados>"
        "</dceCabecMsg>"
        "</soap12:Header>"
        "<soap12:Body>"
        f'<dceDadosMsg xmlns="{_NS_DCE}">'
        f"{payload_xml}"
        "</dceDadosMsg>"
        "</soap12:Body>"
        "</soap12:Envelope>"
    )


class SefazClient:
    def __init__(self, settings: Settings, cert_service: CertificateService | None = None) -> None:
        self._settings = settings
        self._cert_service = cert_service

    def _client(self) -> httpx.Client:
        if self._cert_service:
            ssl_ctx = self._cert_service.create_ssl_context(
                verify_ssl=self._settings.dce_verify_ssl,
                ca_bundle=self._settings.dce_ca_bundle,
            )
            return httpx.Client(timeout=_TIMEOUT, verify=ssl_ctx)
        return httpx.Client(timeout=_TIMEOUT, verify=self._settings.dce_verify_ssl)

    def _post(self, url: str, action: str, payload_xml: str) -> tuple[int, str]:
        body = _envelope_soap(action, payload_xml)
        headers = {
            "Content-Type": f'{_SOAP_CONTENT_TYPE}; action="{action}"',
            "SOAPAction": action,
        }
        t0 = time.monotonic()
        try:
            with self._client() as client:
                resp = client.post(url, content=body.encode("utf-8"), headers=headers)
            elapsed = time.monotonic() - t0
            logger.info("SOAP %s → HTTP %d (%.2fs)", action, resp.status_code, elapsed)
            if resp.status_code >= 400:
                logger.error("SEFAZ response body: %s", resp.text[:2000])
            return resp.status_code, resp.text
        except httpx.RequestError as exc:
            logger.error("Erro de comunicação com SEFAZ: %s", exc)
            raise

    def consultar_status(self) -> dict:
        url = self._settings.require_status_url()
        payload = (
            f'<consStatServDCe xmlns="{_NS_DCE}" versao="1.00">'
            f"<tpAmb>{self._settings.tp_amb}</tpAmb>"
            f"<cUF>{self._settings.dce_cuf}</cUF>"
            f"<xServ>STATUS</xServ>"
            f"</consStatServDCe>"
        )
        http_status, xml_bruto = self._post(url, "DCeStatusServico", payload)
        return _extrair_retorno_basico(http_status, xml_bruto)

    def autorizar(self, xml_assinado: bytes) -> dict:
        url = self._settings.require_authorization_url()
        payload_xml = xml_assinado.decode("utf-8")
        if payload_xml.startswith("<?xml"):
            payload_xml = payload_xml[payload_xml.index("?>") + 2 :].lstrip()
        http_status, xml_bruto = self._post(url, "dceAutorizacao", payload_xml)
        return _extrair_retorno_basico(http_status, xml_bruto)

    def consultar_protocolo(self, chave: str) -> dict:
        url = self._settings.require_query_url()
        payload = (
            f'<consSitDCe xmlns="{_NS_DCE}" versao="1.00">'
            f"<tpAmb>{self._settings.tp_amb}</tpAmb>"
            f"<xServ>CONSULTAR</xServ>"
            f"<chDCe>{chave}</chDCe>"
            f"</consSitDCe>"
        )
        http_status, xml_bruto = self._post(url, "dceConsulta", payload)
        return _extrair_retorno_basico(http_status, xml_bruto)


def _extrair_retorno_basico(http_status: int, xml_bruto: str) -> dict:
    result: dict = {
        "http_status": http_status,
        "xml_bruto": xml_bruto,
        "c_stat": "",
        "x_motivo": "",
        "protocolo": None,
    }
    try:
        root = etree.fromstring(xml_bruto.encode("utf-8"))
        for el in root.iter():
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if tag == "cStat" and el.text:
                result["c_stat"] = el.text.strip()
            elif tag == "xMotivo" and el.text:
                result["x_motivo"] = el.text.strip()
            elif tag == "nProt" and el.text:
                result["protocolo"] = el.text.strip()
    except Exception:
        pass
    return result

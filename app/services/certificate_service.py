"""
Carregamento e validação de certificado A1 ICP-Brasil e criação de contexto SSL mTLS.
"""

from __future__ import annotations

import ssl
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CertificateError(Exception):
    pass


class CertificateService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cert: x509.Certificate | None = None
        self._private_key = None

    def carregar(self) -> None:
        path = self._settings.require_cert()
        senha = self._settings.dce_cert_password.encode("utf-8") or None
        try:
            data = path.read_bytes()
            pk, cert, _ = pkcs12.load_key_and_certificates(data, senha)
        except Exception as exc:
            raise CertificateError(f"Erro ao carregar certificado '{path.name}': {exc}") from exc
        self._private_key = pk
        self._cert = cert
        self._validar_validade(cert)
        logger.info("Certificado carregado: %s", cert.subject.rfc4514_string())

    def _validar_validade(self, cert: x509.Certificate) -> None:
        now = datetime.now(UTC)
        not_after = cert.not_valid_after_utc
        if now > not_after:
            raise CertificateError(f"Certificado expirado em {not_after.isoformat()}")

    @property
    def is_loaded(self) -> bool:
        return self._cert is not None and self._private_key is not None

    @property
    def certificado(self) -> x509.Certificate:
        if self._cert is None:
            raise CertificateError("Certificado não carregado. Chame carregar() antes.")
        return self._cert

    @property
    def chave_privada(self):
        if self._private_key is None:
            raise CertificateError("Chave privada não carregada. Chame carregar() antes.")
        return self._private_key

    def create_ssl_context(
        self, verify_ssl: bool = False, ca_bundle: str | None = None
    ) -> ssl.SSLContext:
        if not self.is_loaded:
            self.carregar()

        ctx = ssl.create_default_context()
        if not verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        elif ca_bundle and Path(ca_bundle).exists():
            ctx.load_verify_locations(cafile=ca_bundle)
        else:
            ctx.load_default_certs()

        cert_pem = self.certificado.public_bytes(serialization.Encoding.PEM)
        key_pem = self.chave_privada.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        with (
            tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as cf,
            tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as kf,
        ):
            cf.write(cert_pem)
            cf.flush()
            kf.write(key_pem)
            kf.flush()
            cert_path = cf.name
            key_path = kf.name

        try:
            ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        finally:
            Path(cert_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)

        return ctx

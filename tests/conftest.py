"""
Fixtures compartilhadas para testes do pytest.
"""

from __future__ import annotations

import datetime
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.db.session as db_session_module
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def self_signed_cert_pfx(tmp_path_factory) -> tuple[str, str]:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "RS"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Ijui"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ASSOCIACAO HOSPITAL DE CARIDADE IJUI"),
            x509.NameAttribute(NameOID.COMMON_NAME, "HCI Teste A1"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )

    password = b"teste123"
    pfx_data = pkcs12.serialize_key_and_certificates(
        b"cert",
        private_key,
        cert,
        None,
        serialization.BestAvailableEncryption(password),
    )

    cert_dir = tmp_path_factory.mktemp("certs")
    cert_path = cert_dir / "test_cert.pfx"
    cert_path.write_bytes(pfx_data)

    return str(cert_path), "teste123"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    mock_session = MagicMock(spec=Session)
    mock_session.scalar.return_value = None
    mock_session.scalars.return_value = []
    mock_session.get.return_value = None
    mock_session.execute.return_value.all.return_value = []
    mock_session.execute.return_value.fetchall.return_value = []

    def fake_refresh(obj):
        if getattr(obj, "id", None) is None:
            obj.id = 1
        if getattr(obj, "criado_em", None) is None:
            obj.criado_em = datetime.datetime.now(datetime.UTC)
        if getattr(obj, "atualizado_em", None) is None:
            obj.atualizado_em = datetime.datetime.now(datetime.UTC)

    mock_session.refresh.side_effect = fake_refresh
    mock_session.add.side_effect = fake_refresh
    yield mock_session


@pytest.fixture
def client(
    db_session: Session, self_signed_cert_pfx: tuple[str, str]
) -> Generator[TestClient, None, None]:
    cert_path, cert_pass = self_signed_cert_pfx

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_settings():
        return Settings(
            dce_env="HOMOLOGACAO",
            dce_cnpj="90730508000138",
            dce_razao_social="ASSOCIACAO HOSPITAL DE CARIDADE IJUI",
            dce_municipio_ibge="4310207",
            dce_municipio="IJUI",
            dce_uf="RS",
            dce_cep="98700000",
            dce_cert_path=cert_path,
            dce_cert_password=cert_pass,
            dce_schema_path="schemas/DCe_v1.00.xsd",
            dce_status_url="https://homologacao.dce.fazenda.pr.gov.br/dce/DCeStatusServico",
            dce_authorization_url="https://homologacao.dce.fazenda.pr.gov.br/dce/DCeAutorizacao",
            dce_query_url="https://homologacao.dce.fazenda.pr.gov.br/dce/DCeConsulta",
            database_url="sqlite:///:memory:",
        )

    def override_get_current_user():
        from app.auth.models import Usuario

        return Usuario(
            id=1,
            nome="Usuário Teste",
            cracha="0001",
            email="teste@hci.local",
            is_active=True,
            is_admin=True,
            password_changed=True,
        )

    from app.auth.deps import get_current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_current_user] = override_get_current_user

    # O lifespan chama get_engine() fora do DI: injeta engine sqlite em
    # memória no cache para não tocar no PostgreSQL do .env real.
    db_session_module._engine = create_engine("sqlite:///:memory:")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

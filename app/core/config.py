"""
Configurações centralizadas da aplicação via variáveis de ambiente.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Ambiente(StrEnum):
    HOMOLOGACAO = "HOMOLOGACAO"
    PRODUCAO = "PRODUCAO"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    dce_env: Ambiente = Ambiente.HOMOLOGACAO
    dce_version: str = "1.00"
    dce_uf: str = "RS"
    dce_cuf: int = 43

    dce_cnpj: str = ""
    dce_razao_social: str = ""
    dce_logradouro: str = ""
    dce_numero: str = ""
    dce_complemento: str = ""
    dce_bairro: str = ""
    dce_municipio_ibge: str = "4310207"
    dce_municipio: str = "IJUI"
    dce_cep: str = ""
    dce_serie: int = 0
    dce_start_number: int = 1

    dce_cert_path: str = "certs/certificado.pfx"
    dce_cert_password: str = ""
    dce_ca_bundle: str = ""
    dce_verify_ssl: bool = False

    dce_schema_path: str = "schemas/DCe_v1.00.xsd"

    dce_authorization_url: str = ""
    dce_query_url: str = ""
    dce_status_url: str = ""

    dce_qrcode_baseurl: str = "https://www.fazenda.pr.gov.br/dce/qrcode"
    dce_chave_url: str = "https://www.fazenda.pr.gov.br/dce/qrcode"

    database_url: str = "postgresql+psycopg://opendce:opendce@localhost:5432/opendce"

    app_host: str = "0.0.0.0"
    app_port: int = 7777
    log_level: str = "INFO"

    auth_secret_key: str = ""
    auth_access_token_expire_minutes: int = 15
    auth_refresh_token_expire_days: int = 7
    auth_default_admin_password: str = ""

    @field_validator("auth_secret_key")
    @classmethod
    def secret_key_valid(cls, v: str) -> str:
        if not v or v.strip() == "":
            import secrets

            return secrets.token_hex(32)
        if len(v) < 16:
            raise ValueError("AUTH_SECRET_KEY deve ter no mínimo 16 caracteres")
        return v

    @field_validator("dce_cnpj")
    @classmethod
    def cnpj_format(cls, v: str) -> str:
        if v and len(v.replace(".", "").replace("/", "").replace("-", "")) != 14:
            raise ValueError("DCE_CNPJ deve ter 14 dígitos")
        return v.replace(".", "").replace("/", "").replace("-", "")

    @field_validator("dce_serie")
    @classmethod
    def serie_range(cls, v: int) -> int:
        if not 0 <= v <= 999:
            raise ValueError("DCE_SERIE deve estar entre 0 e 999")
        return v

    @field_validator("dce_cuf")
    @classmethod
    def cuf_valid(cls, v: int) -> int:
        ufs_validas = {
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            31,
            32,
            33,
            35,
            41,
            42,
            43,
            50,
            51,
            52,
            53,
        }
        if v not in ufs_validas:
            raise ValueError(f"DCE_CUF inválido: {v}")
        return v

    @property
    def tp_amb(self) -> int:
        return 2 if self.dce_env == Ambiente.HOMOLOGACAO else 1

    @property
    def cert_path(self) -> Path:
        return Path(self.dce_cert_path)

    @property
    def schema_path(self) -> Path:
        return Path(self.dce_schema_path)

    def require_cert(self) -> Path:
        p = self.cert_path
        if not p.exists():
            raise FileNotFoundError(
                f"Certificado não encontrado em '{p}'. "
                "Configure DCE_CERT_PATH com o caminho correto."
            )
        return p

    def require_schema(self) -> Path:
        p = self.schema_path
        if p.exists():
            return p

        if self.dce_schema_path == "schemas/DCe_v1.00.xsd":
            candidates = [
                Path("schemas/dce/DCe_v1.00.xsd"),
                Path("schemas/dce/dce_v1.00.xsd"),
                Path("schemas/DCe_v1.00.xsd"),
                Path("schemas/dce_v1.00.xsd"),
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate

        raise FileNotFoundError(
            f"Schema XSD não encontrado em '{p}' ou em 'schemas/dce/'. "
            "Coloque a pasta 'dce/' ou o arquivo 'DCe_v1.00.xsd' dentro do diretório 'schemas/'."
        )

    def require_authorization_url(self) -> str:
        if not self.dce_authorization_url:
            raise ValueError(
                "DCE_AUTHORIZATION_URL não configurado. "
                "Homologação SVRS: https://homologacao.dce.fazenda.pr.gov.br/dce/DCeAutorizacao"
            )
        return self.dce_authorization_url

    def require_query_url(self) -> str:
        if not self.dce_query_url:
            raise ValueError(
                "DCE_QUERY_URL não configurado. "
                "Homologação SVRS: https://homologacao.dce.fazenda.pr.gov.br/dce/DCeConsulta"
            )
        return self.dce_query_url

    def require_status_url(self) -> str:
        if not self.dce_status_url:
            raise ValueError(
                "DCE_STATUS_URL não configurado. "
                "Homologação SVRS: https://homologacao.dce.fazenda.pr.gov.br/dce/DCeStatusServico"
            )
        return self.dce_status_url


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

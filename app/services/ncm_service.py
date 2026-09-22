"""
Serviço para consulta e resolução de NCM utilizando a BrasilAPI.
"""

from __future__ import annotations

import functools
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_BASE_URL = "https://brasilapi.com.br/api/ncm/v1"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) opendce/1.0"}
TIMEOUT_SECONDS = 5.0
DEFAULT_NCM = "90189099"


class NcmService:
    @staticmethod
    def _formatar_ncm(raw_code: str) -> str | None:
        digits = re.sub(r"\D", "", str(raw_code))
        if not digits:
            return None
        if len(digits) == 8:
            return digits
        if len(digits) > 8:
            return digits[:8]
        if len(digits) == 2:
            return digits
        return None

    @classmethod
    @functools.lru_cache(maxsize=1024)
    def consultar_api_ncm(cls, termo: str) -> str | None:
        termo_limpo = termo.strip()
        if len(termo_limpo) < 2:
            return None
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS, headers=HEADERS) as client:
                response = client.get(API_BASE_URL, params={"search": termo_limpo})
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        for item in data:
                            fmt = cls._formatar_ncm(str(item.get("codigo", "")))
                            if fmt and len(fmt) == 8:
                                return fmt
                        return cls._formatar_ncm(str(data[0].get("codigo", "")))
        except Exception as exc:
            logger.warning("Falha ao consultar BrasilAPI para '%s': %s", termo, exc)
        return None

    @classmethod
    def buscar_ncm_lista(cls, termo: str, limite: int = 10) -> list[dict[str, str]]:
        termo_limpo = termo.strip()
        if len(termo_limpo) < 2:
            return []
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS, headers=HEADERS) as client:
                response = client.get(API_BASE_URL, params={"search": termo_limpo})
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return [
                            {
                                "codigo": str(item.get("codigo", "")),
                                "codigo_num": cls._formatar_ncm(str(item.get("codigo", ""))) or "",
                                "descricao": str(item.get("descricao", "")),
                            }
                            for item in data[:limite]
                            if item.get("codigo")
                        ]
        except Exception as exc:
            logger.warning("Erro na listagem da BrasilAPI para '%s': %s", termo, exc)
        return []

    @classmethod
    def obter_ncm(cls, cd_ncm: Any, nome: str) -> str:
        if cd_ncm:
            formatted = cls._formatar_ncm(str(cd_ncm))
            if formatted and len(formatted) == 8:
                return formatted

        nome_limpo = str(nome or "").strip()
        if not nome_limpo:
            return DEFAULT_NCM

        res = cls.consultar_api_ncm(nome_limpo)
        if not res and " " in nome_limpo:
            palavras = [w for w in nome_limpo.split() if len(w) >= 3]
            for palavra in palavras[:2]:
                res = cls.consultar_api_ncm(palavra)
                if res:
                    break

        return res or DEFAULT_NCM

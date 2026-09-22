"""
Geração e validação da chave de acesso de 44 dígitos da DC-e.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

_FUSO_BRASILIA = timezone(timedelta(hours=-3))
_CDC_INVALIDOS = {
    "000000",
    "111111",
    "222222",
    "333333",
    "444444",
    "555555",
    "666666",
    "777777",
    "888888",
    "999999",
}


def calcular_dv(chave43: str) -> int:
    if len(chave43) != 43:
        raise ValueError(f"Chave base deve ter 43 dígitos, recebeu {len(chave43)}")
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = sum(int(d) * pesos[(len(chave43) - 1 - i) % 8] for i, d in enumerate(chave43))
    resto = soma % 11
    return 0 if resto in (0, 1) else 11 - resto


def _gerar_cdc_seguro(numero_dc: int) -> str:
    for _ in range(100):
        cdc = f"{secrets.randbelow(1_000_000):06d}"
        if cdc not in _CDC_INVALIDOS and cdc != f"{numero_dc:06d}":
            return cdc
    raise RuntimeError("Não foi possível gerar cDC válido após 100 tentativas")


def gerar_chave(
    c_uf: int,
    cnpj: str,
    serie: int,
    numero: int,
    tp_emis: int,
    tp_emit: int,
    n_site_autoriz: int,
    data_emissao: datetime,
) -> tuple[str, str]:
    if data_emissao.tzinfo is not None:
        data_emissao = data_emissao.astimezone(_FUSO_BRASILIA)
    aamm = data_emissao.strftime("%y%m")
    mod = "99"
    cdc = _gerar_cdc_seguro(numero)

    chave43 = (
        f"{c_uf:02d}"
        f"{aamm}"
        f"{cnpj:0>14}"
        f"{mod}"
        f"{serie:03d}"
        f"{numero:09d}"
        f"{tp_emis:01d}"
        f"{tp_emit:01d}"
        f"{n_site_autoriz:01d}"
        f"{cdc}"
    )
    dv = calcular_dv(chave43)
    chave44 = chave43 + str(dv)
    return chave44, cdc


def validar_chave(chave44: str) -> bool:
    if len(chave44) != 44 or not chave44.isdigit():
        return False
    return calcular_dv(chave44[:43]) == int(chave44[43])

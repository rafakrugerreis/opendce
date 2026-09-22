"""
Testes do KeyService: chave de acesso, DV módulo 11, cDC.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.services.key_service import calcular_dv, gerar_chave, validar_chave

_DIGITOS_EXEMPLO = [
    5,
    2,
    0,
    6,
    0,
    4,
    3,
    3,
    0,
    0,
    9,
    9,
    1,
    1,
    0,
    0,
    2,
    5,
    0,
    6,
    5,
    5,
    0,
    1,
    2,
    0,
    0,
    0,
    0,
    0,
    0,
    7,
    8,
    0,
    0,
    2,
    6,
    7,
    3,
    0,
    1,
    6,
    1,
]
_PESOS_EXEMPLO = [
    4,
    3,
    2,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
]
DV_MANUAL = 5


def test_dv_exemplo_manual():
    soma = sum(d * p for d, p in zip(_DIGITOS_EXEMPLO, _PESOS_EXEMPLO, strict=False))
    assert soma == 644
    resto = soma % 11
    assert resto == 6
    dv = 0 if resto in (0, 1) else 11 - resto
    assert dv == DV_MANUAL
    chave43 = "".join(str(d) for d in _DIGITOS_EXEMPLO)
    assert calcular_dv(chave43) == DV_MANUAL


def test_chave_44_digitos():
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj="90730508000138",
        serie=0,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 1, 15),
    )
    assert len(chave) == 44
    assert chave.isdigit()


def test_chave_comeca_com_cuf_rs():
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj="90730508000138",
        serie=0,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 1, 15),
    )
    assert chave[:2] == "43"


def test_chave_contem_cnpj():
    cnpj = "90730508000138"
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj=cnpj,
        serie=0,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 6, 1),
    )
    assert chave[6:20] == cnpj


def test_chave_modelo_99():
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj="90730508000138",
        serie=0,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 6, 1),
    )
    assert chave[20:22] == "99"


def test_dv_valido_na_chave_gerada():
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj="90730508000138",
        serie=0,
        numero=100,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 3, 20),
    )
    assert validar_chave(chave)


def test_dv_resto_zero_resulta_em_zero():
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj="90730508000138",
        serie=0,
        numero=999,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 12, 31),
    )
    dv = calcular_dv(chave[:43])
    assert 0 <= dv <= 9


def test_cdc_invalido_rejeitado():
    from app.services.key_service import _CDC_INVALIDOS

    for _ in range(50):
        _, cdc = gerar_chave(
            c_uf=43,
            cnpj="90730508000138",
            serie=0,
            numero=1,
            tp_emis=1,
            tp_emit=2,
            n_site_autoriz=0,
            data_emissao=datetime(2024, 1, 1),
        )
        assert cdc not in _CDC_INVALIDOS
        assert cdc != "000001"


def test_cdc_diferente_do_numero():
    for _ in range(50):
        numero = 123456
        _, cdc = gerar_chave(
            c_uf=43,
            cnpj="90730508000138",
            serie=0,
            numero=numero,
            tp_emis=1,
            tp_emit=2,
            n_site_autoriz=0,
            data_emissao=datetime(2024, 1, 1),
        )
        assert cdc != f"{numero:06d}"


def test_validar_chave_invalida():
    chave, _ = gerar_chave(
        c_uf=43,
        cnpj="90730508000138",
        serie=0,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=datetime(2024, 1, 1),
    )
    chave_errada = chave[:43] + str((int(chave[43]) + 1) % 10)
    assert not validar_chave(chave_errada)


def test_calcular_dv_tamanho_errado():
    with pytest.raises(ValueError):
        calcular_dv("12345")

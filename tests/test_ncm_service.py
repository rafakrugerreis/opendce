"""
Testes unitários para o serviço de consulta e resolução de NCM via BrasilAPI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.ncm_service import NcmService


def test_formatar_ncm():
    assert NcmService._formatar_ncm("90.18.31.11") == "90183111"
    assert NcmService._formatar_ncm("90189099") == "90189099"
    assert NcmService._formatar_ncm("90") == "90"
    assert NcmService._formatar_ncm("") is None
    assert NcmService._formatar_ncm("abc") is None


def test_obter_ncm_com_banco_preenchido():
    assert NcmService.obter_ncm("30049045", "DIPIRONA") == "30049045"
    assert NcmService.obter_ncm("9018.31.11", "SERINGA") == "90183111"


def test_obter_ncm_com_api_mockada():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "codigo": "2933.11.11",
            "descricao": "Dipirona",
        }
    ]

    with patch("httpx.Client.get", return_value=mock_resp):
        NcmService.consultar_api_ncm.cache_clear()
        res = NcmService.obter_ncm(None, "DIPIRONA 500MG")
        assert res == "29331111"


def test_buscar_ncm_lista_mockada():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "codigo": "9018.31.11",
            "descricao": "Seringas descartáveis",
        }
    ]

    with patch("httpx.Client.get", return_value=mock_resp):
        lista = NcmService.buscar_ncm_lista("seringa")
        assert len(lista) == 1
        assert lista[0]["codigo_num"] == "90183111"
        assert lista[0]["descricao"] == "Seringas descartáveis"


def test_obter_ncm_fallback_padrao():
    with patch("httpx.Client.get", side_effect=Exception("Timeout")):
        NcmService.consultar_api_ncm.cache_clear()
        assert NcmService.obter_ncm(None, "SERINGA DESCARTAVEL") == "90189099"
        assert NcmService.obter_ncm(None, "AMPOLA GLICOSE") == "90189099"
        assert NcmService.obter_ncm(None, "DESCONHECIDO XYZ") == "90189099"

"""
Testes de integração das rotas da API e web.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_get_root_html(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Opendce" in response.text
    assert "Declaração de Conteúdo Eletrônica" in response.text


def test_get_dce_list(client: TestClient):
    response = client.get("/api/dce")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_dce_nao_encontrada(client: TestClient):
    response = client.get("/api/dce/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"


def test_cancelar_retorna_501(client: TestClient):
    response = client.post("/api/dce/1/cancelar")
    assert response.status_code == 501
    data = response.json()
    assert data["detail"]["code"] == "NOT_IMPLEMENTED"


def test_criar_dce_com_validacao_falha(client: TestClient):
    payload = {
        "destinatario_documento": "00000000000",
        "destinatario_endereco": {
            "logradouro": "Rua Teste",
            "numero": "1",
            "bairro": "Centro",
            "municipio_ibge": "4310207",
            "municipio": "Ijuí",
            "uf": "RS",
            "cep": "98700000",
        },
        "itens": [{"descricao": "Item 1", "quantidade": 1, "valor_unitario": 10.0}],
        "modalidade_transporte": 1,
    }
    response = client.post("/api/dce", json=payload)
    assert response.status_code == 422


def test_criar_dce_transportadora_alfanumerica_invalida(client: TestClient):
    payload = {
        "destinatario_documento": "12.ABC.345/0001-88",
        "destinatario_endereco": {
            "logradouro": "Rua Teste",
            "numero": "1",
            "bairro": "Centro",
            "municipio_ibge": "4310207",
            "municipio": "Ijuí",
            "uf": "RS",
            "cep": "98700000",
        },
        "itens": [{"descricao": "Item 1", "quantidade": 1, "valor_unitario": 10.0}],
        "modalidade_transporte": 2,
        "cnpj_transportadora": "12.ABC.345/0001-99",
    }
    response = client.post("/api/dce", json=payload)
    assert response.status_code == 422


def test_criar_dce_transportadora_alfanumerica_sucesso(client: TestClient):
    payload = {
        "destinatario_documento": "12.ABC.345/0001-88",
        "destinatario_nome": "DESTINATARIO TESTE",
        "destinatario_endereco": {
            "logradouro": "Rua Teste",
            "numero": "1",
            "bairro": "Centro",
            "municipio_ibge": "4310207",
            "municipio": "Ijuí",
            "uf": "RS",
            "cep": "98700000",
        },
        "itens": [{"descricao": "Item 1", "quantidade": 1, "valor_unitario": 10.0}],
        "modalidade_transporte": 2,
        "cnpj_transportadora": "K9RUQU6U000146",
    }
    response = client.post("/api/dce", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ASSINADA"
    assert "chave" in data


def test_status_sefaz_mock(client: TestClient):
    with patch("app.services.sefaz_client.SefazClient.consultar_status") as mock_status:
        mock_status.return_value = {
            "http_status": 200,
            "c_stat": "107",
            "x_motivo": "Serviço em Operação",
            "xml_bruto": "<retConsStatServDCe><cStat>107</cStat></retConsStatServDCe>",
        }
        response = client.get("/api/status-sefaz")
        assert response.status_code == 200
        data = response.json()
        assert data["c_stat"] == "107"
        assert data["x_motivo"] == "Serviço em Operação"


def test_buscar_produtos_api(client: TestClient):
    response = client.get("/api/produtos?q=a")
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/produtos?q=ringer")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_buscar_ncm_api(client: TestClient):
    response = client.get("/api/ncm/buscar?q=a")
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/ncm/buscar?q=seringa")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_resolver_ncm_api(client: TestClient):
    response = client.get("/api/ncm/resolver?descricao=")
    assert response.status_code == 200
    assert response.json()["ncm"] == "90189099"

    response = client.get("/api/ncm/resolver?descricao=seringa")
    assert response.status_code == 200
    assert "ncm" in response.json()


def test_buscar_fornecedores_api(client: TestClient):
    response = client.get("/api/fornecedores?q=a")
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/fornecedores?q=hospital")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unauthenticated_api_rejected():
    from app.main import app

    app.dependency_overrides.clear()
    with TestClient(app) as unauth_client:
        response = unauth_client.get("/api/dce")
        assert response.status_code == 401

        response = unauth_client.get("/api/dce/1")
        assert response.status_code == 401

        response = unauth_client.get("/api/status-sefaz")
        assert response.status_code == 401


def test_force_change_password_requires_signed_jwt(client: TestClient):
    # Tentativa de forjar cookie simples sem assinatura JWT deve falhar com redirect para login
    client.cookies.set("force_user_id", "1")
    response = client.get("/force-change-password", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_security_headers_present(client: TestClient):
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_parse_dace_extrai_numero_serie_e_data():
    from unittest.mock import MagicMock

    from app.api.routes_web import _parse_dace

    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <DCe xmlns="http://www.portalfiscal.inf.br/dce">
      <infDCe versao="1.00" Id="DCe43260990730508000138990010000000291206908481">
        <ide>
          <cUF>43</cUF>
          <cDC>20690848</cDC>
          <mod>99</mod>
          <serie>1</serie>
          <nDC>29</nDC>
          <dhEmi>2026-09-14T14:17:33-03:00</dhEmi>
          <tpEmis>1</tpEmis>
          <tpEmit>2</tpEmit>
          <nSiteAutoriz>0</nSiteAutoriz>
          <cDV>1</cDV>
          <tpAmb>2</tpAmb>
          <verProc>Opendce-Python-1.0</verProc>
        </ide>
        <emit>
          <CNPJ>90730508000138</CNPJ>
          <xNome>ASSOCIACAO HOSPITAL DE CARIDADE IJUI</xNome>
          <enderEmit>
            <xLgr>AV DAVID JOSE MARTINS</xLgr>
            <nro>152</nro>
            <xBairro>CENTRO</xBairro>
            <cMun>4310207</cMun>
            <xMun>IJUI</xMun>
            <UF>RS</UF>
            <CEP>98700000</CEP>
          </enderEmit>
        </emit>
        <dest>
          <CNPJ>92021062000106</CNPJ>
          <xNome>DCE EMITIDA EM AMBIENTE DE HOMOLOGACAO</xNome>
          <enderDest>
            <xLgr>Rua Teixeira Soares</xLgr>
            <nro>S/N</nro>
            <xBairro>Centro</xBairro>
            <cMun>4314100</cMun>
            <xMun>Passo Fundo</xMun>
            <UF>RS</UF>
            <CEP>99010080</CEP>
          </enderDest>
        </dest>
        <total><vDC>171.00</vDC></total>
      </infDCe>
    </DCe>"""
    doc = MagicMock()
    doc.numero = 29
    doc.serie = 1
    doc.chave = "43260990730508000138990010000000291206908481"
    doc.protocolo = "3432600000029269"
    doc.xml_assinado = xml

    dace = _parse_dace(doc)
    assert dace["numero"] == "000000029"
    assert dace["serie"] == "001"
    assert dace["dh_emi"] == "14/09/2026 14:17:33"
    assert dace["dest_nome"] == "DCE EMITIDA EM AMBIENTE DE HOMOLOGACAO"

    # Testar fallback exclusivamente a partir das tags XML caso numero/serie sejam None no doc
    doc_sem_props = MagicMock()
    doc_sem_props.numero = None
    doc_sem_props.serie = None
    doc_sem_props.chave = "43260990730508000138990010000000291206908481"
    doc_sem_props.protocolo = "3432600000029269"
    doc_sem_props.xml_assinado = xml

    dace2 = _parse_dace(doc_sem_props)
    assert dace2["numero"] == "000000029"
    assert dace2["serie"] == "001"

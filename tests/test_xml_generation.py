"""
Testes de geração de XML da DC-e conforme Manual Oficial.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from lxml import etree

from app.core.config import Settings
from app.schemas.dce import DceEndereco, DceInput, DceItem
from app.services.dce_xml_service import NS, gerar_xml
from app.services.key_service import gerar_chave


def test_gerar_xml_estrutura_e_regras():
    settings = Settings(
        dce_env="HOMOLOGACAO",
        dce_cnpj="90730508000138",
        dce_razao_social="ASSOCIACAO HOSPITAL DE CARIDADE IJUI",
        dce_logradouro="AVENIDA DAVID JOSE MARTINS",
        dce_numero="152",
        dce_bairro="CENTRO",
        dce_municipio_ibge="4310207",
        dce_municipio="IJUI",
        dce_uf="RS",
        dce_cep="98700000",
        dce_serie=0,
        dce_cuf=43,
    )

    end = DceEndereco(
        logradouro="RUA 15 DE NOVEMBRO",
        numero="200",
        bairro="CENTRO",
        municipio_ibge="4310207",
        municipio="IJUI",
        uf="RS",
        cep="98700000",
    )

    itens = [
        DceItem(
            descricao="EQUIPAMENTO MEDICO",
            quantidade=Decimal("1"),
            valor_unitario=Decimal("1500.00"),
        ),
        DceItem(
            descricao="CABO CONECTOR", quantidade=Decimal("2"), valor_unitario=Decimal("75.50")
        ),
    ]

    dados = DceInput(
        destinatario_documento="90730508000138",
        destinatario_nome="DESTINATARIO TESTE",
        destinatario_endereco=end,
        itens=itens,
        modalidade_transporte=1,
    )

    agora = datetime(2024, 6, 1, 10, 30, 0)
    chave, cdc = gerar_chave(
        c_uf=settings.dce_cuf,
        cnpj=settings.dce_cnpj,
        serie=settings.dce_serie,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=agora,
    )

    xml_bytes = gerar_xml(settings, dados, chave, cdc, 1, agora)
    assert xml_bytes.startswith(b"<?xml")

    root = etree.fromstring(xml_bytes)
    nsmap = {"dce": NS}

    # 1. Namespace correto sem prefixo no nó raiz
    assert root.tag == f"{{{NS}}}DCe"

    # 2. infDCe com Id correto
    inf_dce = root.find("dce:infDCe", nsmap)
    assert inf_dce is not None
    assert inf_dce.get("Id") == f"DCe{chave}"
    assert inf_dce.get("versao") == "1.00"

    # 3. Regra E04-20: Em homologação, xNome do destinatário deve ser obrigatório e fixo
    x_nome_dest = root.find(".//dce:dest/dce:xNome", nsmap)
    assert x_nome_dest is not None
    assert x_nome_dest.text == "DCE EMITIDA EM AMBIENTE DE HOMOLOGACAO"

    # 5. Textos jurídicos fixos no infDec
    inf_dec = root.find(".//dce:infDec", nsmap)
    assert inf_dec is not None
    x_obs1 = inf_dec.find("dce:xObs1", nsmap).text
    x_obs2 = inf_dec.find("dce:xObs2", nsmap).text
    assert "É contribuinte de ICMS" in x_obs1
    assert "Constitui crime contra a ordem tributária" in x_obs2

    # 6. Total bate com os itens: 1500.00 + 2*75.50 = 1651.00
    v_dc = root.find(".//dce:total/dce:vDC", nsmap).text
    assert v_dc == "1651.00"

    # 6. infDCeSupl deve estar fora de infDCe, como filho direto de DCe
    inf_supl = root.find("dce:infDCeSupl", nsmap)
    assert inf_supl is not None
    assert root.find("dce:infDCe/dce:infDCeSupl", nsmap) is None
    qr_code = inf_supl.find("dce:qrCodDCe", nsmap).text
    assert f"chDCe={chave}" in qr_code


def test_gerar_xml_e_validar_xsd_cnpj_alfanumerico(self_signed_cert_pfx: tuple[str, str]):
    from app.services.certificate_service import CertificateService
    from app.services.schema_validation_service import SchemaValidationService
    from app.services.xml_signer_service import XmlSignerService

    cert_path, cert_pass = self_signed_cert_pfx
    settings = Settings(
        dce_env="HOMOLOGACAO",
        dce_cnpj="90730508000138",
        dce_razao_social="ASSOCIACAO HOSPITAL DE CARIDADE IJUI",
        dce_logradouro="AVENIDA DAVID JOSE MARTINS",
        dce_numero="152",
        dce_bairro="CENTRO",
        dce_municipio_ibge="4310207",
        dce_municipio="IJUI",
        dce_uf="RS",
        dce_cep="98700000",
        dce_serie=0,
        dce_cuf=43,
        dce_schema_path="schemas/dce/dce_v1.00.xsd",
        dce_cert_path=cert_path,
        dce_cert_password=cert_pass,
    )

    end = DceEndereco(
        logradouro="RUA 15 DE NOVEMBRO",
        numero="200",
        bairro="CENTRO",
        municipio_ibge="4310207",
        municipio="IJUI",
        uf="RS",
        cep="98700000",
    )

    itens = [
        DceItem(
            descricao="EQUIPAMENTO MEDICO",
            quantidade=Decimal("1"),
            valor_unitario=Decimal("1500.00"),
        ),
    ]

    dados = DceInput(
        destinatario_documento="12.ABC.345/0001-88",
        destinatario_nome="DESTINATARIO TESTE",
        destinatario_endereco=end,
        itens=itens,
        modalidade_transporte=2,
        cnpj_transportadora="K9RUQU6U000146",
    )

    agora = datetime(2024, 6, 1, 10, 30, 0)
    chave, cdc = gerar_chave(
        c_uf=settings.dce_cuf,
        cnpj=settings.dce_cnpj,
        serie=settings.dce_serie,
        numero=1,
        tp_emis=1,
        tp_emit=2,
        n_site_autoriz=0,
        data_emissao=agora,
    )

    xml_bytes = gerar_xml(settings, dados, chave, cdc, 1, agora)
    cert_svc = CertificateService(settings)
    cert_svc.carregar()
    signer = XmlSignerService(cert_svc)
    xml_assinado = signer.assinar(xml_bytes, chave)

    validator = SchemaValidationService(settings)
    validator.validar(xml_assinado)

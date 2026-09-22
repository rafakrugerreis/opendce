"""
Testes de validação dos Schemas Pydantic da DC-e.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.dce import DceEndereco, DceInput, DceItem, validar_cnpj, validar_cpf


def test_cpf_valido_e_invalido():
    assert validar_cpf("11144477735") is True
    assert validar_cpf("00000000000") is False
    assert validar_cpf("12345678900") is False


def test_cnpj_valido_e_invalido():
    assert validar_cnpj("90730508000138") is True
    assert validar_cnpj("90.730.508/0001-38") is True
    assert validar_cnpj("00000000000000") is False
    assert validar_cnpj("11111111111111") is False
    assert validar_cnpj("12ABC345000188") is True
    assert validar_cnpj("12.ABC.345/0001-88") is True
    assert validar_cnpj("AB12CD34000184") is True
    assert validar_cnpj("AB.12C.D34/0001-84") is True
    assert validar_cnpj("12.ABC.345/0001-89") is False
    assert validar_cnpj("12.ABC.345/0001-8A") is False
    assert validar_cnpj("AAAAAAAAAAAAAA") is False


def test_endereco_valido():
    end = DceEndereco(
        logradouro="Rua do Comércio",
        numero="100",
        bairro="Centro",
        municipio_ibge="4310207",
        municipio="Ijuí",
        uf="RS",
        cep="98700000",
    )
    assert end.uf == "RS"
    assert end.cep == "98700000"


def test_endereco_ibge_invalido():
    with pytest.raises(ValidationError) as exc:
        DceEndereco(
            logradouro="Rua do Comércio",
            numero="100",
            bairro="Centro",
            municipio_ibge="43102",
            municipio="Ijuí",
            uf="RS",
            cep="98700000",
        )
    assert "Código IBGE" in str(exc.value)


def test_item_calculo_total():
    item = DceItem(
        descricao="Cadeira de Rodas Hospitalar",
        quantidade=Decimal("2"),
        valor_unitario=Decimal("450.50"),
    )
    assert item.valor_total == Decimal("901.00")


def test_dce_input_total_calculado():
    end = DceEndereco(
        logradouro="Rua das Flores",
        numero="50",
        bairro="Centro",
        municipio_ibge="4310207",
        municipio="Ijuí",
        uf="RS",
        cep="98700000",
    )
    itens = [
        DceItem(descricao="Item 1", quantidade=Decimal("2"), valor_unitario=Decimal("10.00")),
        DceItem(descricao="Item 2", quantidade=Decimal("1"), valor_unitario=Decimal("30.50")),
    ]
    dce = DceInput(
        destinatario_documento="90730508000138",
        destinatario_nome="Destinatário Teste",
        destinatario_endereco=end,
        itens=itens,
        modalidade_transporte=1,
    )
    assert dce.valor_total == Decimal("50.50")


def test_dce_input_transportadora_obrigatoria_modalidade_2():
    end = DceEndereco(
        logradouro="Rua das Flores",
        numero="50",
        bairro="Centro",
        municipio_ibge="4310207",
        municipio="Ijuí",
        uf="RS",
        cep="98700000",
    )
    itens = [
        DceItem(descricao="Item 1", quantidade=Decimal("1"), valor_unitario=Decimal("100.00")),
    ]
    with pytest.raises(ValidationError) as exc:
        DceInput(
            destinatario_documento="90730508000138",
            destinatario_endereco=end,
            itens=itens,
            modalidade_transporte=2,
        )
    assert "CNPJ da transportadora é obrigatório" in str(exc.value)


def test_dce_input_transportadora_alfanumerica_modalidade_2():
    end = DceEndereco(
        logradouro="Rua das Flores",
        numero="50",
        bairro="Centro",
        municipio_ibge="4310207",
        municipio="Ijuí",
        uf="RS",
        cep="98700000",
    )
    itens = [
        DceItem(descricao="Item 1", quantidade=Decimal("1"), valor_unitario=Decimal("100.00")),
    ]
    dce = DceInput(
        destinatario_documento="12.ABC.345/0001-88",
        destinatario_endereco=end,
        itens=itens,
        modalidade_transporte=2,
        cnpj_transportadora="AB.12C.D34/0001-84",
    )
    assert dce.destinatario_documento == "12ABC345000188"
    assert dce.cnpj_transportadora == "AB12CD34000184"

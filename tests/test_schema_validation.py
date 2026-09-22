"""
Testes do serviço de validação de Schema XSD e proteção XXE.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.schema_validation_service import SchemaValidationError, SchemaValidationService


def test_schema_inexistente_lanca_filenotfound():
    settings = Settings(dce_schema_path="schemas/inexistente.xsd")
    validator = SchemaValidationService(settings)
    with pytest.raises(FileNotFoundError) as exc:
        validator.validar(b"<test/>")
    assert "Schema XSD não encontrado" in str(exc.value)


def test_schema_validacao_com_xsd_temporario():
    mini_xsd = b"""<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://www.portalfiscal.inf.br/dce"
               xmlns="http://www.portalfiscal.inf.br/dce"
               elementFormDefault="qualified">
        <xs:element name="DCe">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="infDCe">
                        <xs:complexType>
                            <xs:sequence>
                                <xs:element name="teste" type="xs:string"/>
                            </xs:sequence>
                        </xs:complexType>
                    </xs:element>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""

    with tempfile.NamedTemporaryFile(suffix=".xsd", delete=False) as tmp:
        tmp.write(mini_xsd)
        tmp_path = Path(tmp.name)

    try:
        settings = Settings(dce_schema_path=str(tmp_path))
        validator = SchemaValidationService(settings)

        xml_valido = b"""<DCe xmlns="http://www.portalfiscal.inf.br/dce">
            <infDCe><teste>OK</teste></infDCe>
        </DCe>"""
        validator.validar(xml_valido)

        xml_invalido = b"""<DCe xmlns="http://www.portalfiscal.inf.br/dce">
            <infDCe><campoInexistente>ERRO</campoInexistente></infDCe>
        </DCe>"""
        with pytest.raises(SchemaValidationError):
            validator.validar(xml_invalido)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_xml_malformado():
    mini_xsd = b"""<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://www.portalfiscal.inf.br/dce"
               elementFormDefault="qualified">
        <xs:element name="root"/>
    </xs:schema>"""

    with tempfile.NamedTemporaryFile(suffix=".xsd", delete=False) as tmp:
        tmp.write(mini_xsd)
        tmp_path = Path(tmp.name)

    try:
        settings = Settings(dce_schema_path=str(tmp_path))
        validator = SchemaValidationService(settings)
        with pytest.raises(SchemaValidationError) as exc:
            validator.validar(b"<DCe><unclosed>")
        assert "XML malformado" in str(exc.value)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

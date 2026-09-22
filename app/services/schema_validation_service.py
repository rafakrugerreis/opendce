"""
Validação do XML da DC-e contra o XSD oficial. Proteção contra XXE.
"""

from __future__ import annotations

from lxml import etree

from app.core.config import Settings


class SchemaValidationError(Exception):
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("; ".join(messages))


class SchemaValidationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._schema: etree.XMLSchema | None = None

    def _carregar_schema(self) -> etree.XMLSchema:
        if self._schema is not None:
            return self._schema
        path = self._settings.require_schema()
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            load_dtd=False,
        )
        with path.open("rb") as f:
            schema_doc = etree.parse(f, parser)
        self._schema = etree.XMLSchema(schema_doc)
        return self._schema

    def validar(self, xml_bytes: bytes) -> None:
        """Valida xml_bytes contra o XSD. Lança SchemaValidationError se inválido.

        Bloqueante: nunca ignora erros de validação silenciosamente.
        """
        schema = self._carregar_schema()
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            load_dtd=False,
        )
        try:
            doc = etree.fromstring(xml_bytes, parser)
        except etree.XMLSyntaxError as exc:
            raise SchemaValidationError([f"XML malformado: {exc}"]) from exc

        if not schema.validate(doc):
            erros = [str(e) for e in schema.error_log]
            raise SchemaValidationError(erros)

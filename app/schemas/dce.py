"""
Schemas Pydantic v2 para entrada e saída da DC-e.
"""

from __future__ import annotations

import re
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

_RE_APENAS_DIGITOS = re.compile(r"^\d+$")
_RE_NCM = re.compile(r"^\d{2}(\d{6})?$")


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for i in range(2):
        soma = sum(int(cpf[j]) * (10 + i - j) for j in range(9 + i))
        esperado = 0 if (soma * 10 % 11) >= 10 else soma * 10 % 11
        if int(cpf[9 + i]) != esperado:
            return False
    return True


def validar_cnpj(cnpj: str) -> bool:
    cnpj = re.sub(r"[^A-Za-z0-9]", "", cnpj).upper()
    if len(cnpj) != 14 or len(set(cnpj)) == 1 or not re.match(r"^[A-Z0-9]{12}\d{2}$", cnpj):
        return False
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(2):
        soma = sum((ord(cnpj[j]) - 48) * pesos[1 - i + j] for j in range(12 + i))
        resto = soma % 11
        if int(cnpj[12 + i]) != (0 if resto < 2 else 11 - resto):
            return False
    return True


class DceEndereco(BaseModel):
    logradouro: str = Field(..., min_length=2, max_length=60)
    numero: str = Field(..., min_length=1, max_length=60)
    complemento: str | None = Field(None, max_length=60)
    bairro: str = Field(..., min_length=2, max_length=60)
    municipio_ibge: str = Field(..., description="Código IBGE de 7 dígitos")
    municipio: str = Field(..., min_length=2, max_length=60)
    uf: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., description="CEP com 8 dígitos")
    c_pais: str = Field(default="1058", description="1058 = Brasil")
    x_pais: str = Field(default="Brasil")

    @field_validator("municipio_ibge")
    @classmethod
    def municipio_7_digitos(cls, v: str) -> str:
        if not re.match(r"^\d{7}$", v):
            raise ValueError("Código IBGE do município deve ter 7 dígitos")
        return v

    @field_validator("uf")
    @classmethod
    def uf_2_letras(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2}$", v.upper()):
            raise ValueError("UF deve ter 2 letras maiúsculas")
        return v.upper()

    @field_validator("cep")
    @classmethod
    def cep_8_digitos(cls, v: str) -> str:
        cep = re.sub(r"\D", "", v)
        if len(cep) != 8:
            raise ValueError("CEP deve ter 8 dígitos")
        return cep


class DceItem(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=120)
    ncm: str | None = Field(None, description="NCM com 2 ou 8 dígitos")
    quantidade: Decimal = Field(..., gt=Decimal(0))
    valor_unitario: Decimal = Field(..., gt=Decimal(0))
    observacao: str | None = Field(None, max_length=500)

    @field_validator("ncm")
    @classmethod
    def ncm_formato(cls, v: str | None) -> str | None:
        if v is not None and not _RE_NCM.match(v):
            raise ValueError("NCM deve ter 2 ou 8 dígitos numéricos")
        return v

    @property
    def valor_total(self) -> Decimal:
        return (self.quantidade * self.valor_unitario).quantize(Decimal("0.01"))


class DceInput(BaseModel):
    destinatario_documento: str = Field(..., description="CPF ou CNPJ do destinatário")
    destinatario_nome: str | None = Field(None, max_length=60)
    destinatario_endereco: DceEndereco
    itens: list[DceItem] = Field(..., min_length=1, max_length=999)
    modalidade_transporte: int = Field(..., description="0=Correios,1=Própria,2=Transportadora")
    cnpj_transportadora: str | None = Field(None)
    informacoes_complementares: str | None = Field(None, max_length=5000)

    @field_validator("destinatario_documento")
    @classmethod
    def doc_valido(cls, v: str) -> str:
        doc = re.sub(r"[^A-Za-z0-9]", "", v).upper()
        if len(doc) == 11 and doc.isdigit():
            if not validar_cpf(doc):
                raise ValueError("CPF do destinatário inválido")
        elif len(doc) == 14:
            if not validar_cnpj(doc):
                raise ValueError("CNPJ do destinatário inválido")
        else:
            raise ValueError("Documento do destinatário deve ser CPF (11) ou CNPJ (14)")
        return doc

    @field_validator("modalidade_transporte")
    @classmethod
    def modalidade_range(cls, v: int) -> int:
        if v not in (0, 1, 2):
            raise ValueError("Modalidade de transporte: 0=Correios, 1=Própria, 2=Transportadora")
        return v

    @model_validator(mode="after")
    def transportadora_obrigatoria(self) -> DceInput:
        if self.modalidade_transporte == 2 and not self.cnpj_transportadora:
            raise ValueError("CNPJ da transportadora é obrigatório para modalidade 2")
        if self.cnpj_transportadora:
            cnpj = re.sub(r"[^A-Za-z0-9]", "", self.cnpj_transportadora).upper()
            if not validar_cnpj(cnpj):
                raise ValueError("CNPJ da transportadora inválido")
            self.cnpj_transportadora = cnpj
        return self

    @property
    def valor_total(self) -> Decimal:
        return sum((item.valor_total for item in self.itens), Decimal("0"))

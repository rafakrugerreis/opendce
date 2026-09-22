"""
Assinatura XMLDSig enveloped da DC-e conforme padrão ICP-Brasil.

Algoritmos obrigatórios (Tabela 4-2 do Manual DC-e Visão Geral):
  CanonicalizationMethod : http://www.w3.org/TR/2001/REC-xml-c14n-20010315
  SignatureMethod        : http://www.w3.org/2000/09/xmldsig#rsa-sha1
  DigestMethod           : http://www.w3.org/2000/09/xmldsig#sha1
  Transforms             : Enveloped + C14N
  KeyInfo                : apenas X509Certificate (sem X509SubjectName, SKI, etc.)

Implementação direta com cryptography + lxml — signxml 5.x bloqueia SHA1 por
política interna, mas o ICP-Brasil exige RSA-SHA1 obrigatoriamente.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from lxml import etree

from app.services.certificate_service import CertificateService

_DS = "http://www.w3.org/2000/09/xmldsig#"
_C14N = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
_DCE_NS = "http://www.portalfiscal.inf.br/dce"


def _ds(name: str) -> str:
    return f"{{{_DS}}}{name}"


def _c14n(elem: etree._Element) -> bytes:
    xml_bytes = etree.tostring(elem, encoding="utf-8")
    standalone = etree.fromstring(xml_bytes)
    return etree.tostring(standalone, method="c14n")


class XmlSignerService:
    def __init__(self, cert_service: CertificateService) -> None:
        self._cert_service = cert_service

    def assinar(self, xml_bytes: bytes, chave: str) -> bytes:
        cert = self._cert_service.certificado
        private_key = self._cert_service.chave_privada

        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_bytes, parser)

        inf_dce = root.find(f"{{{_DCE_NS}}}infDCe")
        if inf_dce is None:
            raise ValueError("Elemento infDCe não encontrado no XML")
        digest_b64 = base64.b64encode(hashlib.sha1(_c14n(inf_dce)).digest()).decode()

        si = etree.Element(_ds("SignedInfo"), nsmap={None: _DS})
        etree.SubElement(si, _ds("CanonicalizationMethod")).set("Algorithm", _C14N)
        etree.SubElement(si, _ds("SignatureMethod")).set("Algorithm", f"{_DS}rsa-sha1")
        ref = etree.SubElement(si, _ds("Reference"))
        ref.set("URI", f"#DCe{chave}")
        transforms = etree.SubElement(ref, _ds("Transforms"))
        etree.SubElement(transforms, _ds("Transform")).set("Algorithm", f"{_DS}enveloped-signature")
        etree.SubElement(transforms, _ds("Transform")).set("Algorithm", _C14N)
        etree.SubElement(ref, _ds("DigestMethod")).set("Algorithm", f"{_DS}sha1")
        etree.SubElement(ref, _ds("DigestValue")).text = digest_b64

        sig_b64 = base64.b64encode(
            private_key.sign(_c14n(si), asym_padding.PKCS1v15(), hashes.SHA1())
        ).decode()

        signature = etree.Element(_ds("Signature"), nsmap={None: _DS})
        signature.append(si)
        etree.SubElement(signature, _ds("SignatureValue")).text = sig_b64
        ki = etree.SubElement(signature, _ds("KeyInfo"))
        x509_data = etree.SubElement(ki, _ds("X509Data"))
        etree.SubElement(x509_data, _ds("X509Certificate")).text = base64.b64encode(
            cert.public_bytes(serialization.Encoding.DER)
        ).decode()

        root.append(signature)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)

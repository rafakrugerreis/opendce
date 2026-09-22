"""
Geração do XML da DC-e conforme leiaute oficial (Manual Anexo I, versão 1.00).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from lxml import etree

from app.core.config import Settings
from app.schemas.dce import DceInput

NS = "http://www.portalfiscal.inf.br/dce"
VERSAO = "1.00"
FUSO_BRASILIA = timezone(timedelta(hours=-3))

_XOBS1 = (
    "É contribuinte de ICMS qualquer pessoa física ou jurídica, que realize, "
    "com habitualidade ou em volume que caracterize intuito comercial, operações "
    "de circulação de mercadoria ou prestações de serviços de transportes "
    "interestadual e intermunicipal e de comunicação, ainda que as operações e "
    "prestações de iniciem no exterior (Lei Complementar nº 87/96, Art. 4º)"
)
_XOBS2 = (
    "Constitui crime contra a ordem tributária suprimir ou reduzir tributo, ou "
    "contribuição social e qualquer acessório: quando negar ou deixar de fornecer, "
    "quando obrigatório, nota fiscal ou documento equivalente, relativa a venda de "
    "mercadoria ou prestação de serviço, efetivamente realizada ou fornece-la em "
    "desacordo com a legislação. Sob pena de reclusão de 2 (dois) e 5 (cinco) anos, "
    "e multa (Lei 8.137/90, Art 1ª, V)."
)


def _e(parent: etree._Element, tag: str, text: str | None = None) -> etree._Element:
    el = etree.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def _fmt_decimal(value: Decimal, casas: int = 2) -> str:
    fmt = f"{{:.{casas}f}}"
    return fmt.format(value)


def _formatar_dh_emi(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt_local = dt.replace(tzinfo=FUSO_BRASILIA)
    else:
        dt_local = dt.astimezone(FUSO_BRASILIA)
    return dt_local.isoformat(timespec="seconds")


def gerar_xml(
    settings: Settings,
    dados: DceInput,
    chave: str,
    cdc: str,
    numero: int,
    data_emissao: datetime,
) -> bytes:
    tp_emis = 1
    tp_emit = 2
    n_site_autoriz = 0
    tp_amb = settings.tp_amb
    dv = chave[43]

    dce = etree.Element(f"{{{NS}}}DCe", nsmap={None: NS})

    inf = etree.SubElement(
        dce,
        f"{{{NS}}}infDCe",
        versao=VERSAO,
        Id=f"DCe{chave}",
    )

    ide = _e(inf, "ide")
    _e(ide, "cUF", str(settings.dce_cuf))
    _e(ide, "cDC", cdc)
    _e(ide, "mod", "99")
    _e(ide, "serie", str(settings.dce_serie))
    _e(ide, "nDC", str(numero))
    _e(ide, "dhEmi", _formatar_dh_emi(data_emissao))
    _e(ide, "tpEmis", str(tp_emis))
    _e(ide, "tpEmit", str(tp_emit))
    _e(ide, "nSiteAutoriz", str(n_site_autoriz))
    _e(ide, "cDV", dv)
    _e(ide, "tpAmb", str(tp_amb))
    _e(ide, "verProc", "Opendce-Python-1.0")

    # ── Grupo C: emit ────────────────────────────────────────────────────────
    emit = _e(inf, "emit")
    _e(emit, "CNPJ", settings.dce_cnpj)
    _e(emit, "xNome", settings.dce_razao_social)
    ender_emit = _e(emit, "enderEmit")
    _e(ender_emit, "xLgr", settings.dce_logradouro)
    _e(ender_emit, "nro", settings.dce_numero)
    if settings.dce_complemento:
        _e(ender_emit, "xCpl", settings.dce_complemento)
    _e(ender_emit, "xBairro", settings.dce_bairro)
    _e(ender_emit, "cMun", settings.dce_municipio_ibge)
    _e(ender_emit, "xMun", settings.dce_municipio)
    _e(ender_emit, "UF", settings.dce_uf)
    _e(ender_emit, "CEP", settings.dce_cep)
    _e(ender_emit, "cPais", "1058")
    _e(ender_emit, "xPais", "Brasil")

    # ── Grupo E: dest ────────────────────────────────────────────────────────
    dest = _e(inf, "dest")
    doc = dados.destinatario_documento
    if len(doc) == 14:
        _e(dest, "CNPJ", doc)
    else:
        _e(dest, "CPF", doc)

    # Regra E04-20: em homologação o xNome é obrigatório e fixo
    x_nome_dest = (
        "DCE EMITIDA EM AMBIENTE DE HOMOLOGACAO" if tp_amb == 2 else (dados.destinatario_nome or "")
    )
    if x_nome_dest:
        _e(dest, "xNome", x_nome_dest)

    ender_dest = _e(dest, "enderDest")
    end = dados.destinatario_endereco
    _e(ender_dest, "xLgr", end.logradouro)
    _e(ender_dest, "nro", end.numero)
    if end.complemento:
        _e(ender_dest, "xCpl", end.complemento)
    _e(ender_dest, "xBairro", end.bairro)
    _e(ender_dest, "cMun", end.municipio_ibge)
    _e(ender_dest, "xMun", end.municipio)
    _e(ender_dest, "UF", end.uf)
    if end.cep:
        _e(ender_dest, "CEP", end.cep)
    _e(ender_dest, "cPais", end.c_pais)
    _e(ender_dest, "xPais", end.x_pais)

    for idx, item in enumerate(dados.itens, start=1):
        det = etree.SubElement(inf, f"{{{NS}}}det", nItem=str(idx))
        prod = _e(det, "prod")
        _e(prod, "xProd", item.descricao)
        _e(prod, "NCM", item.ncm or "90189099")
        _e(prod, "qCom", _fmt_decimal(item.quantidade, 4).rstrip("0").rstrip(".") or "0")
        _e(prod, "vUnCom", _fmt_decimal(item.valor_unitario, 2))
        _e(prod, "vProd", _fmt_decimal(item.valor_total, 2))
        if item.observacao:
            _e(det, "infAdProd", item.observacao)

    total = _e(inf, "total")
    _e(total, "vDC", _fmt_decimal(dados.valor_total, 2))

    transp = _e(inf, "transp")
    _e(transp, "modTrans", str(dados.modalidade_transporte))
    _e(transp, "CNPJTransp", dados.cnpj_transportadora or "")

    if dados.informacoes_complementares:
        inf_adic = _e(inf, "infAdic")
        _e(inf_adic, "infCpl", dados.informacoes_complementares)

    inf_dec = _e(inf, "infDec")
    _e(inf_dec, "xObs1", _XOBS1)
    _e(inf_dec, "xObs2", _XOBS2)

    inf_solic = _e(dce, "infSolicDCe")
    _e(inf_solic, "xSolic", "")
    inf_supl = _e(dce, "infDCeSupl")
    qr_url = _build_qrcode_url(settings, chave, tp_amb)
    chave_url = (
        settings.dce_chave_url
        or settings.dce_qrcode_baseurl
        or "https://www.fazenda.pr.gov.br/dce/qrcode"
    )
    _e(inf_supl, "qrCodDCe", qr_url)
    _e(inf_supl, "urlChave", chave_url)

    return etree.tostring(
        dce,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=False,
    )


def _build_qrcode_url(settings: Settings, chave: str, tp_amb: int) -> str:
    base = (settings.dce_qrcode_baseurl or "https://www.fazenda.pr.gov.br/dce/qrcode").rstrip("/")
    return f"{base}?chDCe={chave}&tpAmb={tp_amb}"

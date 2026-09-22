"""
Rotas web — renderiza interface Jinja2.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.models import Usuario
from app.db.session import get_db
from app.repositories.dce_repository import DceRepository

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("app/static/images/favicon.png")


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    repo = DceRepository(db)
    contagem = repo.contagem_por_status()
    documentos = repo.listar(limit=20)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "contagem": contagem,
            "documentos": documentos,
            "current_user": current_user,
        },
    )


@router.get("/dce/{doc_id}", response_class=HTMLResponse)
def detalhe(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    repo = DceRepository(db)
    doc = repo.buscar_por_id(doc_id)
    return templates.TemplateResponse(
        request=request,
        name="dce_detail.html",
        context={"doc": doc, "current_user": current_user},
    )


def _parse_dace(doc: object) -> dict[str, object]:
    from datetime import datetime

    from lxml import etree

    xml_str = getattr(doc, "xml_assinado", None) or getattr(doc, "xml_original", None)
    if not xml_str:
        return {}
    root = etree.fromstring(xml_str.encode("utf-8"))
    ns = {"d": "http://www.portalfiscal.inf.br/dce"}

    def t(path: str) -> str:
        return root.findtext(path, default="", namespaces=ns)

    transp_mod = t(".//d:transp/d:modTrans")
    mod_map = {"0": "0 - CORREIOS (ECT)", "1": "1 - TRANSPORTE PRÓPRIO", "2": "2 - TRANSPORTADORA"}

    itens = [
        {
            "item": idx,
            "descricao": det.findtext("d:prod/d:xProd", default="", namespaces=ns),
            "quantidade": det.findtext("d:prod/d:qCom", default="1", namespaces=ns),
            "valor": det.findtext("d:prod/d:vProd", default="0.00", namespaces=ns),
        }
        for idx, det in enumerate(root.findall(".//d:det", namespaces=ns), start=1)
    ]

    numero_val = getattr(doc, "numero", None) or t(".//d:ide/d:nDC") or 0
    serie_val = getattr(doc, "serie", None) or t(".//d:ide/d:serie") or 0
    raw_dh = t(".//d:ide/d:dhEmi")
    dh_emi = ""
    if raw_dh:
        try:
            dt = datetime.fromisoformat(raw_dh)
            dh_emi = dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            dh_emi = f"{raw_dh[:10]} {raw_dh[11:19]}".strip()

    return {
        "numero": f"{int(numero_val):09d}",
        "serie": f"{int(serie_val):03d}",
        "chave": getattr(doc, "chave", ""),
        "dh_emi": dh_emi,
        "mod_trans": mod_map.get(transp_mod, transp_mod),
        "protocolo": getattr(doc, "protocolo", "") or "—",
        "emit_doc": t(".//d:emit/d:CNPJ") or t(".//d:emit/d:CPF"),
        "emit_nome": t(".//d:emit/d:xNome"),
        "emit_cidade_uf": f"{t('.//d:emit/d:enderEmit/d:xMun')}-{t('.//d:emit/d:enderEmit/d:UF')}",
        "emit_endereco": f"{t('.//d:emit/d:enderEmit/d:xLgr')}, {t('.//d:emit/d:enderEmit/d:nro')}, {t('.//d:emit/d:enderEmit/d:xBairro')}, CEP: {t('.//d:emit/d:enderEmit/d:CEP')}",
        "dest_doc": t(".//d:dest/d:CNPJ") or t(".//d:dest/d:CPF"),
        "dest_nome": t(".//d:dest/d:xNome"),
        "dest_cidade_uf": f"{t('.//d:dest/d:enderDest/d:xMun')}-{t('.//d:dest/d:enderDest/d:UF')}",
        "dest_endereco": f"{t('.//d:dest/d:enderDest/d:xLgr')}, {t('.//d:dest/d:enderDest/d:nro')}, {t('.//d:dest/d:enderDest/d:xBairro')}, CEP: {t('.//d:dest/d:enderDest/d:CEP')}",
        "transp_cnpj": t(".//d:transp/d:CNPJTransp") or "—",
        "transp_nome": "Transportadora"
        if transp_mod == "2"
        else ("Correios (ECT)" if transp_mod == "0" else "Transporte Próprio (HCI)"),
        "itens": itens,
        "valor_total": t(".//d:total/d:vDC") or "0.00",
        "inf_cpl": t(".//d:infAdic/d:infCpl") or "",
        "qrcode_url": t(".//d:infDCeSupl/d:qrCodDCe") or "",
    }


@router.get("/dce/{doc_id}/dace", response_class=HTMLResponse)
def imprimir_dace(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    repo = DceRepository(db)
    doc = repo.buscar_por_id(doc_id)
    if not doc:
        return templates.TemplateResponse(
            request=request,
            name="dce_detail.html",
            context={"doc": None, "current_user": current_user},
        )
    dace = _parse_dace(doc)
    return templates.TemplateResponse(
        request=request,
        name="dace.html",
        context={"doc": doc, "dace": dace, "current_user": current_user},
    )

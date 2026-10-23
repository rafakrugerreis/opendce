"""
Rotas da API REST para DC-e.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.models import Usuario
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.dce_repository import DceRepository
from app.schemas.dce import DceInput
from app.schemas.responses import DceDocumentResponse
from app.services.certificate_service import CertificateService
from app.services.dce_service import DceService
from app.services.ncm_service import NcmService

router = APIRouter(prefix="/api", tags=["dce"])


def _make_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DceService:
    cert = CertificateService(settings)
    return DceService(settings, db, cert)


@router.get("/dce", response_model=list[DceDocumentResponse])
def listar_dce(
    status: str | None = None,
    numero: int | None = None,
    chave: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = DceRepository(db)
    return repo.listar(status=status, numero=numero, chave=chave, limit=limit, offset=offset)


@router.post("/dce", response_model=DceDocumentResponse, status_code=201)
def criar_dce(
    dados: DceInput,
    svc: DceService = Depends(_make_service),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        doc = svc.criar(dados, usuario=current_user.nome)
        return doc
    except FileNotFoundError as exc:
        raise HTTPException(422, detail={"code": "CONFIGURATION_ERROR", "message": str(exc)})
    except ValueError as exc:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": str(exc)})
    except Exception as exc:
        raise HTTPException(500, detail={"code": "XML_ERROR", "message": str(exc)})


@router.get("/dce/{doc_id}", response_model=DceDocumentResponse)
def detalhe_dce(
    doc_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = DceRepository(db)
    doc = repo.buscar_por_id(doc_id)
    if doc is None:
        raise HTTPException(
            404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": f"Documento {doc_id} não encontrado"},
        )
    return doc


@router.get("/dce/{doc_id}/xml")
def xml_dce(
    doc_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = DceRepository(db)
    doc = repo.buscar_por_id(doc_id)
    if doc is None:
        raise HTTPException(404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Não encontrado"})
    if not doc.xml_assinado:
        raise HTTPException(
            422, detail={"code": "XML_ERROR", "message": "Documento não possui XML assinado"}
        )
    return Response(content=doc.xml_assinado, media_type="application/xml; charset=UTF-8")


@router.get("/dce/{doc_id}/download")
def download_xml(
    doc_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = DceRepository(db)
    doc = repo.buscar_por_id(doc_id)
    if doc is None:
        raise HTTPException(404)
    filename = f"DCe_{doc.chave}.xml"
    return Response(
        content=(doc.xml_assinado or "").encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/dce/{doc_id}/transmitir", response_model=DceDocumentResponse)
def transmitir(
    doc_id: int,
    current_user: Usuario = Depends(get_current_user),
    svc: DceService = Depends(_make_service),
):
    try:
        return svc.transmitir(doc_id)
    except LookupError as exc:
        raise HTTPException(404, detail={"code": "DOCUMENT_NOT_FOUND", "message": str(exc)})
    except ValueError as exc:
        raise HTTPException(422, detail={"code": "CONFIGURATION_ERROR", "message": str(exc)})
    except Exception as exc:
        raise HTTPException(502, detail={"code": "SOAP_ERROR", "message": str(exc)})


@router.post("/dce/{doc_id}/consultar", response_model=DceDocumentResponse)
def consultar(
    doc_id: int,
    current_user: Usuario = Depends(get_current_user),
    svc: DceService = Depends(_make_service),
):
    try:
        return svc.consultar_sefaz(doc_id)
    except LookupError as exc:
        raise HTTPException(404, detail={"code": "DOCUMENT_NOT_FOUND", "message": str(exc)})
    except ValueError as exc:
        raise HTTPException(422, detail={"code": "CONFIGURATION_ERROR", "message": str(exc)})
    except Exception as exc:
        raise HTTPException(502, detail={"code": "SOAP_ERROR", "message": str(exc)})


@router.post("/dce/{doc_id}/cancelar")
def cancelar(
    doc_id: int,
    current_user: Usuario = Depends(get_current_user),
):
    raise HTTPException(
        501,
        detail={
            "code": "NOT_IMPLEMENTED",
            "message": (
                "Cancelamento não implementado. "
                "Ative com DCE_FEATURE_CANCELAMENTO=true quando disponível."
            ),
        },
    )


@router.get("/produtos")
def buscar_produtos(
    q: str = "",
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, str]]:
    termo = q.strip()
    if len(termo) < 2:
        return []
    from sqlalchemy import text

    sql = text(
        "SELECT DISTINCT DS_PRODUTO_RESUMIDO, CD_NCM FROM PRODUTO "
        "WHERE UPPER(DS_PRODUTO_RESUMIDO) LIKE UPPER(:term) "
        "AND DS_PRODUTO_RESUMIDO IS NOT NULL "
        "LIMIT 20"
    )
    rows = db.execute(sql, {"term": f"%{termo}%"}).fetchall()
    return [
        {
            "descricao": str(r[0]),
            "ncm": NcmService._formatar_ncm(str(r[1])) if r[1] else "",
        }
        for r in rows
        if r[0]
    ]


@router.get("/ncm/resolver")
def resolver_ncm(
    descricao: str = "",
    current_user: Usuario = Depends(get_current_user),
) -> dict[str, str]:
    termo = descricao.strip()
    if not termo:
        return {"descricao": "", "ncm": "90189099"}
    ncm = NcmService.obter_ncm(None, termo)
    return {"descricao": termo, "ncm": ncm}


@router.get("/ncm/buscar")
def buscar_ncm(
    q: str = "",
    current_user: Usuario = Depends(get_current_user),
) -> list[dict[str, str]]:
    termo = q.strip()
    if len(termo) < 2:
        return []
    return NcmService.buscar_ncm_lista(termo)


@router.get("/fornecedores")
def buscar_fornecedores(
    q: str = "",
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, str]]:
    termo = q.strip()
    if len(termo) < 2:
        return []
    from sqlalchemy import text

    termo_num = "".join(filter(str.isdigit, termo))
    sql = text(
        "SELECT DISTINCT NM_FORNECEDOR, DS_ENDERECO, NR_CGC_CPF, DS_BAIRRO, NR_CEP "
        "FROM FORNECEDOR "
        "WHERE SN_ATIVO = 'S' "
        "AND NM_FORNECEDOR IS NOT NULL "
        "AND ("
        "  UPPER(NM_FORNECEDOR) LIKE UPPER(:term) "
        "  OR NR_CGC_CPF LIKE :term "
        "  OR (:term_num != '' AND REPLACE(REPLACE(REPLACE(NR_CGC_CPF, '.', ''), '/', ''), '-', '') LIKE :term_num) "
        ") "
        "LIMIT 20"
    )
    rows = db.execute(
        sql,
        {
            "term": f"%{termo}%",
            "term_num": f"%{termo_num}%" if termo_num else "",
        },
    ).fetchall()
    return [
        {
            "nome": str(r[0] or "").strip(),
            "endereco": str(r[1] or "").strip(),
            "documento": str(r[2] or "").strip(),
            "bairro": str(r[3] or "").strip(),
            "cep": str(r[4] or "").strip(),
        }
        for r in rows
        if r[0]
    ]

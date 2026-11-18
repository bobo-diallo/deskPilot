from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_embedder
from app.domains.search.ports import Embedder
from app.domains.search.service import Mode, SearchService

router = APIRouter(prefix="/search", tags=["search"])


class IndexRequest(BaseModel):
    title: str
    text: str


class IndexResult(BaseModel):
    document_id: int
    title: str
    chunks: int


class HitResult(BaseModel):
    chunk_id: int
    document_id: int
    title: str
    text: str
    score: float


@router.post("/documents", status_code=201)
def index_document(
    body: IndexRequest,
    session: Annotated[Session, Depends(get_db_session)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
) -> IndexResult:
    try:
        document = SearchService(session, embedder).index_text(body.title, body.text)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return IndexResult(
        document_id=document.id, title=document.filename, chunks=len(document.chunks)
    )


@router.get("")
def search(
    q: Annotated[str, Query(min_length=1, description="La question, en français")],
    session: Annotated[Session, Depends(get_db_session)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    k: Annotated[int, Query(ge=1, le=20)] = 5,
    mode: Mode = "hybrid",
) -> list[HitResult]:
    hits = SearchService(session, embedder).search(q, k=k, mode=mode)
    return [HitResult(**hit.__dict__) for hit in hits]

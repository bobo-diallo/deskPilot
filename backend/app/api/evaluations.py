from dataclasses import asdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.domains.evaluations.library import ReportLibrary, UnknownReportError

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


class ReportSummaryResult(BaseModel):
    id: str
    title: str
    date: date | None


class TableResult(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class SectionResult(BaseModel):
    title: str
    paragraphs: list[str]
    tables: list[TableResult]


class ReportResult(BaseModel):
    id: str
    title: str
    date: date | None
    intro: str
    note: str
    sections: list[SectionResult]


def get_report_library() -> ReportLibrary:
    return ReportLibrary(get_settings().evaluation_reports_dir)


@router.get("/reports")
def list_reports(
    library: Annotated[ReportLibrary, Depends(get_report_library)],
) -> list[ReportSummaryResult]:
    return [ReportSummaryResult(**asdict(summary)) for summary in library.list()]


@router.get("/reports/{report_id}")
def get_report(
    report_id: str, library: Annotated[ReportLibrary, Depends(get_report_library)]
) -> ReportResult:
    try:
        return ReportResult.model_validate(asdict(library.get(report_id)))
    except UnknownReportError:
        raise HTTPException(status_code=404, detail="Rapport introuvable.") from None

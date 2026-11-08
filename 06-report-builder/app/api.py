"""HTTP-слой конструктора отчётов."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app import config, service

router = APIRouter()


class ReportRequest(BaseModel):
    title: str = ""
    template: str = Field(default="threat", pattern="^(threat|incident|actor)$")
    tlp: str = Field(default="TLP:AMBER")
    summary: str = ""
    author: str = "analyst"
    iocs: list[dict] = Field(default_factory=list)
    findings: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/templates")
def templates() -> dict:
    return {"items": list(service.templates())}


@router.get("/api/sample")
def sample() -> dict:
    return service.sample()


@router.post("/api/preview")
def preview(payload: ReportRequest) -> dict:
    return service.preview(payload.model_dump())


@router.post("/api/reports")
def create(payload: ReportRequest) -> dict:
    return service.create(payload.model_dump(), True)


@router.get("/api/reports")
def reports(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {"items": list(service.history(limit))}


@router.get("/api/reports/{report_id}")
def report(report_id: int) -> dict:
    found = service.report(report_id)
    return found or missing(report_id)


@router.get("/api/reports/{report_id}/markdown", response_class=PlainTextResponse)
def markdown(report_id: int) -> str:
    return service.markdown_of(report_id) or missing(report_id)


@router.get("/api/metrics")
def metrics() -> dict:
    return service.metrics()


def missing(report_id: int) -> dict:
    raise HTTPException(status_code=404, detail=f"отчёт {report_id} не найден")

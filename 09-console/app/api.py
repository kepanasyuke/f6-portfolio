"""HTTP-слой консоли: один API на все бизнес-разделы."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app import aggregate, config

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
async def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/overview")
async def overview() -> dict:
    return await aggregate.overview()


@router.get("/api/indicators")
async def indicators(q: str = "", kind: str = "", severity: str = "") -> dict:
    return await aggregate.indicators(q, kind, severity)


@router.get("/api/hunting")
async def hunting() -> dict:
    return await aggregate.hunting()


@router.post("/api/hunting/run")
async def run_hunting() -> dict:
    return await aggregate.run_hunting()


@router.get("/api/logs")
async def logs(q: str = "") -> dict:
    return await aggregate.logs(q)


@router.get("/api/graph")
async def graph(node: str = "", depth: int = Query(default=2, ge=1)) -> dict:
    return await aggregate.graph(node, depth)


@router.get("/api/domains")
async def domains(brand: str = "f6security.example") -> dict:
    return await aggregate.domains(brand)


@router.get("/api/reports")
async def reports() -> dict:
    return await aggregate.reports()


@router.post("/api/reports")
async def create_report(payload: ReportRequest) -> dict:
    return await aggregate.create_report(payload.model_dump())


@router.get("/api/hosts")
async def hosts() -> dict:
    return await aggregate.hosts()


@router.post("/api/hosts/{name}/check")
async def check_host(name: str) -> dict:
    return await aggregate.check_host(name)

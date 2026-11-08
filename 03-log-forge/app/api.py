"""HTTP-слой поиска по журналам."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app import config, service

router = APIRouter()


class IngestRequest(BaseModel):
    format: str = Field(default="syslog", pattern="^(syslog|auth|nginx|windows|csv)$")
    content: str
    prefix: str = "manual"


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=25, ge=1, le=200)


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/stats")
def stats() -> dict:
    return service.statistics()


@router.get("/api/logs")
def logs(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {"items": list(service.recent(limit))}


@router.post("/api/search")
def search(payload: SearchRequest) -> dict:
    return service.search(payload.query, payload.limit)


@router.get("/api/search")
def search_get(query: str = "", limit: int = Query(default=25, ge=1, le=200)) -> dict:
    return service.search(query, limit)


@router.post("/api/ingest")
def ingest(payload: IngestRequest) -> dict:
    return service.ingest(payload.format, payload.content, payload.prefix)


@router.post("/api/reindex")
def reindex() -> dict:
    return {"documents": len(service.reset().docs)}


@router.get("/api/mapping")
def mapping() -> dict:
    return service.MAPPING

"""HTTP-слой: REST API портала индикаторов."""
from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app import config, service

router = APIRouter()


class IngestRequest(BaseModel):
    format: str = Field(default="csv", pattern="^(csv|json|txt|text)$")
    content: str


class LocalFeedRequest(BaseModel):
    name: str


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/iocs")
def iocs(
    kind: str = "",
    severity: str = "",
    q: str = "",
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    return service.search(kind, severity, q, limit, offset)


@router.get("/api/stats")
def stats() -> dict:
    return service.stats()


@router.get("/api/feeds")
def feeds() -> dict:
    return {"items": service.list_feeds()}


@router.post("/api/ingest")
def ingest(payload: IngestRequest) -> dict:
    return service.ingest(payload.format, payload.content)


@router.post("/api/ingest/local")
def ingest_local(payload: LocalFeedRequest) -> dict:
    return service.ingest_local(known(payload.name))


@router.post("/api/ingest/all")
def ingest_all() -> dict:
    return {"results": service.ingest_all()}


def known(name: str) -> str:
    return name if name in service.list_feeds() else missing(name)


def missing(name: str) -> NoReturn:
    raise HTTPException(status_code=404, detail=f"фид {name} не найден")

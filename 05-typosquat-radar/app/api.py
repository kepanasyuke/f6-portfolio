"""HTTP-слой радара похожих доменов."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app import config, service

router = APIRouter()


class ScanRequest(BaseModel):
    brand: str = Field(default=config.BRAND, min_length=3)
    limit: int = Field(default=40, ge=1, le=200)


class WatchRequest(BaseModel):
    domain: str
    note: str = ""


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/stats")
def stats() -> dict:
    return service.statistics()


@router.post("/api/scan")
def scan(payload: ScanRequest) -> dict:
    return service.scan(payload.brand.strip().lower(), payload.limit)


@router.get("/api/check")
def check(domain: str = Query(...), brand: str = Query(default=config.BRAND)) -> dict:
    return service.check(brand.strip().lower(), domain)


@router.post("/api/watchlist")
def watch(payload: WatchRequest) -> dict:
    return service.watch(payload.domain.strip().lower(), payload.note)


@router.get("/api/watchlist")
def watchlist() -> dict:
    return {"items": list(service.watchlist())}


@router.get("/api/scans")
def scans(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {"items": list(service.recent(limit))}

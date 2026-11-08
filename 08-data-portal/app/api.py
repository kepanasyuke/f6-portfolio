"""HTTP-слой портала данных."""
from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app import config, service

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/summary")
def summary() -> dict:
    return service.summary()


@router.get("/api/sources")
def sources() -> dict:
    return {"items": list(service.summary()["sources"])}


@router.get("/api/rows")
def rows(
    source: str,
    table: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = "",
    direction: str = "",
    q: str = "",
) -> dict:
    return payload(source, table, page_spec(limit, offset, sort, direction, q))


def page_spec(limit: int, offset: int, sort: str, direction: str, q: str) -> dict:
    return {"limit": limit, "offset": offset, "sort": sort, "direction": direction, "q": q}


def payload(source: str, table: str, spec: dict) -> dict:
    return service.page(source, table, spec) or missing(source, table)


def missing(source: str, table: str) -> NoReturn:
    raise HTTPException(status_code=404, detail=f"нет источника {source} или таблицы {table}")


@router.get("/api/export.csv", response_class=PlainTextResponse)
def export(source: str, table: str, sort: str = "", direction: str = "", q: str = "") -> str:
    return service.export(source, table, page_spec(200, 0, sort, direction, q))

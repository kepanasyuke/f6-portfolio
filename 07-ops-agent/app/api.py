"""HTTP-слой сервиса эксплуатации."""
from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app import config, service

router = APIRouter()


class HostRequest(BaseModel):
    name: str = Field(min_length=2)
    role: str = "server"
    os: str = Field(default="linux", pattern="^(linux|windows)$")
    ip: str = ""
    owner: str = ""
    tags: str = ""


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/overview")
def overview() -> dict:
    return service.overview()


@router.get("/api/hosts")
def hosts() -> dict:
    return {"items": list(service.inventory())}


@router.get("/api/hosts/{name}")
def host(name: str) -> dict:
    return service.host_card(name) or missing(name)


@router.post("/api/hosts")
def create_host(payload: HostRequest) -> dict:
    return service.register(payload.model_dump())


@router.post("/api/hosts/{name}/check")
def check_host(name: str) -> dict:
    return service.refresh(name) or missing(name)


@router.post("/api/check-all")
def check_all() -> dict:
    return {"results": list(service.refresh_all())}


@router.get("/api/problems")
def problems() -> dict:
    return {"items": list(service.problems())}


@router.get("/api/playbook")
def playbook(os_name: str = Query(default="linux", alias="os")) -> dict:
    return service.playbook(os_name)


@router.get("/api/journal")
def journal(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {"items": list(service.journal(limit))}


def missing(name: str) -> NoReturn:
    raise HTTPException(status_code=404, detail=f"хост {name} не найден")

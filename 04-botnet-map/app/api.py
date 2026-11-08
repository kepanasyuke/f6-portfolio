"""HTTP-слой карты инфраструктуры."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app import config, service

router = APIRouter()


class GraphPayload(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/graph")
def graph() -> dict:
    return service.overview()


@router.get("/api/stats")
def stats() -> dict:
    return service.statistics()


@router.get("/api/nodes")
def nodes(q: str = "") -> dict:
    return {"items": list(service.search(q))}


@router.get("/api/nodes/{node_id}")
def node(node_id: str) -> dict:
    return service.node(node_id)


@router.get("/api/pivot")
def pivot(node_id: str = Query(alias="node"), depth: int = Query(default=2, ge=1)) -> dict:
    return service.pivot(node_id, depth)


@router.get("/api/schema")
def schema() -> dict:
    return {"dialect": "postgresql", "sql": service.postgres_schema()}


@router.post("/api/import")
def import_graph(payload: GraphPayload) -> dict:
    return service.import_graph(payload.model_dump())

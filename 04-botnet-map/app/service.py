"""Сценарии: обзор графа, пивот от узла, схема для PostgreSQL."""
from app import config, graph, store


def ensure_seeded() -> bool:
    return bool(store.scalar(store.COUNT_NODES)) or bool(store.seed())


def overview() -> dict:
    return {**graph.overview(), "stats": graph.statistics()}


def pivot(node_id: str, depth: int) -> dict:
    return graph.subgraph(node_id, clamp(depth))


def clamp(depth: int) -> int:
    return max(1, min(config.MAX_DEPTH, depth))


def neighbours(node_id: str) -> dict:
    return pivot(node_id, 1)


def search(needle: str) -> tuple[dict, ...]:
    return graph.search(needle)


def node(node_id: str) -> dict:
    return graph.node(node_id)


def statistics() -> dict:
    return graph.statistics()


def postgres_schema() -> str:
    return config.SCHEMA_FILE.read_text(encoding="utf-8")


def import_graph(payload: dict) -> dict:
    return {"imported": store.load(payload), "stats": graph.statistics()}

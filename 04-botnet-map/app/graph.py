"""Обход графа: дистанции по CTE, подграф, агрегаты."""
from app import store


def distances(node_id: str, depth: int) -> dict[str, int]:
    return {row["id"]: row["depth"] for row in store.query(store.REACH, (node_id, depth))}


def placeholders(count: int) -> str:
    return ", ".join("?" * count)


def nodes_by_ids(ids: tuple[str, ...]) -> tuple[dict, ...]:
    return store.query(store.NODES_BY_IDS.format(placeholders=placeholders(len(ids))), ids) if ids else ()


def edges_within(ids: tuple[str, ...]) -> tuple[dict, ...]:
    sql = store.EDGES_WITHIN.format(placeholders=placeholders(len(ids)))
    return store.query(sql, ids + ids) if ids else ()


def subgraph(node_id: str, depth: int) -> dict:
    return assemble(node_id, distances(node_id, depth))


def assemble(node_id: str, levels: dict[str, int]) -> dict:
    ids = tuple(levels)
    return {"center": node_id, "depths": levels, "nodes": nodes_by_ids(ids), "edges": edges_within(ids)}


def overview() -> dict:
    return {"nodes": store.query(store.NODES_ALL), "edges": store.query(store.EDGES_ALL)}


def search(needle: str) -> tuple[dict, ...]:
    return store.query(store.NODES_LIKE, (f"%{needle}%",))


def node(node_id: str) -> dict:
    found = store.query(store.NODE_ONE, (node_id,))
    return found[0] if found else {}


def statistics() -> dict:
    return {
        "nodes": store.scalar(store.COUNT_NODES),
        "edges": store.scalar(store.COUNT_EDGES),
        "by_kind": {row["key"]: row["n"] for row in store.query(store.GROUP_KIND)},
        "by_relation": {row["key"]: row["n"] for row in store.query(store.GROUP_RELATION)},
    }

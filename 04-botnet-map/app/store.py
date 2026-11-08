"""Граф инфраструктуры на SQLite: узлы, рёбра, рекурсивный обход через CTE.

Схема совместима с PostgreSQL — DDL лежит в data/schema.postgres.sql.
"""
import json
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    first_seen TEXT NOT NULL DEFAULT '',
    risk INTEGER NOT NULL DEFAULT 50,
    tags TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    relation TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 50,
    first_seen TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (src, dst, relation)
);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE VIEW IF NOT EXISTS links AS
    SELECT src, dst, relation, confidence FROM edges
    UNION ALL
    SELECT dst, src, relation, confidence FROM edges;
"""
REACH = """
WITH RECURSIVE reach(id, depth) AS (
    SELECT ?, 0
    UNION
    SELECT links.dst, reach.depth + 1
    FROM links JOIN reach ON links.src = reach.id
    WHERE reach.depth < ?
)
SELECT id, MIN(depth) AS depth FROM reach GROUP BY id ORDER BY depth, id
"""
NODES_ALL = "SELECT id, kind, value, first_seen, risk, tags FROM nodes ORDER BY kind, value"
NODES_LIKE = (
    "SELECT id, kind, value, first_seen, risk, tags FROM nodes "
    "WHERE value LIKE ? ORDER BY kind, value"
)
NODES_BY_IDS = "SELECT id, kind, value, first_seen, risk, tags FROM nodes WHERE id IN ({placeholders})"
NODE_ONE = "SELECT id, kind, value, first_seen, risk, tags FROM nodes WHERE id = ?"
EDGES_ALL = "SELECT src, dst, relation, confidence, first_seen FROM edges ORDER BY src, dst"
EDGES_WITHIN = (
    "SELECT src, dst, relation, confidence, first_seen FROM edges "
    "WHERE src IN ({placeholders}) AND dst IN ({placeholders})"
)
COUNT_NODES = "SELECT COUNT(*) AS n FROM nodes"
COUNT_EDGES = "SELECT COUNT(*) AS n FROM edges"
GROUP_KIND = "SELECT kind AS key, COUNT(*) AS n FROM nodes GROUP BY kind ORDER BY n DESC"
GROUP_RELATION = "SELECT relation AS key, COUNT(*) AS n FROM edges GROUP BY relation ORDER BY n DESC"
INSERT_NODE = (
    "INSERT OR REPLACE INTO nodes (id, kind, value, first_seen, risk, tags) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
INSERT_EDGE = (
    "INSERT OR REPLACE INTO edges (src, dst, relation, confidence, first_seen) "
    "VALUES (?, ?, ?, ?, ?)"
)


def connect() -> sqlite3.Connection:
    return schema(configured(sqlite3.connect(config.db_path())))


def configured(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    return connection


def schema(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.executescript(SCHEMA)
    return connection


def query(sql: str, params: tuple = ()) -> tuple[dict, ...]:
    with connect() as connection:
        return tuple(dict(row) for row in connection.execute(sql, params).fetchall())


def scalar(sql: str, params: tuple = ()) -> int:
    return query(sql, params)[0]["n"]


def seed() -> int:
    payload = json.loads(config.GRAPH_FILE.read_text(encoding="utf-8"))
    return load(payload)


def load(payload: dict) -> int:
    return save(node_rows(payload), edge_rows(payload))


def node_rows(payload: dict) -> tuple[tuple, ...]:
    return tuple(node_row(item) for item in payload.get("nodes", []))


def edge_rows(payload: dict) -> tuple[tuple, ...]:
    return tuple(edge_row(item) for item in payload.get("edges", []))


def node_row(item: dict) -> tuple:
    return (
        item["id"],
        item["kind"],
        item["value"],
        item.get("first_seen", ""),
        int(item.get("risk", 50)),
        item.get("tags", ""),
    )


def edge_row(item: dict) -> tuple:
    return (
        item["src"],
        item["dst"],
        item["relation"],
        int(item.get("confidence", 50)),
        item.get("first_seen", ""),
    )


def save(nodes: tuple[tuple, ...], edges: tuple[tuple, ...]) -> int:
    with connect() as connection:
        connection.executemany(INSERT_NODE, nodes)
        connection.executemany(INSERT_EDGE, edges)
    return len(nodes)

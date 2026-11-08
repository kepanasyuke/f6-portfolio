"""Репозиторий IOC на SQLite: схема, апсерт, фильтрованный поиск, агрегаты."""
import sqlite3
from collections.abc import Iterable

from app import config

GROUPABLE = ("kind", "severity", "source")
SCHEMA = """
CREATE TABLE IF NOT EXISTS iocs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    source TEXT NOT NULL DEFAULT 'unknown',
    confidence INTEGER NOT NULL DEFAULT 50,
    first_seen TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_iocs_kind ON iocs(kind);
CREATE INDEX IF NOT EXISTS idx_iocs_severity ON iocs(severity);
CREATE INDEX IF NOT EXISTS idx_iocs_source ON iocs(source);
"""
UPSERT = """
INSERT INTO iocs (value, kind, severity, source, confidence, first_seen, tags)
VALUES (:value, :kind, :severity, :source, :confidence, :first_seen, :tags)
ON CONFLICT(value) DO UPDATE SET
    severity = excluded.severity,
    confidence = MAX(iocs.confidence, excluded.confidence),
    tags = CASE WHEN iocs.tags = '' OR iocs.tags = excluded.tags
                THEN excluded.tags ELSE iocs.tags || ',' || excluded.tags END
"""
SEARCH = """
SELECT value, kind, severity, source, confidence, first_seen, tags
FROM iocs WHERE {where}
ORDER BY confidence DESC, value ASC
LIMIT ? OFFSET ?
"""
COUNT = "SELECT COUNT(*) AS n FROM iocs"
GROUP = "SELECT {column} AS key, COUNT(*) AS n FROM iocs GROUP BY {column} ORDER BY n DESC"


def connect() -> sqlite3.Connection:
    return migrate(sqlite3.connect(config.db_path()))


def migrate(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    return schema(connection)


def schema(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.executescript(SCHEMA)
    return connection


def fetch(sql: str, params: tuple = ()) -> tuple[sqlite3.Row, ...]:
    with connect() as connection:
        return tuple(connection.execute(sql, params).fetchall())


def save(records: Iterable[dict]) -> None:
    with connect() as connection:
        connection.executemany(UPSERT, tuple(records))


def upsert(records: tuple[dict, ...]) -> int:
    save(records)
    return len(records)


def search(kind: str, severity: str, needle: str, limit: int, offset: int) -> tuple[dict, ...]:
    clause, params = compose(kind, severity, needle)
    return tuple(dict(row) for row in fetch(SEARCH.format(where=clause), (*params, limit, offset)))


def compose(kind: str, severity: str, needle: str) -> tuple[str, tuple]:
    return join_parts(conditions(kind, severity, needle))


def conditions(kind: str, severity: str, needle: str) -> tuple:
    candidates = (equality("kind", kind), equality("severity", severity), contains(needle))
    return tuple(part for part in candidates if part)


def join_parts(parts: tuple) -> tuple[str, tuple]:
    return (" AND ".join(item[0] for item in parts) or "1=1"), flatten(parts)


def flatten(parts: tuple) -> tuple:
    return tuple(value for item in parts for value in item[1])


def equality(column: str, value: str) -> tuple[str, tuple] | None:
    return (f"{column} = ?", (value,)) if value else None


def contains(needle: str) -> tuple[str, tuple] | None:
    return ("value LIKE ?", (f"%{needle}%",)) if needle else None


def total() -> int:
    return fetch(COUNT)[0]["n"]


def group(column: str) -> dict[str, int]:
    return {row["key"]: row["n"] for row in fetch(GROUP.format(column=column))} if column in GROUPABLE else {}

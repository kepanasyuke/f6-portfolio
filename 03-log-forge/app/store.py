"""Хранилище нормализованных журналов на SQLite."""
import json
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS log_events (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL DEFAULT '',
    host TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    document TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON log_events(ts);
CREATE INDEX IF NOT EXISTS idx_logs_category ON log_events(category);
"""
SAVE = """
INSERT OR REPLACE INTO log_events (id, ts, host, category, document)
VALUES (?, ?, ?, ?, ?)
"""
SELECT_ALL = "SELECT document FROM log_events ORDER BY ts"
COUNT = "SELECT COUNT(*) AS n FROM log_events"


def connect() -> sqlite3.Connection:
    return schema(configured(sqlite3.connect(config.db_path())))


def configured(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    return connection


def schema(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.executescript(SCHEMA)
    return connection


def save(documents: tuple[dict, ...]) -> int:
    rows = tuple(row(document, position) for position, document in enumerate(documents))
    return insert(rows)


def insert(rows: tuple[tuple, ...]) -> int:
    with connect() as connection:
        connection.executemany(SAVE, rows)
    return len(rows)


def row(document: dict, position: int) -> tuple:
    return (
        document.get("id", f"log-{position:05d}"),
        document.get("@timestamp", ""),
        document.get("host", ""),
        document.get("event.category", ""),
        json.dumps(document, ensure_ascii=False),
    )


def load() -> tuple[dict, ...]:
    with connect() as connection:
        return tuple(json.loads(item["document"]) for item in connection.execute(SELECT_ALL).fetchall())


def total() -> int:
    with connect() as connection:
        return connection.execute(COUNT).fetchone()["n"]

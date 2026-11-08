"""Хранилище правил и детекций на SQLite."""
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS custom_rules (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    yaml TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS detections (
    rule_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    host TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (rule_id, event_id)
);
"""

SAVE_RULE = "INSERT OR REPLACE INTO custom_rules (id, title, yaml) VALUES (?, ?, ?)"
SAVE_DETECTION = """
INSERT OR IGNORE INTO detections (rule_id, event_id, host, occurred_at, summary)
VALUES (?, ?, ?, ?, ?)
"""
SELECT_RULES = "SELECT id, title, yaml FROM custom_rules ORDER BY id"
SELECT_DETECTIONS = (
    "SELECT rule_id, event_id, host, occurred_at, summary "
    "FROM detections ORDER BY occurred_at DESC"
)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(config.db_path())
    return schema(connection)


def schema(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    return init(connection)


def init(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.executescript(SCHEMA)
    return connection


def write(sql: str, payload: tuple) -> int:
    with connect() as connection:
        connection.executemany(sql, payload)


def rows(sql: str) -> tuple[dict, ...]:
    with connect() as connection:
        return tuple(dict(row) for row in connection.execute(sql).fetchall())


def save_rule(rule_id: str, title: str, text: str) -> int:
    write(SAVE_RULE, ((rule_id, title, text),))
    return 1


def custom_rules() -> tuple[dict, ...]:
    return rows(SELECT_RULES)


def save_detections(items: tuple[dict, ...]) -> int:
    write(SAVE_DETECTION, items)
    return len(items)


def detections() -> tuple[dict, ...]:
    return rows(SELECT_DETECTIONS)

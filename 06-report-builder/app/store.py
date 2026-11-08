"""Хранилище отчётов на SQLite."""
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    template TEXT NOT NULL,
    tlp TEXT NOT NULL,
    markdown TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at DESC);
"""
SAVE = "INSERT INTO reports (title, template, tlp, markdown, payload) VALUES (?, ?, ?, ?, ?)"
SELECT_MANY = "SELECT id, title, template, tlp, created_at FROM reports ORDER BY id DESC LIMIT ?"
SELECT_ONE = "SELECT id, title, template, tlp, markdown, payload, created_at FROM reports WHERE id = ?"
COUNT = "SELECT COUNT(*) AS n FROM reports"
GROUP_TEMPLATE = "SELECT template AS key, COUNT(*) AS n FROM reports GROUP BY template ORDER BY n DESC"


def connect() -> sqlite3.Connection:
    return schema(configured(sqlite3.connect(db_file())))


def db_file():
    config.db_path().parent.mkdir(parents=True, exist_ok=True)
    return config.db_path()


def configured(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    return connection


def schema(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.executescript(SCHEMA)
    return connection


def query(sql: str, params: tuple = ()) -> tuple[dict, ...]:
    with connect() as connection:
        return tuple(dict(row) for row in connection.execute(sql, params).fetchall())


def execute(sql: str, params: tuple) -> int:
    with connect() as connection:
        return connection.execute(sql, params).lastrowid


def save(row: tuple) -> int:
    return execute(SAVE, row)


def many(limit: int) -> tuple[dict, ...]:
    return query(SELECT_MANY, (limit,))


def one(report_id: int) -> dict:
    found = query(SELECT_ONE, (report_id,))
    return found[0] if found else {}


def total() -> int:
    return query(COUNT)[0]["n"]


def by_template() -> dict[str, int]:
    return {row["key"]: row["n"] for row in query(GROUP_TEMPLATE)}

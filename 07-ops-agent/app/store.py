"""Инвентарь хостов, результаты проверок и журнал действий на SQLite."""
import json
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS hosts (
    name TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    os TEXT NOT NULL,
    ip TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS checks (
    host TEXT NOT NULL,
    metric TEXT NOT NULL,
    title TEXT NOT NULL,
    value INTEGER NOT NULL,
    unit TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    checked_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (host, metric)
);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
UPSERT_HOST = (
    "INSERT OR REPLACE INTO hosts (name, role, os, ip, owner, tags) VALUES (?, ?, ?, ?, ?, ?)"
)
UPSERT_CHECK = (
    "INSERT INTO checks (host, metric, title, value, unit, status) VALUES (?, ?, ?, ?, ?, ?) "
    "ON CONFLICT(host, metric) DO UPDATE SET title = excluded.title, value = excluded.value, "
    "unit = excluded.unit, status = excluded.status, checked_at = datetime('now')"
)
SELECT_HOSTS = "SELECT name, role, os, ip, owner, tags FROM hosts ORDER BY os, name"
SELECT_HOST = "SELECT name, role, os, ip, owner, tags FROM hosts WHERE name = ?"
SELECT_CHECKS = (
    "SELECT metric, title, value, unit, status, checked_at FROM checks "
    "WHERE host = ? ORDER BY status DESC, metric"
)
SELECT_ALL_CHECKS = "SELECT host, metric, status FROM checks"
INSERT_AUDIT = "INSERT INTO audit (action, target, detail) VALUES (?, ?, ?)"
SELECT_AUDIT = "SELECT action, target, detail, created_at FROM audit ORDER BY id DESC LIMIT ?"
COUNT_HOSTS = "SELECT COUNT(*) AS n FROM hosts"


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


def write(sql: str, payload: tuple) -> int:
    with connect() as connection:
        connection.executemany(sql, payload)
    return len(payload)


def save_hosts(records: tuple[dict, ...]) -> int:
    return write(UPSERT_HOST, tuple(host_row(record) for record in records))


def host_row(record: dict) -> tuple:
    return (
        record["name"],
        record["role"],
        record["os"],
        record["ip"],
        record.get("owner", ""),
        record.get("tags", ""),
    )


def save_checks(host_name: str, records: tuple[dict, ...]) -> int:
    return write(UPSERT_CHECK, tuple(check_row(host_name, check) for check in records))


def check_row(host_name: str, check: dict) -> tuple:
    return (host_name, check["metric"], check["title"], int(check["value"]), check["unit"], check["status"])


def hosts() -> tuple[dict, ...]:
    return query(SELECT_HOSTS)


def host(name: str) -> dict:
    found = query(SELECT_HOST, (name,))
    return found[0] if found else {}


def checks(host_name: str) -> tuple[dict, ...]:
    return query(SELECT_CHECKS, (host_name,))


def all_checks() -> tuple[dict, ...]:
    return query(SELECT_ALL_CHECKS)


def audit(action: str, target: str, detail: str) -> int:
    with connect() as connection:
        return connection.execute(INSERT_AUDIT, (action, target, detail)).lastrowid


def journal(limit: int) -> tuple[dict, ...]:
    return query(SELECT_AUDIT, (limit,))


def total() -> int:
    return query(COUNT_HOSTS)[0]["n"]


def load_inventory(payload: dict) -> int:
    return save_hosts(tuple(payload.get("hosts", [])))


def dump_host(host_name: str) -> str:
    return json.dumps(host(host_name), ensure_ascii=False)

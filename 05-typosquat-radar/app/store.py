"""Сканирования и список наблюдения на SQLite."""
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    domain TEXT NOT NULL,
    risk INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (brand, domain)
);
CREATE TABLE IF NOT EXISTS watchlist (
    domain TEXT PRIMARY KEY,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_scans_brand ON scans(brand);
"""
SAVE_SCAN = """
INSERT INTO scans (brand, domain, risk, verdict) VALUES (?, ?, ?, ?)
ON CONFLICT(brand, domain) DO UPDATE SET risk = excluded.risk, verdict = excluded.verdict
"""
SELECT_SCANS = "SELECT brand, domain, risk, verdict, created_at FROM scans ORDER BY risk DESC, domain LIMIT ?"
SELECT_BY_BRAND = "SELECT domain, risk, verdict FROM scans WHERE brand = ? ORDER BY risk DESC"
COUNT_SCANS = "SELECT COUNT(*) AS n FROM scans"
SAVE_WATCH = "INSERT OR REPLACE INTO watchlist (domain, note) VALUES (?, ?)"
SELECT_WATCH = "SELECT domain, note, created_at FROM watchlist ORDER BY domain"


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


def save_scans(brand: str, items: tuple[dict, ...]) -> int:
    with connect() as connection:
        connection.executemany(SAVE_SCAN, tuple(scan_row(brand, item) for item in items))
    return len(items)


def scan_row(brand: str, item: dict) -> tuple:
    return (brand, item["domain"], int(item["risk"]), item["verdict"])


def scans(limit: int) -> tuple[dict, ...]:
    return query(SELECT_SCANS, (limit,))


def by_brand(brand: str) -> tuple[dict, ...]:
    return query(SELECT_BY_BRAND, (brand,))


def count() -> int:
    return query(COUNT_SCANS)[0]["n"]


def watch(domain: str, note: str) -> int:
    with connect() as connection:
        connection.execute(SAVE_WATCH, (domain, note))
    return 1


def watchlist() -> tuple[dict, ...]:
    return query(SELECT_WATCH)

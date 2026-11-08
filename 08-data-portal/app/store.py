"""Доступ к базам сервисов строго на чтение."""
import sqlite3
from pathlib import Path

NAMES = (
    "SELECT name FROM sqlite_master "
    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
)


def connect(path: Path) -> sqlite3.Connection:
    return configured(sqlite3.connect(f"file:{path}?mode=ro", uri=True))


def configured(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    return connection


def rows(connection: sqlite3.Connection, sql: str, params: tuple = ()) -> tuple[dict, ...]:
    return tuple(dict(row) for row in connection.execute(sql, params).fetchall())


def read(path: Path, sql: str, params: tuple = ()) -> tuple[dict, ...]:
    with connect(path) as connection:
        return rows(connection, sql, params)


def scalar(path: Path, sql: str, params: tuple = ()) -> int:
    found = read(path, sql, params)
    return int(found[0]["value"]) if found else 0


def quoted(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'

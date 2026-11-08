"""Реестр источников: базы, таблицы, колонки, число строк."""
from pathlib import Path

from app import config, store

COUNT = "SELECT COUNT(*) AS value FROM {table}"
INFO = "PRAGMA table_info({table})"


def overview() -> tuple[dict, ...]:
    return tuple(describe(source) for source in config.REGISTRY)


def describe(source: dict) -> dict:
    return {**source, "available": available(source), "tables": tables(source)}


def available(source: dict) -> bool:
    return config.db_path(source).is_file()


def tables(source: dict) -> tuple[dict, ...]:
    return tuple(table(config.db_path(source), name) for name in names(source)) if available(source) else ()


def names(source: dict) -> tuple[str, ...]:
    return tuple(row["name"] for row in read_names(source)) if available(source) else ()


def read_names(source: dict) -> tuple[dict, ...]:
    return store.read(config.db_path(source), store.NAMES)


def table(path: Path, name: str) -> dict:
    return {"name": name, "rows": count(path, name), "columns": columns(path, name)}


def count(path: Path, name: str) -> int:
    return store.scalar(path, COUNT.format(table=store.quoted(name)))


def columns(path: Path, name: str) -> tuple[dict, ...]:
    return tuple(to_column(row) for row in store.read(path, INFO.format(table=store.quoted(name))))


def to_column(row: dict) -> dict:
    return {
        "name": row["name"],
        "type": row["type"] or "text",
        "pk": bool(row["pk"]),
        "notnull": bool(row["notnull"]),
    }


def known(source: dict, table_name: str) -> bool:
    return table_name in names(source)


def column_names(path: Path, name: str) -> tuple[str, ...]:
    return tuple(column["name"] for column in columns(path, name))

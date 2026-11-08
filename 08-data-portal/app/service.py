"""Сценарии портала: страницы данных, поиск, сводка, выгрузка CSV."""
import csv
import io
from pathlib import Path

from app import config, sources, store

MAX_LIMIT = 200
MAX_OFFSET = 1000000


def page(source_key: str, table_name: str, spec: dict) -> dict:
    request = request_of(source_key, table_name, spec)
    return summarize(request) if request else {}


def request_of(source_key: str, table_name: str, spec: dict) -> dict:
    source = config.source(source_key)
    return build_request(source, table_name, spec) if source and sources.known(source, table_name) else {}


def build_request(source: dict, table_name: str, spec: dict) -> dict:
    path = config.db_path(source)
    return {
        "source": source["key"],
        "service": source["service"],
        "path": path,
        "table": table_name,
        "columns": sources.column_names(path, table_name),
        "limit": clamp(spec.get("limit"), 1, MAX_LIMIT, 50),
        "offset": clamp(spec.get("offset"), 0, MAX_OFFSET, 0),
        "sort": sort_of(spec.get("sort"), path, table_name),
        "direction": "DESC" if str(spec.get("direction", "asc")).lower() == "desc" else "ASC",
        "needle": str(spec.get("q", "") or "").strip(),
    }


def clamp(value: object, low: int, high: int, fallback: int) -> int:
    return min(max(int(value), low), high) if str(value).isdigit() else fallback


def sort_of(value: object, path: Path, table_name: str) -> str:
    names = sources.column_names(path, table_name)
    return str(value) if str(value) in names else first(names)


def first(names: tuple[str, ...]) -> str:
    return names[0] if names else "rowid"


def summarize(request: dict) -> dict:
    return {
        "columns": layout(request),
        "total": total(request),
        "rows": rows_of(request),
        "limit": request["limit"],
        "offset": request["offset"],
    }


def layout(request: dict) -> tuple[dict, ...]:
    return sources.columns(request["path"], request["table"])


def total(request: dict) -> int:
    return store.scalar(request["path"], count_sql(request), condition_params(request))


def count_sql(request: dict) -> str:
    return f"SELECT COUNT(*) AS value FROM {store.quoted(request['table'])} WHERE {clause(request)}"


def rows_of(request: dict) -> tuple[dict, ...]:
    return store.read(request["path"], select_sql(request), page_params(request))


def select_sql(request: dict) -> str:
    table_name = store.quoted(request["table"])
    return f"SELECT * FROM {table_name} WHERE {clause(request)} {ordering(request)} LIMIT ? OFFSET ?"


def ordering(request: dict) -> str:
    return f"ORDER BY {store.quoted(request['sort'])} {request['direction']}"


def clause(request: dict) -> str:
    return " OR ".join(masked(request)) if request["needle"] else "1=1"


def masked(request: dict) -> tuple[str, ...]:
    return tuple(f"CAST({store.quoted(name)} AS TEXT) LIKE ?" for name in request["columns"]) or ("1=0",)


def needle_params(request: dict) -> tuple[str, ...]:
    return tuple(f"%{request['needle']}%" for _ in masked(request))


def condition_params(request: dict) -> tuple:
    return needle_params(request) if request["needle"] else ()


def page_params(request: dict) -> tuple:
    return (*condition_params(request), request["limit"], request["offset"])


def summary() -> dict:
    return {"sources": sources.overview(), "kpis": tuple(kpi(item) for item in config.KPIS)}


def kpi(item: dict) -> dict:
    return {"title": item["title"], "hint": item["hint"], "value": measure(item)}


def measure(item: dict) -> int:
    source = config.source(item["db"])
    return store.scalar(config.db_path(source), item["sql"]) if sources.available(source) else 0


def export(source_key: str, table_name: str, spec: dict) -> str:
    return to_csv(page(source_key, table_name, {**spec, "limit": MAX_LIMIT, "offset": 0}))


def to_csv(payload: dict) -> str:
    return render_csv(payload, io.StringIO())


def render_csv(payload: dict, buffer) -> str:
    write_rows(payload, csv.writer(buffer, delimiter=";"))
    return buffer.getvalue()


def write_rows(payload: dict, writer) -> None:
    writer.writerow(names_of(payload))
    writer.writerows(matrix(payload))


def names_of(payload: dict) -> tuple[str, ...]:
    return tuple(column["name"] for column in payload["columns"])


def matrix(payload: dict) -> tuple[tuple, ...]:
    return tuple(tuple(cell(row.get(name)) for name in names_of(payload)) for row in payload["rows"])


def cell(value: object) -> str:
    return "" if value is None else str(value)

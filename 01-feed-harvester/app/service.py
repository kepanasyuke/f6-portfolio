"""Сценарии: приём фидов, поиск, статистика, автосев демо-данных."""
from app import config, parsers, store


def ingest(format_name: str, content: str) -> dict:
    records, rejected = parsers.parse(format_name, content)
    return {"parsed": len(records), "stored": store.upsert(records), "rejected": rejected}


def ingest_local(name: str) -> dict:
    return ingest(parsers.format_of(name), read_feed(name))


def read_feed(name: str) -> str:
    return (config.FEEDS_DIR / name).read_text(encoding="utf-8")


def list_feeds() -> tuple[str, ...]:
    return tuple(sorted(path.name for path in config.FEEDS_DIR.iterdir() if path.is_file()))


def ingest_all() -> tuple[dict, ...]:
    return tuple({"feed": name, **ingest_local(name)} for name in list_feeds())


def ensure_seeded() -> bool:
    return bool(store.total()) or bool(ingest_all())


def search(kind: str, severity: str, needle: str, limit: int, offset: int) -> dict:
    items = store.search(kind, severity, needle, limit, offset)
    return {"items": items, "count": len(items), "limit": limit, "offset": offset}


def stats() -> dict:
    return {
        "total": store.total(),
        "by_kind": store.group("kind"),
        "by_severity": store.group("severity"),
        "by_source": store.group("source"),
    }

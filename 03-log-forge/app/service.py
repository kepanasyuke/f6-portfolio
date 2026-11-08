"""Сценарии: приём журналов, построение индекса, поиск."""
from pathlib import Path

from app import config, index, parsers, store

CACHE: dict[str, index.Index] = {}
MAPPING = {
    "mappings": {
        "properties": {
            "@timestamp": {"type": "date"},
            "host": {"type": "keyword"},
            "event.category": {"type": "keyword"},
            "event.dataset": {"type": "keyword"},
            "event.outcome": {"type": "keyword"},
            "event.code": {"type": "keyword"},
            "user.name": {"type": "keyword"},
            "source.ip": {"type": "ip"},
            "process.name": {"type": "keyword"},
            "url.path": {"type": "keyword", "fields": {"text": {"type": "text"}}},
            "http.request.method": {"type": "keyword"},
            "http.response.status_code": {"type": "integer"},
            "http.response.body.bytes": {"type": "long"},
            "user_agent.original": {"type": "text"},
            "message": {"type": "text"},
        }
    }
}


def ingest(format_name: str, content: str, prefix: str) -> dict:
    return index_and_store(documents(parsers.parse(format_name, content), prefix))


def documents(parsed: tuple[dict, ...], prefix: str) -> tuple[dict, ...]:
    return tuple({**document, "id": f"{prefix}-{position:04d}"} for position, document in enumerate(parsed))


def index_and_store(docs: tuple[dict, ...]) -> dict:
    store.save(docs)
    return {"stored": len(docs), "documents": len(reset().docs)}


def ingest_file(path: Path) -> dict:
    return ingest(format_of(path), path.read_text(encoding="utf-8"), path.stem)


def format_of(path: Path) -> str:
    return parsers.FORMATS.get(path.stem.lower(), "syslog")


def seed() -> bool:
    return bool(store.total()) or bool(ingest_all())


def ingest_all() -> tuple[dict, ...]:
    return tuple(ingest_file(path) for path in sorted(config.LOGS_DIR.iterdir()) if path.is_file())


def current() -> index.Index:
    return CACHE["index"] if "index" in CACHE else remember(index.build(store.load()))


def remember(built: index.Index) -> index.Index:
    CACHE["index"] = built
    return built


def reset() -> index.Index:
    CACHE.clear()
    return remember(index.build(store.load()))


def search(query: str, limit: int) -> dict:
    items = index.search(current(), query, limit)
    return {"query": query, "count": len(items), "items": items}


def statistics() -> dict:
    return index.statistics(current())


def recent(limit: int) -> tuple[dict, ...]:
    return current().docs[:limit]

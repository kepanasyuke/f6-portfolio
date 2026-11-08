"""Сценарии: инвентаризация, прогон проверок, дашборд, чек-листы, журнал."""
import json

from app import checks, config, playbooks, store


def ensure_seeded() -> bool:
    return bool(store.total()) or bool(seed())


def seed() -> dict:
    return load(inventory_payload())


def inventory_payload() -> dict:
    return json.loads(config.HOSTS_FILE.read_text(encoding="utf-8"))


def load(payload: dict) -> dict:
    return {"hosts": store.load_inventory(payload), "refreshed": len(refresh_all())}


def register(payload: dict) -> dict:
    return host_card(save_and_audit(payload))


def save_and_audit(payload: dict) -> str:
    store.save_hosts((payload,))
    return audit_registration(payload)


def audit_registration(payload: dict) -> str:
    store.audit("register", payload["name"], payload.get("role", ""))
    return payload["name"]


def refresh(name: str) -> dict:
    host = store.host(name)
    return measure(host) if host else {}


def measure(host: dict) -> dict:
    return persist(host, checks.values(host))


def persist(host: dict, measured: tuple[dict, ...]) -> dict:
    record(host["name"], measured)
    return {"host": host["name"], "status": checks.host_status(measured), "checks": measured}


def record(name: str, measured: tuple[dict, ...]) -> None:
    store.save_checks(name, measured)
    store.audit("check", name, f"метрик: {len(measured)}")


def refresh_all() -> tuple[dict, ...]:
    return tuple(refresh(host["name"]) for host in store.hosts())


def host_card(name: str) -> dict:
    host = store.host(name)
    return {**host, "checks": store.checks(name), "status": card_status(store.checks(name))} if host else {}


def card_status(measured: tuple[dict, ...]) -> str:
    return checks.host_status(measured) if measured else "unknown"


def inventory() -> tuple[dict, ...]:
    return tuple(host_card(host["name"]) for host in store.hosts())


def overview() -> dict:
    cards = inventory()
    return {
        "hosts": cards,
        "stats": {
            "total": len(cards),
            "by_status": count_status(cards),
            "by_os": count_os(cards),
            "problems": tuple(item["name"] for item in cards if item["status"] != "ok"),
        },
    }


def count_status(cards: tuple[dict, ...]) -> dict[str, int]:
    names = {card["status"] for card in cards}
    return {name: sum(1 for card in cards if card["status"] == name) for name in names}


def count_os(cards: tuple[dict, ...]) -> dict[str, int]:
    names = {card["os"] for card in cards}
    return {name: sum(1 for card in cards if card["os"] == name) for name in names}


def playbook(os_name: str) -> dict:
    return {
        "os": os_name.lower(),
        "items": list(playbooks.playbook(os_name)),
        "available": list(playbooks.os_names()),
    }


def journal(limit: int) -> tuple[dict, ...]:
    return store.journal(limit)


def problems() -> tuple[dict, ...]:
    return tuple(
        {"host": card["name"], "metric": check["metric"], "value": check["value"], "status": check["status"]}
        for card in inventory()
        for check in card["checks"]
        if check["status"] != "ok"
    )

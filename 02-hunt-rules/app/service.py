"""Сценарии: библиотека правил, прогон по событиям, сохранение детекций."""
from pathlib import Path

from app import config, engine, events, rules, store


def library() -> tuple[rules.Rule, ...]:
    return packaged() + custom()


def packaged() -> tuple[rules.Rule, ...]:
    return tuple(load_rule(path) for path in sorted(config.RULES_DIR.glob("*.yaml")))


def load_rule(path: Path) -> rules.Rule:
    return rules.parse(path.read_text(encoding="utf-8"), path.name)


def custom() -> tuple[rules.Rule, ...]:
    return tuple(rules.parse(row["yaml"], f"db:{row['id']}") for row in store.custom_rules())


def describe() -> tuple[dict, ...]:
    return tuple(rules.as_dict(rule) for rule in library())


def add_custom(text: str) -> dict:
    return persist_rule(rules.parse(text, "custom"), text)


def persist_rule(rule: rules.Rule, text: str) -> dict:
    store.save_rule(rule.id, rule.title, text)
    return rules.as_dict(rule)


def run(rule_ids: tuple[str, ...] = ()) -> dict:
    return summarize(pick(rule_ids), events.load())


def pick(rule_ids: tuple[str, ...]) -> tuple[rules.Rule, ...]:
    return tuple(rule for rule in library() if not rule_ids or rule.id in rule_ids)


def summarize(selected: tuple[rules.Rule, ...], stream: tuple[dict, ...]) -> dict:
    findings = tuple(finding(item, stream) for item in selected)
    return {"events": len(stream), "findings": findings, "total": sum(item["hits"] for item in findings)}


def finding(rule: rules.Rule, stream: tuple[dict, ...]) -> dict:
    matched = engine.hits(rule, stream)
    return {**rules.as_dict(rule), "hits": len(matched), "matches": matched[:10]}


def replay(rule_ids: tuple[str, ...] = ()) -> dict:
    return persist(run(rule_ids))


def persist(summary: dict) -> dict:
    rows = tuple(row for item in summary["findings"] for row in detection_rows(item))
    return {**summary, "saved": store.save_detections(rows)}


def detection_rows(item: dict) -> tuple[tuple, ...]:
    return tuple(detection_row(item, event) for event in item["matches"])


def detection_row(item: dict, event: dict) -> tuple:
    return (item["id"], event["id"], event.get("host", ""), event.get("ts", ""), item["title"])


def stored_detections() -> tuple[dict, ...]:
    return store.detections()


def event_count() -> int:
    return len(events.load())


def rule_sources() -> tuple[str, ...]:
    return tuple(sorted(path.name for path in Path(config.RULES_DIR).glob("*.yaml")))

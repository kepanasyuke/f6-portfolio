"""Модель правила хантинга и разбор YAML-описания."""
from dataclasses import dataclass
from typing import NoReturn

import yaml


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    tactic: str
    technique: str
    condition: str
    selection: dict
    source: str = ""


def parse(text: str, source: str = "") -> Rule:
    return require(build(yaml.safe_load(text), source))


def build(payload: dict, source: str) -> Rule:
    data = payload if isinstance(payload, dict) else {}
    return Rule(
        id=str(data.get("id", "")).strip(),
        title=str(data.get("title", "")).strip(),
        severity=str(data.get("severity", "medium")).lower(),
        tactic=str(data.get("tactic", "")).strip(),
        technique=str(data.get("technique", "")).strip(),
        condition=str(data.get("condition", "all")).lower(),
        selection=dict(data.get("selection") or {}),
        source=source,
    )


def require(rule: Rule) -> Rule:
    return rule if rule.id and rule.title and rule.selection else reject(rule)


def reject(rule: Rule) -> NoReturn:
    raise ValueError(f"правило {rule.id or rule.title or '?'} без id, названия или selection")


def as_dict(rule: Rule) -> dict:
    return {
        "id": rule.id,
        "title": rule.title,
        "severity": rule.severity,
        "tactic": rule.tactic,
        "technique": rule.technique,
        "condition": rule.condition,
        "selection": rule.selection,
        "source": rule.source,
    }

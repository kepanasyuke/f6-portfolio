"""Движок: применение правила к потоку событий."""
from app import matchers
from app.rules import Rule


def matches(event: dict, rule: Rule) -> bool:
    checks = tuple(matchers.match_field(event, field, expected) for field, expected in rule.selection.items())
    return evaluate_checks(checks, rule.condition)


def evaluate_checks(checks: tuple[bool, ...], condition: str) -> bool:
    return any(checks) if condition == "any" else all(checks)


def hits(rule: Rule, events: tuple[dict, ...]) -> tuple[dict, ...]:
    return tuple(event for event in events if matches(event, rule))


def evaluate(rules: tuple[Rule, ...], events: tuple[dict, ...]) -> tuple[dict, ...]:
    return tuple(verdict(rule, hits(rule, events)) for rule in rules)


def verdict(rule: Rule, matched: tuple[dict, ...]) -> dict:
    return {"rule": rule, "hits": matched}

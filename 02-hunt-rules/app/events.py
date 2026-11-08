"""Источник событий: синтетический поток в формате JSON Lines."""
import json

from app import config


def load() -> tuple[dict, ...]:
    return parse(config.EVENTS_FILE.read_text(encoding="utf-8"))


def parse(text: str) -> tuple[dict, ...]:
    return tuple(json.loads(line) for line in text.splitlines() if line.strip())


def by_id(identifier: str) -> dict:
    return next((event for event in load() if event["id"] == identifier), {})

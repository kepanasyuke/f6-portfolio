"""Примитивы сопоставления: точечные поля, точное значение, glob, регулярка."""
import fnmatch
import re

REGEX_PREFIX = "re:"


def dig(event: dict, field: str):
    head, _, tail = field.partition(".")
    return child(event, field) if not tail or has(event, field) else dig(child(event, head), tail)


def has(event: dict, field: str) -> bool:
    return isinstance(event, dict) and field in event


def child(event: dict, head: str):
    return event.get(head, "") if isinstance(event, dict) else ""


def match_field(event: dict, field: str, expected) -> bool:
    return match_value(dig(event, field), expected)


def match_value(actual, expected) -> bool:
    return any(single(actual, item) for item in as_list(expected))


def as_list(expected) -> list:
    return expected if isinstance(expected, list) else [expected]


def single(actual, expected) -> bool:
    text = str(expected)
    return regex_hit(actual, cut(text)) if text.startswith(REGEX_PREFIX) else glob_hit(actual, text)


def cut(text: str) -> str:
    return text[len(REGEX_PREFIX) :]


def glob_hit(actual, pattern: str) -> bool:
    return fnmatch.fnmatchcase(str(actual).lower(), pattern.lower())


def regex_hit(actual, pattern: str) -> bool:
    return bool(re.search(pattern, str(actual)))

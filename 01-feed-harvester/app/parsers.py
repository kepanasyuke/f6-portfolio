"""Парсеры фидов: CSV, JSON и построчный текст с обфускацией ([.] и hxxp)."""
import csv
import io
import json
import re
from pathlib import Path

FIELDS = ("value", "severity", "source", "confidence", "first_seen", "tags")
REFANG_RULES = (
    (r"hxxps", "https"),
    (r"hxxp", "http"),
    (r"\[\.\]", "."),
    (r"\(\.\)", "."),
    (r"\[:\]", ":"),
    (r"\[at\]", "@"),
    (r"\s+", ""),
)
KIND_PATTERNS = (
    ("ipv4", re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")),
    ("sha256", re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)),
    ("md5", re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)),
    ("url", re.compile(r"^https?://\S+$", re.IGNORECASE)),
    ("email", re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)),
    ("domain", re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,}$", re.IGNORECASE)),
)
SEVERITIES = ("low", "medium", "high", "critical")


def refang(value: str) -> str:
    return cleanup(value)


def cleanup(value: str) -> str:
    return fold(str(value or ""), REFANG_RULES)


def fold(value: str, rules: tuple) -> str:
    return value if not rules else fold(re.sub(rules[0][0], rules[0][1], value), rules[1:])


def detect_kind(value: str) -> str:
    return next((kind for kind, pattern in KIND_PATTERNS if pattern.match(value)), "")


def parse(format_name: str, content: str) -> tuple[tuple[dict, ...], int]:
    return DECODERS.get(format_name, decode_text)(content)


def split_records(rows: tuple[dict, ...]) -> tuple[tuple[dict, ...], int]:
    accepted = tuple(row for row in rows if row["kind"])
    return accepted, len(rows) - len(accepted)


def normalize_row(row: dict, default_source: str) -> dict:
    value = refang(pick(row, "value", "indicator", "ioc", "address"))
    return {
        "value": value,
        "kind": detect_kind(value),
        "severity": severity_of(pick(row, "severity", "risk", "level")),
        "source": pick(row, "source", "feed", "provider") or default_source,
        "confidence": confidence_of(pick(row, "confidence", "score", "weight")),
        "first_seen": pick(row, "first_seen", "date", "seen"),
        "tags": tags_of(pick(row, "tags", "tag", "labels")),
    }


def pick(row: dict, *names: str) -> str:
    return normalize_key(find_value(lowered(row), names))


def lowered(row: dict) -> dict:
    return {str(key).strip().lower(): value for key, value in row.items()}


def find_value(row: dict, names: tuple) -> str:
    return next((row[name] for name in names if row.get(name)), "")


def normalize_key(value: str) -> str:
    return str(value).strip()


def severity_of(value: str) -> str:
    return value.lower() if value.lower() in SEVERITIES else "medium"


def confidence_of(value: str) -> int:
    return clamp_int(value)


def clamp_int(value: str | int) -> int:
    return max(0, min(100, signed_int(value)))


def signed_int(value: str | int) -> int:
    text = re.sub(r"[^\d-]", "", str(value)) or "0"
    return 0 if text == "-" else int(text)


def tags_of(value: str) -> str:
    return ",".join(part.strip() for part in re.split(r"[,;|]", str(value)) if part.strip())


def decode_csv(content: str) -> tuple[tuple[dict, ...], int]:
    rows = tuple(normalize_row(row, "csv-feed") for row in csv.DictReader(io.StringIO(content)))
    return split_records(rows)


def decode_json(content: str) -> tuple[tuple[dict, ...], int]:
    payload = json.loads(content)
    return split_records(tuple(normalize_row(item, "json-feed") for item in as_items(payload)))


def as_items(payload: object) -> tuple[dict, ...]:
    return tuple(payload if isinstance(payload, list) else payload.get("data", []))


def decode_text(content: str) -> tuple[tuple[dict, ...], int]:
    rows = tuple(to_row(line) for line in content.splitlines() if usable(line))
    return split_records(tuple(normalize_row(row, "text-feed") for row in rows))


def usable(line: str) -> bool:
    return bool(line.strip()) and not line.strip().startswith("#")


def to_row(line: str) -> dict:
    return dict(zip(FIELDS, fields(line), strict=False))


def fields(line: str) -> list[str]:
    return re.split(r"[\t|;]+", line.strip(), maxsplit=len(FIELDS))


def format_of(name: str) -> str:
    return Path(name).suffix.lstrip(".").lower() or "txt"


DECODERS = {"csv": decode_csv, "json": decode_json, "txt": decode_text, "text": decode_text}

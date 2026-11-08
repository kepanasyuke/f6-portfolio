"""Конфигурация сервиса Hunt Rules."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
RULES_DIR = PROJECT_DIR / "data" / "rules"
EVENTS_FILE = PROJECT_DIR / "data" / "events.jsonl"
DEFAULT_DB = PROJECT_DIR / "data" / "hunt.sqlite3"
SERVICE_NAME = "hunt-rules"
VERSION = "1.0.0"


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))

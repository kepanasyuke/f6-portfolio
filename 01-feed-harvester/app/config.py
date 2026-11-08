"""Конфигурация сервиса Feed Harvester."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
FEEDS_DIR = PROJECT_DIR / "data" / "feeds"
DEFAULT_DB = PROJECT_DIR / "data" / "iocs.sqlite3"
SERVICE_NAME = "feed-harvester"
VERSION = "1.0.0"


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))


def ensure_dirs() -> None:
    db_path().parent.mkdir(parents=True, exist_ok=True)

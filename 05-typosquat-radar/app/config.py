"""Конфигурация сервиса Typosquat Radar."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
DATA_DIR = PROJECT_DIR / "data"
DEFAULT_DB = DATA_DIR / "radar.sqlite3"
SERVICE_NAME = "typosquat-radar"
VERSION = "1.0.0"
BRAND = "f6security.example"
RISKY_TLDS = ("zip", "mov", "co", "top", "xyz", "click", "link", "support")


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))

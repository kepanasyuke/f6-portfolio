"""Конфигурация сервиса Log Forge."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
LOGS_DIR = PROJECT_DIR / "data" / "logs"
DEFAULT_DB = PROJECT_DIR / "data" / "logs.sqlite3"
SERVICE_NAME = "log-forge"
VERSION = "1.0.0"
DEFAULT_YEAR = 2026


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))

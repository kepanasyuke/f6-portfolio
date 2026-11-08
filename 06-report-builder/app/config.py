"""Конфигурация сервиса Report Builder."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
DATA_DIR = PROJECT_DIR / "data"
DEFAULT_DB = DATA_DIR / "reports.sqlite3"
SERVICE_NAME = "report-builder"
VERSION = "1.0.0"
TLP = ("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED")


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))

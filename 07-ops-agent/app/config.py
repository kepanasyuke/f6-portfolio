"""Конфигурация сервиса Ops Agent."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
DATA_DIR = PROJECT_DIR / "data"
HOSTS_FILE = DATA_DIR / "hosts.json"
DEFAULT_DB = DATA_DIR / "ops.sqlite3"
SERVICE_NAME = "ops-agent"
VERSION = "1.0.0"


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))

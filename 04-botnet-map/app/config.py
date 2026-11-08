"""Конфигурация сервиса Botnet Map."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = PROJECT_DIR.parent / "shared"
DATA_DIR = PROJECT_DIR / "data"
GRAPH_FILE = DATA_DIR / "graph.json"
SCHEMA_FILE = DATA_DIR / "schema.postgres.sql"
DEFAULT_DB = DATA_DIR / "graph.sqlite3"
SERVICE_NAME = "botnet-map"
VERSION = "1.0.0"
MAX_DEPTH = 4


def db_path() -> Path:
    return Path(os.environ.get("F6_DB", str(DEFAULT_DB)))

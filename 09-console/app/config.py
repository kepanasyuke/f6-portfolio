"""Конфигурация консоли: реестр сервисов стенда."""
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = PROJECT_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = ROOT_DIR / "shared"
SERVICE_NAME = "console"
VERSION = "1.0.0"
PORT = 8210
TIMEOUT = 4.0

SERVICES = (
    {"key": "iocs", "title": "Индикаторы", "port": 8201, "summary": "/api/stats"},
    {"key": "hunt", "title": "Хантинг", "port": 8202, "summary": "/api/detections"},
    {"key": "logs", "title": "Журналы", "port": 8203, "summary": "/api/stats"},
    {"key": "graph", "title": "Инфраструктура", "port": 8204, "summary": "/api/stats"},
    {"key": "radar", "title": "Домены", "port": 8205, "summary": "/api/stats"},
    {"key": "reports", "title": "Отчёты", "port": 8206, "summary": "/api/metrics"},
    {"key": "ops", "title": "Хосты", "port": 8207, "summary": "/api/overview"},
)


def service(key: str) -> dict:
    return next((item for item in SERVICES if item["key"] == key), {})


def base(service_item: dict) -> str:
    return f"http://127.0.0.1:{service_item['port']}"


def summary_url(service_item: dict) -> str:
    return base(service_item) + service_item["summary"]


def endpoint(key: str, path: str) -> str:
    found = service(key)
    return base(found) + path if found else ""

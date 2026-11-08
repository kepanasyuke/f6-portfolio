"""Конфигурация портала данных: реестр баз стенда и KPI."""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = PROJECT_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SHARED_DIR = ROOT_DIR / "shared"
SERVICE_NAME = "data-portal"
VERSION = "1.0.0"
PORT = 8109

REGISTRY = (
    {
        "key": "iocs",
        "title": "Индикаторы компрометации",
        "service": "Feed Harvester",
        "port": 8101,
        "db": "01-feed-harvester/data/iocs.sqlite3",
    },
    {
        "key": "hunt",
        "title": "Правила и детекции",
        "service": "Hunt Rules",
        "port": 8102,
        "db": "02-hunt-rules/data/hunt.sqlite3",
    },
    {
        "key": "logs",
        "title": "Нормализованные журналы",
        "service": "Log Forge",
        "port": 8103,
        "db": "03-log-forge/data/logs.sqlite3",
    },
    {
        "key": "graph",
        "title": "Граф инфраструктуры",
        "service": "Botnet Map",
        "port": 8104,
        "db": "04-botnet-map/data/graph.sqlite3",
    },
    {
        "key": "radar",
        "title": "Похожие домены",
        "service": "Typosquat Radar",
        "port": 8105,
        "db": "05-typosquat-radar/data/radar.sqlite3",
    },
    {
        "key": "reports",
        "title": "Отчёты портала",
        "service": "Report Builder",
        "port": 8106,
        "db": "06-report-builder/data/reports.sqlite3",
    },
    {
        "key": "ops",
        "title": "Инвентарь и метрики",
        "service": "Ops Agent",
        "port": 8107,
        "db": "07-ops-agent/data/ops.sqlite3",
    },
)

KPIS = (
    {"title": "Индикаторы", "hint": "база IOC", "db": "iocs", "sql": "SELECT COUNT(*) AS value FROM iocs"},
    {
        "title": "Детекции",
        "hint": "срабатывания правил",
        "db": "hunt",
        "sql": "SELECT COUNT(*) AS value FROM detections",
    },
    {
        "title": "Журналы",
        "hint": "нормализованные события",
        "db": "logs",
        "sql": "SELECT COUNT(*) AS value FROM log_events",
    },
    {
        "title": "Узлы графа",
        "hint": "инфраструктура",
        "db": "graph",
        "sql": "SELECT COUNT(*) AS value FROM nodes",
    },
    {
        "title": "Связи графа",
        "hint": "рёбра с уверенностью",
        "db": "graph",
        "sql": "SELECT COUNT(*) AS value FROM edges",
    },
    {
        "title": "Домены под риском",
        "hint": "verdict = critical",
        "db": "radar",
        "sql": "SELECT COUNT(*) AS value FROM scans WHERE verdict = 'critical'",
    },
    {
        "title": "Отчёты",
        "hint": "для портала TI",
        "db": "reports",
        "sql": "SELECT COUNT(*) AS value FROM reports",
    },
    {
        "title": "Проблемы хостов",
        "hint": "warn и critical",
        "db": "ops",
        "sql": "SELECT COUNT(*) AS value FROM checks WHERE status != 'ok'",
    },
)


def root() -> Path:
    return Path(os.environ.get("F6_DATA_ROOT", str(ROOT_DIR)))


def db_path(source: dict) -> Path:
    return root() / source["db"]


def source(key: str) -> dict:
    return next((item for item in REGISTRY if item["key"] == key), {})

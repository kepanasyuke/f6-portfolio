import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

IOCS = """
CREATE TABLE iocs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    confidence INTEGER NOT NULL DEFAULT 50
);
"""
SCANS = """
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    domain TEXT NOT NULL,
    risk INTEGER NOT NULL,
    verdict TEXT NOT NULL
);
"""
ROWS = (
    ("203.0.113.24", "ipv4", "critical", 94),
    ("cdn-login.example.com", "domain", "high", 88),
    ("update.example.co", "domain", "medium", 61),
)


def build(root: Path) -> None:
    write_iocs(root / "01-feed-harvester/data/iocs.sqlite3")
    write_scans(root / "05-typosquat-radar/data/radar.sqlite3")


def write_iocs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(IOCS)
    connection.executemany("INSERT INTO iocs (value, kind, severity, confidence) VALUES (?, ?, ?, ?)", ROWS)
    connection.commit()
    connection.close()


def write_scans(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(SCANS)
    connection.executemany(
        "INSERT INTO scans (brand, domain, risk, verdict) VALUES (?, ?, ?, ?)",
        (("f6security.example", "f6securit.example", 88, "critical"), ("f6security.example", "f6.co", 40, "medium")),
    )
    connection.commit()
    connection.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    build(tmp_path)
    monkeypatch.setenv("F6_DATA_ROOT", str(tmp_path))
    from app.main import create_app

    return TestClient(create_app())

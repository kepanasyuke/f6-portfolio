import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("F6_DB", str(tmp_path / "radar.sqlite3"))
    from app.main import create_app

    return TestClient(create_app())

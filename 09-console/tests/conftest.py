import httpx
import pytest
from fastapi.testclient import TestClient

SUMMARIES = {
    "/api/stats": {"total": 12, "documents": 22, "nodes": 20, "edges": 26, "verdicts": {"critical": 12}},
    "/api/detections": {"items": [{"rule_id": "F6-0001", "host": "fin-ws-07"}]},
    "/api/metrics": {"reports": 3},
    "/api/overview": {"stats": {"by_status": {"critical": 6}, "problems": ["fin-ws-07"]}},
}


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.port == 8199:
        raise httpx.ConnectError("сервис недоступен", request=request)
    return httpx.Response(200, json=payload(request))


def payload(request: httpx.Request) -> dict:
    return SUMMARIES.get(request.url.path, {"items": [], "columns": [], "total": 0})


@pytest.fixture()
def client(monkeypatch):
    from app import client as http_client
    from app.main import create_app

    http_client.TRANSPORT["value"] = httpx.MockTransport(handler)
    yield TestClient(create_app())
    http_client.TRANSPORT["value"] = None


@pytest.fixture()
def offline(client, monkeypatch):
    from app import config

    services = tuple({**item, "port": 8199} for item in config.SERVICES)
    monkeypatch.setattr(config, "SERVICES", services)
    return client

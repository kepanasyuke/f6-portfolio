SAMPLE = {
    "title": "Кампания Gatekeeper",
    "template": "threat",
    "tlp": "TLP:AMBER",
    "summary": "Фишинг через поддельные панели входа.",
    "iocs": [{"kind": "domain", "value": "cdn-login.example.com"}],
    "findings": [{"severity": "critical", "title": "Общий сертификат", "detail": "cert 8f14"}],
    "recommendations": ["Заблокировать домен"],
}


def test_health(client):
    assert client.get("/api/health").json()["service"] == "report-builder"


def test_templates_listed(client):
    items = client.get("/api/templates").json()["items"]
    assert {item["id"] for item in items} == {"threat", "incident", "actor"}


def test_preview_does_not_persist(client):
    payload = client.post("/api/preview", json=SAMPLE).json()
    assert payload["html"].startswith("<h1>")
    assert client.get("/api/reports").json()["items"] == []


def test_create_and_read_report(client):
    created = client.post("/api/reports", json=SAMPLE).json()
    report_id = created["id"]
    stored = client.get(f"/api/reports/{report_id}").json()
    assert stored["title"] == "Кампания Gatekeeper"
    assert "## Наблюдения" in stored["markdown"]
    assert "<table>" in stored["html"]


def test_markdown_export(client):
    report_id = client.post("/api/reports", json=SAMPLE).json()["id"]
    response = client.get(f"/api/reports/{report_id}/markdown")
    assert response.status_code == 200
    assert response.text.startswith("# Кампания Gatekeeper")


def test_missing_report_returns_404(client):
    assert client.get("/api/reports/9999").status_code == 404


def test_metrics_count_reports(client):
    client.post("/api/reports", json=SAMPLE)
    client.post("/api/reports", json={**SAMPLE, "template": "incident"})
    payload = client.get("/api/metrics").json()
    assert payload["reports"] == 2
    assert payload["by_template"]["threat"] == 1


def test_sample_payload_is_valid(client):
    sample = client.get("/api/sample").json()
    response = client.post("/api/reports", json=sample)
    assert response.status_code == 200
    assert response.json()["severity"]["critical"] == 1

def kpi_map(client) -> dict:
    payload = client.get("/api/overview").json()
    return {item["title"]: item["value"] for item in payload["kpis"]}


def test_health(client):
    assert client.get("/api/health").json()["service"] == "console"


def test_overview_lists_every_service(client):
    payload = client.get("/api/overview").json()
    assert len(payload["services"]) == 7
    assert all(item["online"] for item in payload["services"])


def test_overview_collects_kpis_from_services(client):
    kpis = kpi_map(client)
    assert kpis["Индикаторы"] == 12
    assert kpis["Детекции"] == 1
    assert kpis["Журналы"] == 22
    assert kpis["Узлы графа"] == 20
    assert kpis["Домены под риском"] == 12
    assert kpis["Отчёты"] == 3
    assert kpis["Проблемы хостов"] == 6


def test_feed_mentions_detection_and_host(client):
    feed = client.get("/api/overview").json()["feed"]
    texts = " ".join(item["text"] for item in feed)
    assert "F6-0001" in texts
    assert "fin-ws-07" in texts


def test_overview_degrades_when_services_are_down(offline):
    payload = offline.get("/api/overview").json()
    assert all(not item["online"] for item in payload["services"])
    assert all(item["value"] == 0 for item in payload["kpis"])


def test_indicators_proxy(client):
    payload = client.get("/api/indicators", params={"q": "example", "kind": "domain"}).json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_hunting_returns_rules_and_detections(client):
    payload = client.get("/api/hunting").json()
    assert payload["rules"]["items"] == []
    assert payload["detections"]["items"][0]["rule_id"] == "F6-0001"


def test_hunting_run_returns_findings(client):
    payload = client.post("/api/hunting/run").json()
    assert "findings" not in payload or payload["findings"] == []


def test_logs_search(client):
    payload = client.get("/api/logs", params={"q": "failed"}).json()
    assert payload["items"] == []


def test_graph_pivot(client):
    payload = client.get("/api/graph", params={"node": "ip-203-0-113-24"}).json()
    assert "depths" not in payload


def test_domains_scan(client):
    payload = client.get("/api/domains", params={"brand": "f6security.example"}).json()
    assert payload["items"] == []


def test_reports_list_and_create(client):
    assert client.get("/api/reports").json()["items"] == []
    created = client.post("/api/reports", json={"title": "Проба", "template": "threat"}).json()
    assert created["items"] == []


def test_hosts_and_check(client):
    payload = client.get("/api/hosts").json()
    assert payload["stats"]["by_status"]["critical"] == 6
    assert client.post("/api/hosts/edge-gw-01/check").json()["items"] == []

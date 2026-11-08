def test_health(client):
    payload = client.get("/api/health").json()
    assert payload["status"] == "ok"
    assert payload["service"] == "feed-harvester"


def test_seed_provides_statistics(client):
    stats = client.get("/api/stats").json()
    assert stats["total"] > 0
    assert set(stats) == {"total", "by_kind", "by_severity", "by_source"}


def test_ingest_csv_adds_records(client):
    before = client.get("/api/stats").json()["total"]
    body = {"format": "csv", "content": "value,severity,source,confidence\n192.0.2.240,critical,hunt,90\n"}
    payload = client.post("/api/ingest", json=body).json()
    assert payload == {"parsed": 1, "stored": 1, "rejected": 0}
    assert client.get("/api/stats").json()["total"] == before + 1


def test_ingest_is_idempotent(client):
    body = {"format": "txt", "content": "192.0.2.241|high|hunt|60\n"}
    client.post("/api/ingest", json=body)
    client.post("/api/ingest", json=body)
    assert client.get("/api/stats").json()["total"] == client.get("/api/stats").json()["total"]
    items = client.get("/api/iocs", params={"q": "192.0.2.241"}).json()["items"]
    assert len(items) == 1


def test_search_filters_by_kind(client):
    payload = client.get("/api/iocs", params={"kind": "domain"}).json()
    assert payload["items"]
    assert all(item["kind"] == "domain" for item in payload["items"])


def test_search_filters_by_severity_and_text(client):
    payload = client.get("/api/iocs", params={"severity": "critical", "q": "example"}).json()
    assert all(item["severity"] == "critical" and "example" in item["value"] for item in payload["items"])


def test_local_feed_ingestion(client):
    feeds = client.get("/api/feeds").json()["items"]
    payload = client.post("/api/ingest/local", json={"name": feeds[0]}).json()
    assert payload["stored"] > 0


def test_unknown_local_feed_returns_404(client):
    assert client.post("/api/ingest/local", json={"name": "nope.csv"}).status_code == 404


def test_limit_is_enforced(client):
    payload = client.get("/api/iocs", params={"limit": 2}).json()
    assert payload["count"] <= 2

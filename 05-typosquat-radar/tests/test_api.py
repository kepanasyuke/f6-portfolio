def test_health(client):
    assert client.get("/api/health").json()["service"] == "typosquat-radar"


def test_scan_returns_ranked_variants(client):
    payload = client.post("/api/scan", json={"brand": "f6security.example", "limit": 12}).json()
    assert payload["generated"] > 20
    assert len(payload["items"]) == 12
    risks = [item["risk"] for item in payload["items"]]
    assert risks == sorted(risks, reverse=True)


def test_scan_persists_history(client):
    client.post("/api/scan", json={"brand": "acme.example", "limit": 5})
    items = client.get("/api/scans", params={"limit": 10}).json()["items"]
    assert any(item["brand"] == "acme.example" for item in items)


def test_check_scores_unknown_domain(client):
    payload = client.get("/api/check", params={"domain": "f6security.exampl", "brand": "f6security.example"}).json()
    assert payload["domain"] == "f6security.exampl"
    assert payload["distance"] == 1
    assert 0 <= payload["risk"] <= 100


def test_watchlist_roundtrip(client):
    client.post("/api/watchlist", json={"domain": "f6security-example.top", "note": "ручная проверка"})
    items = client.get("/api/watchlist").json()["items"]
    assert items[0]["domain"] == "f6security-example.top"
    assert items[0]["note"] == "ручная проверка"


def test_statistics_exposes_techniques(client):
    payload = client.get("/api/stats").json()
    assert payload["scanned"] > 0
    assert "omissions" in payload["techniques"]
    assert payload["brand"] == "f6security.example"


def test_seed_fills_database(client):
    assert client.get("/api/stats").json()["scanned"] >= 20

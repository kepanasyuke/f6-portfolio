def test_health(client):
    assert client.get("/api/health").json()["service"] == "log-forge"


def test_seed_builds_index(client):
    payload = client.get("/api/stats").json()
    assert payload["documents"] >= 15
    assert payload["terms"] > 20
    assert "authentication" in payload["categories"]


def test_search_finds_failed_logins(client):
    payload = client.post("/api/search", json={"query": "failed root", "limit": 10}).json()
    assert payload["count"] >= 1
    assert payload["items"][0]["user.name"] == "root"


def test_search_by_ip_mask(client):
    payload = client.post("/api/search", json={"query": "203.0.113.*", "limit": 10}).json()
    assert payload["count"] >= 1


def test_ingest_adds_document(client):
    body = {"format": "syslog", "content": "Oct  2 14:11:05 gw sshd[4200]: Failed password for root from 192.0.2.44 port 1 ssh2", "prefix": "manual"}
    before = client.get("/api/stats").json()["documents"]
    payload = client.post("/api/ingest", json=body).json()
    assert payload["stored"] == 1
    assert payload["documents"] == before + 1


def test_reindex_keeps_documents(client):
    before = client.get("/api/stats").json()["documents"]
    payload = client.post("/api/reindex", json={}).json()
    assert payload["documents"] == before


def test_mapping_has_key_fields(client):
    properties = client.get("/api/mapping").json()["mappings"]["properties"]
    assert properties["source.ip"]["type"] == "ip"
    assert properties["@timestamp"]["type"] == "date"


def test_recent_returns_documents(client):
    assert client.get("/api/logs", params={"limit": 5}).json()["items"]

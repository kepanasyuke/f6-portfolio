def test_health(client):
    assert client.get("/api/health").json()["service"] == "ops-agent"


def test_seed_loads_inventory(client):
    payload = client.get("/api/overview").json()
    assert payload["stats"]["total"] >= 8
    assert payload["hosts"][0]["checks"]


def test_host_detail_has_all_metrics(client):
    payload = client.get("/api/hosts/edge-gw-01").json()
    assert len(payload["checks"]) == 6
    assert payload["status"] in ("ok", "warn", "critical")


def test_unknown_host_returns_404(client):
    assert client.get("/api/hosts/nope").status_code == 404


def test_check_records_journal(client):
    client.post("/api/hosts/web-01/check", json={})
    journal = client.get("/api/journal").json()["items"]
    assert journal[0]["action"] == "check"
    assert journal[0]["target"] == "web-01"


def test_check_all_returns_every_host(client):
    payload = client.post("/api/check-all", json={}).json()
    assert len(payload["results"]) >= 8


def test_problems_only_lists_bad_checks(client):
    items = client.get("/api/problems").json()["items"]
    assert all(item["status"] in ("warn", "critical") for item in items)


def test_register_new_host(client):
    payload = client.post(
        "/api/hosts",
        json={"name": "web-03", "role": "web", "os": "linux", "ip": "198.51.100.23", "owner": "product", "tags": "nginx"},
    ).json()
    assert payload["name"] == "web-03"
    assert client.get("/api/overview").json()["stats"]["total"] >= 9


def test_playbook_by_os(client):
    payload = client.get("/api/playbook", params={"os": "windows"}).json()
    assert payload["os"] == "windows"
    assert any(item["id"].startswith("win-") for item in payload["items"])


def test_checks_are_stable_between_runs(client):
    first = client.post("/api/hosts/db-01/check", json={}).json()
    second = client.post("/api/hosts/db-01/check", json={}).json()
    assert [item["value"] for item in first["checks"]] == [item["value"] for item in second["checks"]]

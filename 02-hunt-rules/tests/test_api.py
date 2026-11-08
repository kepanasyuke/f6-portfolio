def test_health(client):
    assert client.get("/api/health").json()["service"] == "hunt-rules"


def test_packaged_rules_are_loaded(client):
    payload = client.get("/api/rules").json()
    assert len(payload["items"]) >= 4
    assert {item["id"] for item in payload["items"]} >= {"F6-0001", "F6-0002"}


def test_evaluate_returns_findings(client):
    payload = client.post("/api/evaluate", json={"rule_ids": []}).json()
    assert payload["events"] > 0
    assert payload["total"] >= 1
    assert all("hits" in item for item in payload["findings"])


def test_evaluate_can_filter_rules(client):
    payload = client.post("/api/evaluate", json={"rule_ids": ["F6-0002"]}).json()
    assert [item["id"] for item in payload["findings"]] == ["F6-0002"]
    assert payload["findings"][0]["hits"] == 2


def test_replay_persists_detections(client):
    first = client.post("/api/replay", json={"rule_ids": []}).json()
    second = client.post("/api/replay", json={"rule_ids": []}).json()
    stored = client.get("/api/detections").json()["items"]
    assert first["saved"] >= 1
    assert len(stored) == first["saved"] == second["saved"]


def test_validate_reports_valid_rule(client):
    text = "id: F6-1\ntitle: Тест\nselection:\n  a: b\n"
    payload = client.post("/api/validate", json={"text": text}).json()
    assert payload["ok"] is True
    assert payload["rule"]["id"] == "F6-1"


def test_validate_reports_error(client):
    response = client.post("/api/validate", json={"text": "id: F6-2\ntitle: Без селекции\n"})
    assert response.status_code == 400
    assert "selection" in response.json()["error"]


def test_custom_rule_becomes_part_of_library(client):
    text = "id: F6-9000\ntitle: Кастом\nselection:\n  event.type: network\n"
    client.post("/api/rules", json={"text": text})
    ids = {item["id"] for item in client.get("/api/rules").json()["items"]}
    assert "F6-9000" in ids

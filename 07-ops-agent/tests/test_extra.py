"""Дополнительные проверки метрик, чек-листов и API эксплуатации."""
from app import checks, playbooks


def metric(name: str) -> dict:
    return next(item for item in checks.METRICS if item["name"] == name)


def test_every_metric_has_title_and_unit():
    assert all(item["title"] and "unit" in item for item in checks.METRICS)


def test_spread_stays_inside_bounds():
    disk = metric("disk_pct")
    for seed_value in (0, 1, 15, 4095, 65535):
        assert disk["low"] <= checks.spread(seed_value, disk) <= disk["high"]


def test_seed_differs_by_host_and_metric():
    assert checks.seed("a", "disk_pct") != checks.seed("b", "disk_pct")
    assert checks.seed("a", "disk_pct") != checks.seed("a", "memory_pct")


def test_memory_thresholds():
    memory = metric("memory_pct")
    assert checks.status(10, memory) == "ok"
    assert checks.status(90, memory) == "warn"
    assert checks.status(96, memory) == "critical"


def test_patches_thresholds():
    patches = metric("patches_behind")
    assert checks.status(0, patches) == "ok"
    assert checks.status(7, patches) == "warn"
    assert checks.status(20, patches) == "critical"


def test_cert_thresholds_inverted():
    cert = metric("cert_days_left")
    assert checks.status(120, cert) == "ok"
    assert checks.status(15, cert) == "warn"
    assert checks.status(5, cert) == "critical"


def test_failed_logins_thresholds():
    logins = metric("failed_logins_24h")
    assert checks.status(3, logins) == "ok"
    assert checks.status(30, logins) == "warn"
    assert checks.status(50, logins) == "critical"


def test_measures_have_status_field():
    measured = checks.values({"name": "web-01"})
    assert len(measured) == len(checks.METRICS)
    assert all("status" in item for item in measured)


def test_worst_filters_ok_checks():
    measured = ({"status": "ok"}, {"status": "warn"})
    assert checks.worst(measured) == ({"status": "warn"},)


def test_linux_playbook_covers_ssh_and_updates():
    ids = {item["id"] for item in playbooks.playbook("linux")}
    assert {"linux-ssh-root", "linux-updates", "linux-auditd"} <= ids


def test_windows_playbook_covers_laps_and_smb():
    ids = {item["id"] for item in playbooks.playbook("windows")}
    assert {"win-laps", "win-smbtls", "win-bitlocker"} <= ids


def test_playbook_items_have_hint():
    assert all(item["how"] for item in playbooks.playbook("linux"))


def test_inventory_has_status_for_every_host(client):
    hosts = client.get("/api/hosts").json()["items"]
    assert hosts
    assert all(host["status"] in ("ok", "warn", "critical", "unknown") for host in hosts)


def test_overview_counts_match_hosts(client):
    payload = client.get("/api/overview").json()
    assert sum(payload["stats"]["by_status"].values()) == payload["stats"]["total"]


def test_host_detail_lists_six_metrics(client):
    payload = client.get("/api/hosts/db-01").json()
    assert {check["metric"] for check in payload["checks"]} == {item["name"] for item in checks.METRICS}


def test_check_updates_journal_entries(client):
    before = len(client.get("/api/journal", params={"limit": 50}).json()["items"])
    client.post("/api/hosts/web-01/check", json={})
    after = len(client.get("/api/journal", params={"limit": 50}).json()["items"])
    assert after == before + 1


def test_register_creates_host_with_owner(client):
    payload = client.post(
        "/api/hosts",
        json={"name": "web-09", "role": "web", "os": "linux", "ip": "198.51.100.99", "owner": "product"},
    ).json()
    assert payload["owner"] == "product"
    assert payload["checks"] == []


def test_register_rejects_bad_os(client):
    response = client.post("/api/hosts", json={"name": "x-01", "os": "solaris"})
    assert response.status_code == 422


def test_check_unknown_host_returns_404(client):
    assert client.post("/api/hosts/nope/check", json={}).status_code == 404


def test_playbook_defaults_to_linux(client):
    payload = client.get("/api/playbook").json()
    assert payload["os"] == "linux"
    assert payload["available"] == ["linux", "windows"]


def test_journal_limit_is_applied(client):
    assert len(client.get("/api/journal", params={"limit": 2}).json()["items"]) <= 2

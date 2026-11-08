from app import checks, playbooks


def test_every_metric_has_limits():
    for metric in checks.METRICS:
        assert metric["direction"] in ("max", "min")
        assert metric["low"] < metric["high"]


def test_values_are_deterministic():
    host = {"name": "edge-gw-01"}
    assert checks.values(host) == checks.values(host)


def test_status_grows_with_value_for_max_metrics():
    disk = next(metric for metric in checks.METRICS if metric["name"] == "disk_pct")
    assert checks.status(10, disk) == "ok"
    assert checks.status(85, disk) == "warn"
    assert checks.status(99, disk) == "critical"


def test_status_shrinks_value_for_min_metrics():
    cert = next(metric for metric in checks.METRICS if metric["name"] == "cert_days_left")
    assert checks.status(100, cert) == "ok"
    assert checks.status(10, cert) == "warn"
    assert checks.status(1, cert) == "critical"


def test_host_status_takes_worst():
    measured = ({"status": "ok"}, {"status": "warn"}, {"status": "critical"})
    assert checks.host_status(measured) == "critical"
    assert checks.host_status(({"status": "ok"}, {"status": "warn"})) == "warn"
    assert checks.host_status(({"status": "ok"},)) == "ok"


def test_playbooks_cover_both_platforms():
    assert playbooks.os_names() == ("linux", "windows")
    assert len(playbooks.playbook("linux")) >= 5
    assert len(playbooks.playbook("windows")) >= 5
    assert playbooks.playbook("unknown") == playbooks.LINUX

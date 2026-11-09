"""Дополнительные проверки генераторов, скоринга и API радара доменов."""

from app import scoring, service, variants


def test_omissions_keep_length_minus_one():
    produced = variants.omissions("f6security.example")
    assert produced
    assert all(len(variant.split(".")[0]) == len("f6security") - 1 for variant in produced)


def test_repetitions_add_one_character():
    produced = variants.repetitions("f6security.example")
    assert all(len(variant.split(".")[0]) == len("f6security") + 1 for variant in produced)


def test_transpositions_produce_swapped_names():
    produced = variants.transpositions("abcdef.example")
    assert "acbdef.example" in produced


def test_hyphenations_contain_dash():
    assert all("-" in variant.split(".")[0] for variant in variants.hyphenations("f6security.example"))


def test_subdomains_keep_base_domain():
    assert all(variant.endswith(".f6security.example") for variant in variants.subdomains("f6security.example"))


def test_tld_swaps_exclude_original():
    assert "f6security.example" not in variants.tld_swaps("f6security.example")


def test_generate_is_sorted_and_unique():
    produced = service.generate("f6security.example")
    assert list(produced) == sorted(produced)
    assert len(produced) == len(set(produced))


def test_distance_is_zero_for_same_domain():
    assert scoring.distance("f6security.example", "f6security.example") == 0


def test_distance_symmetric():
    assert scoring.distance("abc.example", "abd.example") == scoring.distance("abd.example", "abc.example")


def test_distance_to_empty_string():
    assert scoring.distance("f6security.example", "") == len("f6security.example")


def test_risk_is_bounded():
    for variant in ("f6security.example", "f6security.zip", "f6sеcurity.example"):
        assert 0 <= scoring.risk_of(1, variant, {"registered": True, "mx": True, "http_status": 200}) <= 100


def test_risky_tld_adds_weight():
    plain = scoring.risk_of(1, "f6security.example", {})
    risky = scoring.risk_of(1, "f6security.zip", {})
    assert risky > plain


def test_cyrillic_adds_weight():
    assert scoring.script_bonus("f6sеcurity.example") > 0
    assert scoring.script_bonus("f6security.example") == 0


def test_flag_bonuses_add_up():
    flags = {"registered": True, "mx": True, "http_status": 200}
    assert scoring.flag_bonus(flags) == 16 + 12 + 14


def test_flag_bonus_ignores_not_found():
    assert scoring.flag_bonus({"registered": False, "mx": False, "http_status": 404}) == 0


def test_verdict_boundaries():
    assert scoring.verdict(75) == "critical"
    assert scoring.verdict(74) == "high"
    assert scoring.verdict(55) == "high"
    assert scoring.verdict(54) == "medium"
    assert scoring.verdict(34) == "low"


def test_signals_include_all_keys():
    assert set(scoring.signals("f6security.example")) == {"registered", "mx", "http_status", "created_days_ago"}


def test_assess_returns_verdict_and_signals():
    item = service.assess("f6security.example", "f6security.exampl")
    assert item["verdict"] in ("critical", "high", "medium", "low")
    assert "registered" in item["signals"]


def test_check_normalizes_case(client):
    payload = client.get("/api/check", params={"domain": "F6SECURITY.EXAMPL"}).json()
    assert payload["domain"] == "f6security.exampl"


def test_watchlist_overwrites_note(client):
    client.post("/api/watchlist", json={"domain": "x.example", "note": "первый"})
    client.post("/api/watchlist", json={"domain": "x.example", "note": "второй"})
    items = [item for item in client.get("/api/watchlist").json()["items"] if item["domain"] == "x.example"]
    assert len(items) == 1
    assert items[0]["note"] == "второй"


def test_scan_limit_is_respected(client):
    payload = client.post("/api/scan", json={"brand": "f6security.example", "limit": 3}).json()
    assert len(payload["items"]) == 3


def test_scan_saves_top_variants_only(client):
    payload = client.post("/api/scan", json={"brand": "acme.example", "limit": 4}).json()
    stored = [item for item in client.get("/api/scans", params={"limit": 200}).json()["items"] if item["brand"] == "acme.example"]
    assert len(stored) == 4
    assert payload["items"][0]["risk"] >= payload["items"][-1]["risk"]


def test_stats_top_ordered_by_risk(client):
    payload = client.get("/api/stats").json()
    risks = [item["risk"] for item in payload["top"]]
    assert risks == sorted(risks, reverse=True)

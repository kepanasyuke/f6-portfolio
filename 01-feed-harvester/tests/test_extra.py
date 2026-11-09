"""Дополнительные проверки парсеров, хранилища и сценариев Feed Harvester."""
import pytest
from app import parsers, service, store

CSV = "value,severity,source,confidence\n203.0.113.7,high,fed,81\ncdn.example.com,medium,fed,60\n"


def test_refang_handles_bracket_colon_and_at():
    assert parsers.refang("hxxp[://]evil[.]example[.]com") .startswith("http")
    assert "@" in parsers.refang("analyst[at]example[.]com")


def test_refang_removes_spaces_inside_value():
    assert parsers.refang(" 203.0.113 .5 ") == "203.0.113.5"


def test_refang_keeps_plain_value():
    assert parsers.refang("plain.example.com") == "plain.example.com"


def test_detect_kind_md5_and_email():
    assert parsers.detect_kind("d41d8cd98f00b204e9800998ecf8427e") == "md5"
    assert parsers.detect_kind("analyst@example.com") == "email"


def test_detect_kind_rejects_short_strings():
    assert parsers.detect_kind("ab") == ""
    assert parsers.detect_kind("") == ""


def test_severity_defaults_to_medium():
    assert parsers.severity_of("нечто") == "medium"
    assert parsers.severity_of("CRITICAL") == "critical"


def test_tags_split_and_trim():
    assert parsers.tags_of(" c2; panel |rat ") == "c2,panel,rat"


def test_confidence_boundaries():
    assert parsers.confidence_of("0") == 0
    assert parsers.confidence_of("100") == 100
    assert parsers.confidence_of("88%") == 88


def test_csv_headers_are_case_insensitive():
    content = "VALUE,Severity,Source,Confidence\n203.0.113.8,HIGH,fed,70\n"
    records, rejected = parsers.parse("csv", content)
    assert records[0]["severity"] == "high"
    assert rejected == 0


def test_json_without_data_key_is_rejected():
    records, rejected = parsers.parse("json", '{"items": []}')
    assert records == ()
    assert rejected == 0


def test_text_feed_with_tabs():
    records, _ = parsers.parse("txt", "203.0.113.9\thigh\tfeed\t66\n")
    assert records[0]["source"] == "feed"


def test_empty_content_yields_nothing():
    assert parsers.parse("csv", "")[0] == ()


def test_format_of_unknown_suffix():
    assert parsers.format_of("feed.bin") == "bin"
    assert parsers.format_of("feed") == "txt"


def test_ingest_counts_parsed_and_rejected():
    result = service.ingest("txt", "203.0.113.10|high|fed|70\nмусор|low\n")
    assert result["parsed"] == 1
    assert result["rejected"] == 1


def test_ingest_local_unknown_feed_raises():
    with pytest.raises(FileNotFoundError):
        service.ingest_local("nope.csv")


def test_list_feeds_returns_seed_files():
    feeds = service.list_feeds()
    assert "iocs.csv" in feeds
    assert all(name.endswith((".csv", ".json", ".txt")) for name in feeds)


def test_ensure_seeded_is_idempotent(client):
    before = client.get("/api/stats").json()["total"]
    service.ensure_seeded()
    assert client.get("/api/stats").json()["total"] == before


def test_store_upsert_keeps_higher_confidence(client):
    client.post("/api/ingest", json={"format": "txt", "content": "198.51.100.5|medium|a|40\n"})
    client.post("/api/ingest", json={"format": "txt", "content": "198.51.100.5|high|b|90\n"})
    items = client.get("/api/iocs", params={"q": "198.51.100.5"}).json()["items"]
    assert len(items) == 1
    assert items[0]["confidence"] == 90


def test_store_merges_tags_on_repeat(client):
    client.post("/api/ingest", json={"format": "txt", "content": "192.0.2.77|low|a|30|2026-10-01|c2\n"})
    client.post("/api/ingest", json={"format": "txt", "content": "192.0.2.77|low|a|30|2026-10-01|panel\n"})
    items = client.get("/api/iocs", params={"q": "192.0.2.77"}).json()["items"]
    assert "c2" in items[0]["tags"] and "panel" in items[0]["tags"]


def test_search_by_severity_only(client):
    payload = client.get("/api/iocs", params={"severity": "critical"}).json()
    assert all(item["severity"] == "critical" for item in payload["items"])


def test_search_returns_empty_for_unknown_value(client):
    payload = client.get("/api/iocs", params={"q": "нет-такого-значения"}).json()
    assert payload["items"] == []


def test_offset_skips_records(client):
    first = client.get("/api/iocs", params={"limit": 1, "offset": 0}).json()["items"]
    second = client.get("/api/iocs", params={"limit": 1, "offset": 1}).json()["items"]
    assert first[0]["value"] != second[0]["value"]


def test_stats_groups_are_consistent(client):
    stats = client.get("/api/stats").json()
    assert sum(stats["by_kind"].values()) == stats["total"]
    assert sum(stats["by_severity"].values()) == stats["total"]


def test_group_rejects_unknown_column():
    assert store.group("неизвестная") == {}


def test_ingest_all_reports_each_feed(client):
    payload = client.post("/api/ingest/all", json={}).json()
    assert len(payload["results"]) >= 3
    assert all("stored" in item for item in payload["results"])

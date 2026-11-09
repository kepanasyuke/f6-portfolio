"""Дополнительные проверки движка правил и его API."""
import pytest
from app import engine, events, matchers, rules


def make_rule(selection, condition="all"):
    return rules.build({"id": "T-9", "title": "Проба", "condition": condition, "selection": selection}, "test")


def test_dig_returns_literal_dotted_key():
    assert matchers.dig({"event.type": "network"}, "event.type") == "network"


def test_dig_descends_into_nested_objects():
    assert matchers.dig({"process": {"parent": {"name": "services.exe"}}}, "process.parent.name") == "services.exe"


def test_dig_returns_empty_for_missing_branch():
    assert matchers.dig({"process": {}}, "process.parent.name") == ""


def test_match_value_accepts_list():
    assert matchers.match_value("high", ["low", "high"])


def test_match_value_is_case_insensitive():
    assert matchers.match_value("High", "high")


def test_regex_is_case_insensitive_when_asked():
    assert matchers.match_field({"c": "IEX Payload"}, "c", "re:(?i)iex")


def test_glob_question_mark():
    assert matchers.match_field({"host": "fin-ws-07"}, "host", "fin-ws-0?")


def test_empty_selection_never_matches_any_condition():
    rule = make_rule({}, "any")
    assert engine.matches({"a": 1}, rule) is False


def test_condition_all_requires_every_field():
    rule = make_rule({"host": "fin-ws-07", "user.name": "a.ivanov"})
    assert engine.matches({"host": "fin-ws-07", "user.name": "a.ivanov"}, rule)
    assert not engine.matches({"host": "fin-ws-07", "user.name": "s.petrova"}, rule)


def test_condition_any_accepts_single_hit():
    rule = make_rule({"host": "fin-ws-07", "user.name": "nobody"}, "any")
    assert engine.matches({"host": "fin-ws-07", "user.name": "a.ivanov"}, rule)


def test_hits_returns_only_matching_events():
    rule = make_rule({"event.type": "network"})
    stream = ({"id": 1, "event.type": "network"}, {"id": 2, "event.type": "process"})
    assert [event["id"] for event in engine.hits(rule, stream)] == [1]


def test_evaluate_packages_rule_and_hits():
    rule = make_rule({"event.type": "network"})
    verdict = engine.evaluate((rule,), ({"id": 1, "event.type": "network"},))[0]
    assert verdict["rule"].id == rule.id
    assert len(verdict["hits"]) == 1


def test_parse_sets_defaults():
    rule = rules.parse("id: D1\ntitle: Проба\nselection:\n  a: b\n")
    assert rule.condition == "all"
    assert rule.severity == "medium"


def test_parse_rejects_rule_without_title():
    with pytest.raises(ValueError):
        rules.parse("id: D2\nselection:\n  a: b\n")


def test_as_dict_round_trip_keeps_selection():
    rule = rules.parse("id: D3\ntitle: Проба\nselection:\n  host: fin-ws-07\n")
    assert rules.as_dict(rule)["selection"] == {"host": "fin-ws-07"}


def test_events_have_ids_and_types():
    stream = events.load()
    assert all("id" in event for event in stream)
    assert {"process", "network", "auth_failure"} & {event["event.type"] for event in stream}


def test_by_id_returns_event_or_empty():
    assert events.by_id("evt-0001")["host"] == "fin-ws-07"
    assert events.by_id("нет-такого") == {}


def test_rules_endpoint_lists_sources(client):
    payload = client.get("/api/rules").json()
    assert payload["sources"]
    assert all(name.endswith(".yaml") for name in payload["sources"])


def test_evaluate_unknown_rule_returns_empty_findings(client):
    payload = client.post("/api/evaluate", json={"rule_ids": ["нет"]}).json()
    assert payload["findings"] == []
    assert payload["total"] == 0


def test_replay_is_idempotent(client):
    first = client.post("/api/replay", json={"rule_ids": []}).json()
    second = client.post("/api/replay", json={"rule_ids": []}).json()
    assert first["saved"] == second["saved"]


def test_detections_are_ordered_by_time(client):
    client.post("/api/replay", json={"rule_ids": []})
    items = client.get("/api/detections").json()["items"]
    times = [item["occurred_at"] for item in items]
    assert times == sorted(times, reverse=True)


def test_events_endpoint_reports_count(client):
    payload = client.get("/api/events").json()
    assert payload["count"] == len(events.load())
    assert payload["items"]


def test_custom_rule_appears_in_evaluate(client):
    text = "id: F6-7777\ntitle: Кастом\nselection:\n  event.type: network\n"
    client.post("/api/rules", json={"text": text})
    payload = client.post("/api/evaluate", json={"rule_ids": ["F6-7777"]}).json()
    assert [item["id"] for item in payload["findings"]] == ["F6-7777"]

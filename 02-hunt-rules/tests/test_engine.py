from app import engine, matchers, rules


def make_rule(selection, condition="all"):
    return rules.build({"id": "T-1", "title": "тест", "condition": condition, "selection": selection}, "test")


def test_nested_field_lookup():
    assert matchers.dig({"process": {"name": "cmd.exe"}}, "process.name") == "cmd.exe"


def test_missing_field_is_empty():
    assert matchers.dig({"a": 1}, "process.name") == ""


def test_exact_match_is_case_insensitive():
    assert matchers.match_field({"process": {"name": "CMD.exe"}}, "process.name", "cmd.exe")


def test_glob_match():
    assert matchers.match_field({"ip": "203.0.113.44"}, "ip", "203.0.113.*")
    assert not matchers.match_field({"ip": "198.51.100.44"}, "ip", "203.0.113.*")


def test_regex_match():
    assert matchers.match_field({"cl": "IEX (New-Object Net.WebClient)"}, "cl", "re:(?i)iex")
    assert not matchers.match_field({"cl": "Get-ChildItem"}, "cl", "re:(?i)iex")


def test_list_is_any_of():
    assert matchers.match_field({"user": "admin"}, "user", ["root", "admin"])
    assert not matchers.match_field({"user": "backup"}, "user", ["root", "admin"])


def test_condition_all_requires_every_field():
    rule = make_rule({"event.type": "auth_failure", "user.name": "root"})
    assert engine.matches({"event.type": "auth_failure", "user.name": "root"}, rule)
    assert not engine.matches({"event.type": "auth_failure", "user.name": "admin"}, rule)


def test_condition_any_requires_one_field():
    rule = make_rule({"process.name": "schtasks.exe", "process.parent.name": "services.exe"}, "any")
    assert engine.matches({"process": {"name": "svchost.exe", "parent": {"name": "services.exe"}}}, rule)
    assert not engine.matches({"process": {"name": "svchost.exe", "parent": {"name": "explorer.exe"}}}, rule)


def test_rule_without_selection_is_rejected():
    try:
        rules.build({"id": "X"}, "")
    except ValueError as error:
        assert "selection" in str(error)


def test_rule_round_trip():
    rule = rules.parse("id: A1\ntitle: Пример\nseverity: HIGH\nselection:\n  a: b\n")
    assert rule.severity == "high"
    assert rules.as_dict(rule)["selection"] == {"a": "b"}

"""Дополнительные проверки нормализации журналов и поиска по индексу."""
from app import index, parsers, service


def test_syslog_without_pid_is_kept_as_raw():
    doc = parsers.parse("syslog", "Oct  2 09:31:17 host sshd: Failed password")[0]
    assert doc["event.dataset"] == "raw"


def test_syslog_invalid_user_counts_as_failure():
    line = "Oct  2 09:34:10 gw sshd[2216]: Invalid user oracle from 203.0.113.24 port 51311"
    doc = parsers.parse("syslog", line)[0]
    assert doc["event.outcome"] == "failure"
    assert doc["user.name"] == "oracle"


def test_syslog_success_and_pid():
    line = "Oct  2 11:20:33 gw sshd[3050]: Accepted password for d.orlov from 198.51.100.31 port 40222 ssh2"
    doc = parsers.parse("syslog", line)[0]
    assert doc["process.pid"] == 3050
    assert doc["event.outcome"] == "success"


def test_syslog_timestamp_has_year():
    line = "Dec 31 23:59:59 gw sshd[1]: Accepted password for a from 192.0.2.1 port 1 ssh2"
    assert parsers.parse("syslog", line)[0]["@timestamp"].startswith("2026-12-31T23:59:59")


def test_nginx_404_and_agent():
    line = '192.0.2.201 - - [02/Oct/2026:13:19:03 +0300] "GET /admin HTTP/1.1" 404 240 "-" "curl/8.4.0"'
    doc = parsers.parse("nginx", line)[0]
    assert doc["http.response.status_code"] == 404
    assert doc["user_agent.original"] == "curl/8.4.0"


def test_nginx_method_and_path():
    line = '198.51.100.77 - - [02/Oct/2026:10:02:31 +0300] "POST /login HTTP/1.1" 401 620 "-" "Mozilla/5.0"'
    doc = parsers.parse("nginx", line)[0]
    assert doc["http.request.method"] == "POST"
    assert doc["url.path"] == "/login"


def test_windows_row_keeps_event_code_as_string():
    content = "timestamp,host,user,event_id,process,message\n2026-10-02T09:14:01Z,ws,a,4688,cmd.exe,Запуск\n"
    doc = parsers.parse("windows", content)[0]
    assert doc["event.code"] == "4688"
    assert doc["message"] == "Запуск"


def test_tokenize_drops_short_noise():
    tokens = index.tokenize("a bb 203.0.113.24")
    assert "a" not in tokens
    assert "203.0.113.24" in tokens


def test_search_requires_all_terms():
    built = index.build(({"message": "failed password root"}, {"message": "failed login"}))
    assert len(index.search(built, "failed root")) == 1


def test_search_is_case_insensitive():
    built = index.build(({"message": "Failed Password"},))
    assert len(index.search(built, "failed password")) == 1


def test_search_without_terms_returns_documents():
    built = index.build(({"message": "a b"}, {"message": "c d"}))
    assert len(index.search(built, "")) == 2


def test_idf_prefers_rare_terms():
    built = index.build(({"m": "alpha"}, {"m": "alpha beta"}, {"m": "beta gamma"}))
    rare = index.search(built, "gamma")[0]
    assert rare["m"] == "beta gamma"


def test_statistics_counts_categories():
    stats = index.statistics(index.build(({"event.category": "web"}, {"event.category": "web"}, {"event.category": "auth"})))
    assert stats["categories"] == {"web": 2, "auth": 1}


def test_count_by_ignores_empty_values():
    assert index.count_by(({"host": "a"}, {"host": ""}, {}), "host") == {"a": 1}


def test_format_of_uses_stem():
    from pathlib import Path

    assert service.format_of(Path("data/access.log")) == "nginx"
    assert service.format_of(Path("data/auth.log")) == "syslog"
    assert service.format_of(Path("data/unknown.log")) == "syslog"


def test_search_endpoint_returns_query_echo(client):
    payload = client.get("/api/search", params={"query": "failed"}).json()
    assert payload["query"] == "failed"
    assert payload["count"] == len(payload["items"])


def test_ingest_exposes_document_count(client):
    before = client.get("/api/stats").json()["documents"]
    body = {"format": "syslog", "content": "Oct  2 16:00:00 gw sshd[1]: Failed password for root from 192.0.2.5 port 1 ssh2", "prefix": "extra"}
    payload = client.post("/api/ingest", json=body).json()
    assert payload["stored"] == 1
    assert payload["documents"] == before + 1


def test_logs_endpoint_limit(client):
    assert len(client.get("/api/logs", params={"limit": 2}).json()["items"]) <= 2

from app import index, parsers


def test_syslog_failure_is_normalized():
    line = "Oct  2 09:31:17 edge-gw-01 sshd[2211]: Failed password for root from 203.0.113.24 port 51122 ssh2"
    doc = parsers.parse("syslog", line)[0]
    assert doc["event.outcome"] == "failure"
    assert doc["user.name"] == "root"
    assert doc["source.ip"] == "203.0.113.24"
    assert doc["@timestamp"].startswith("2026-10-02T09:31:17")


def test_syslog_success_is_normalized():
    line = "Oct  2 11:20:33 edge-gw-01 sshd[3050]: Accepted password for d.orlov from 198.51.100.31 port 40222 ssh2"
    doc = parsers.parse("syslog", line)[0]
    assert doc["event.outcome"] == "success"
    assert doc["user.name"] == "d.orlov"


def test_nginx_line_is_normalized():
    line = '203.0.113.24 - - [02/Oct/2026:09:14:02 +0300] "GET /a.ps1 HTTP/1.1" 200 512 "-" "curl/8.4.0"'
    doc = parsers.parse("nginx", line)[0]
    assert doc["http.request.method"] == "GET"
    assert doc["http.response.status_code"] == 200
    assert doc["url.path"] == "/a.ps1"
    assert doc["@timestamp"].startswith("2026-10-02T09:14:02")


def test_unknown_line_is_kept_as_raw():
    doc = parsers.parse("syslog", "какая-то строка без формата")[0]
    assert doc["event.category"] == "unknown"


def test_windows_csv_is_normalized():
    content = "timestamp,host,user,event_id,process,message\n2026-10-02T09:14:01Z,ws-07,a.ivanov,4688,powershell.exe,Encoded command\n"
    doc = parsers.parse("windows", content)[0]
    assert doc["event.code"] == "4688"
    assert doc["process.name"] == "powershell.exe"


def test_index_finds_all_terms():
    docs = ({"message": "failed password for root"}, {"message": "accepted password for admin"}, {"message": "failed login"})
    built = index.build(docs)
    assert len(index.search(built, "failed password")) == 1
    assert len(index.search(built, "failed")) == 2


def test_wildcard_search():
    docs = ({"message": "203.0.113.24 beacon"}, {"message": "198.51.100.1 beacon"})
    built = index.build(docs)
    assert len(index.search(built, "203.*")) == 1


def test_scores_prefer_rare_terms():
    docs = ({"message": "failed login common"}, {"message": "failed login rare"})
    built = index.build(docs)
    results = index.search(built, "rare")
    assert results[0]["message"].endswith("rare")


def test_empty_query_returns_everything():
    docs = ({"message": "a"}, {"message": "b"})
    assert len(index.search(index.build(docs), "")) == 2

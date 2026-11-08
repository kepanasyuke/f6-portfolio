def test_health(client):
    payload = client.get("/api/health").json()
    assert payload["service"] == "data-portal"


def test_sources_mark_available_bases(client):
    sources = {item["key"]: item for item in client.get("/api/sources").json()["items"]}
    assert sources["iocs"]["available"] is True
    assert sources["iocs"]["tables"][0]["name"] == "iocs"
    assert sources["ops"]["available"] is False
    assert sources["ops"]["tables"] == []


def test_summary_counts_rows_and_kpis(client):
    payload = client.get("/api/summary").json()
    assert payload["kpis"]
    iocs = next(item for item in payload["sources"] if item["key"] == "iocs")
    assert iocs["tables"][0]["rows"] == 3


def test_kpi_uses_sql_condition(client):
    kpis = {item["title"]: item["value"] for item in client.get("/api/summary").json()["kpis"]}
    assert kpis["Индикаторы"] == 3
    assert kpis["Домены под риском"] == 1
    assert kpis["Журналы"] == 0


def test_rows_page_has_columns_and_meta(client):
    payload = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "limit": 2}).json()
    assert payload["total"] == 3
    assert len(payload["rows"]) == 2
    assert [column["name"] for column in payload["columns"]][:3] == ["id", "value", "kind"]
    assert payload["columns"][0]["pk"] is True


def test_pagination_shifts_rows(client):
    first = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "limit": 2, "offset": 0}).json()
    second = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "limit": 2, "offset": 2}).json()
    assert first["rows"][0]["id"] != second["rows"][0]["id"]
    assert len(second["rows"]) == 1


def test_search_filters_by_any_column(client):
    payload = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "q": "example"}).json()
    assert payload["total"] == 2
    assert all("example" in row["value"] for row in payload["rows"])


def test_search_without_matches_returns_empty(client):
    payload = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "q": "нет-такого"}).json()
    assert payload["total"] == 0
    assert payload["rows"] == []


def test_sorting_by_column_and_direction(client):
    payload = client.get(
        "/api/rows",
        params={"source": "iocs", "table": "iocs", "sort": "confidence", "direction": "desc"},
    ).json()
    confidences = [row["confidence"] for row in payload["rows"]]
    assert confidences == sorted(confidences, reverse=True)


def test_unknown_column_falls_back_to_first(client):
    payload = client.get(
        "/api/rows",
        params={"source": "iocs", "table": "iocs", "sort": "no-such-column", "direction": "asc"},
    ).json()
    assert [row["id"] for row in payload["rows"]] == sorted(row["id"] for row in payload["rows"])


def test_limit_above_maximum_is_rejected(client):
    response = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "limit": 5000})
    assert response.status_code == 422


def test_limit_within_bounds_is_applied(client):
    payload = client.get("/api/rows", params={"source": "iocs", "table": "iocs", "limit": 1}).json()
    assert payload["limit"] == 1
    assert len(payload["rows"]) == 1


def test_unknown_source_returns_404(client):
    assert client.get("/api/rows", params={"source": "nope", "table": "iocs"}).status_code == 404


def test_system_table_is_not_exposed(client):
    response = client.get("/api/rows", params={"source": "iocs", "table": "sqlite_master"})
    assert response.status_code == 404


def test_csv_export_has_header_and_rows(client):
    response = client.get("/api/export.csv", params={"source": "iocs", "table": "iocs"})
    lines = response.text.strip().splitlines()
    assert response.status_code == 200
    assert lines[0] == "id;value;kind;severity;confidence"
    assert len(lines) == 4
    assert "203.0.113.24" in lines[1]

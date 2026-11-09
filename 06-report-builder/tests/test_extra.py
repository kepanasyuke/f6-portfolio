"""Дополнительные проверки конвертера Markdown и сборки отчётов."""
from app import markdown, reports

PAYLOAD = {
    "title": "Кампания",
    "template": "threat",
    "tlp": "TLP:RED",
    "summary": "Кратко",
    "iocs": [{"kind": "ip", "value": "203.0.113.24"}],
    "findings": [{"severity": "high", "title": "Находка", "detail": "Детали"}],
    "recommendations": ["Шаг один"],
}


def test_empty_markdown_returns_empty_html():
    assert markdown.to_html("") == ""


def test_paragraph_joins_lines():
    assert "<p>раз два</p>" in markdown.to_html("раз\nдва")


def test_h2_and_h3_are_rendered():
    html = markdown.to_html("## Уровень два\n\n### Уровень три")
    assert "<h2>Уровень два</h2>" in html
    assert "<h3>Уровень три</h3>" in html


def test_ordered_list_strips_numbers():
    html = markdown.to_html("1. первый\n2. второй")
    assert "<li>первый</li>" in html


def test_quote_merges_lines():
    assert "<blockquote>раз два</blockquote>" in markdown.to_html("> раз\n> два")


def test_inline_code_and_bold_together():
    html = markdown.to_html("**жирный** и `код`")
    assert "<strong>жирный</strong>" in html and "<code>код</code>" in html


def test_ampersand_is_escaped():
    assert "&amp;" in markdown.to_html("A & B")


def test_table_cells_are_escaped():
    html = markdown.to_html("| a | b |\n|---|---|\n| <x> | y |")
    assert "&lt;x&gt;" in html


def test_kind_of_detects_structures():
    assert markdown.kind_of("- пункт") == "bullet"
    assert markdown.kind_of("# Заголовок") == "h1"
    assert markdown.kind_of("") == "blank"
    assert markdown.kind_of("просто текст") == "paragraph"


def test_header_uses_title_and_tlp():
    text = reports.build(PAYLOAD)
    assert text.startswith("# Кампания")
    assert "TLP:RED" in text


def test_header_falls_back_to_template_title():
    text = reports.build({"template": "incident"})
    assert reports.TEMPLATE_TITLES["incident"] in text


def test_footer_mentions_author():
    assert "подготовил: analyst" in reports.build(PAYLOAD)


def test_footer_uses_custom_author():
    assert "подготовил: d.orlov" in reports.build({**PAYLOAD, "author": "d.orlov"})


def test_ioc_table_contains_kind_and_value():
    text = reports.build(PAYLOAD)
    assert "| ip | 203.0.113.24 |" in text


def test_findings_table_contains_severity():
    assert "| high | Находка | Детали |" in reports.build(PAYLOAD)


def test_recommendations_are_bulleted():
    assert "- Шаг один" in reports.build(PAYLOAD)


def test_missing_recommendations_skip_section():
    assert "## Рекомендации" not in reports.build({"title": "Без советов", "template": "actor"})


def test_severity_counts_are_lowercased():
    counts = reports.severity_counts(({"severity": "HIGH"}, {"severity": "high"}, {"severity": "low"}))
    assert counts == {"high": 2, "low": 1}


def test_templates_endpoint_has_three_items(client):
    items = client.get("/api/templates").json()["items"]
    assert len(items) == 3
    assert all(item["title"] for item in items)


def test_preview_returns_severity_summary(client):
    payload = client.post("/api/preview", json={"findings": [{"severity": "critical", "title": "Т"}]}).json()
    assert payload["severity"] == {"critical": 1}


def test_create_uses_default_tlp(client):
    created = client.post("/api/reports", json={"title": "Без TLP"}).json()
    assert created["tlp"] == "TLP:AMBER"


def test_history_is_newest_first(client):
    first = client.post("/api/reports", json={"title": "Первый"}).json()["id"]
    second = client.post("/api/reports", json={"title": "Второй"}).json()["id"]
    items = client.get("/api/reports").json()["items"]
    assert items[0]["id"] == second > first


def test_markdown_export_has_extension_header(client):
    report_id = client.post("/api/reports", json={"title": "Выгрузка"}).json()["id"]
    response = client.get(f"/api/reports/{report_id}/markdown")
    assert response.headers["content-type"].startswith("text/plain")
    assert "# Выгрузка" in response.text


def test_metrics_by_template_groups_counts(client):
    client.post("/api/reports", json={"title": "A", "template": "actor"})
    client.post("/api/reports", json={"title": "B", "template": "actor"})
    payload = client.get("/api/metrics").json()
    assert payload["by_template"]["actor"] == 2

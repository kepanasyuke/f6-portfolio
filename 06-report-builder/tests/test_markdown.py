from app import markdown, reports


def test_headings_and_paragraphs():
    html = markdown.to_html("# Заголовок\n\nОбычный текст")
    assert "<h1>Заголовок</h1>" in html
    assert "<p>Обычный текст</p>" in html


def test_bold_code_and_links():
    html = markdown.to_html("Текст **жирный** и `код` и [ссылка](https://example.com)")
    assert "<strong>жирный</strong>" in html
    assert "<code>код</code>" in html
    assert 'href="https://example.com"' in html


def test_bullet_list():
    html = markdown.to_html("- первый\n- второй")
    assert html.count("<li>") == 2
    assert "<ul>" in html


def test_ordered_list():
    html = markdown.to_html("1. один\n2. два")
    assert "<ol>" in html
    assert html.count("<li>") == 2


def test_blockquote():
    assert "<blockquote>" in markdown.to_html("> цитата")


def test_table_skips_separator_row():
    html = markdown.to_html("| Тип | Значение |\n|---|---|\n| ip | 203.0.113.24 |")
    assert html.count("<tr>") == 2
    assert "<th>Тип</th>" in html
    assert "<td>203.0.113.24</td>" in html


def test_escape_prevents_html_injection():
    html = markdown.to_html("Опасно <script>alert(1)</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_rule_line():
    assert "<hr />" in markdown.to_html("---")


def test_report_contains_required_sections():
    text = reports.build(
        {
            "title": "Тестовый отчёт",
            "template": "threat",
            "tlp": "TLP:RED",
            "summary": "Кратко о главном",
            "iocs": [{"kind": "domain", "value": "example.com"}],
            "findings": [{"severity": "high", "title": "Находка", "detail": "Детали"}],
            "recommendations": ["Сделать раз", "Сделать два"],
        }
    )
    assert text.startswith("# Тестовый отчёт")
    assert "TLP:RED" in text
    assert "## Резюме" in text
    assert "## Индикаторы компрометации" in text
    assert "## Наблюдения" in text
    assert "## Рекомендации" in text
    assert "- Сделать раз" in text


def test_report_skips_empty_sections():
    text = reports.build({"title": "Пусто", "template": "incident"})
    assert "## Резюме" not in text
    assert "## Наблюдения" not in text


def test_severity_counts():
    counts = reports.severity_counts(({"severity": "high"}, {"severity": "HIGH"}, {"severity": "low"}))
    assert counts == {"high": 2, "low": 1}

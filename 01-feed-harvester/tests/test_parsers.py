from app import parsers


def test_refang_restores_dots_and_scheme():
    assert parsers.refang("hxxps://evil[.]example[.]com/a") == "https://evil.example.com/a"


def test_detect_kind_covers_main_types():
    assert parsers.detect_kind("203.0.113.5") == "ipv4"
    assert parsers.detect_kind("https://example.com/x") == "url"
    assert parsers.detect_kind("a" * 64) == "sha256"
    assert parsers.detect_kind("mail.example.com") == "domain"


def test_detect_kind_rejects_garbage():
    assert parsers.detect_kind("не индикатор") == ""


def test_csv_feed_normalizes_fields():
    records, rejected = parsers.parse("csv", "value,severity,source,confidence\n203.0.113.9,high,test,77\n")
    assert rejected == 0
    assert records[0]["kind"] == "ipv4"
    assert records[0]["confidence"] == 77
    assert records[0]["severity"] == "high"


def test_json_feed_accepts_aliases():
    content = '{"data": [{"indicator": "198[.]51[.]100[.]2", "risk": "critical", "score": "88"}]}'
    records, rejected = parsers.parse("json", content)
    assert rejected == 0
    assert records[0]["value"] == "198.51.100.2"
    assert records[0]["severity"] == "critical"


def test_text_feed_skips_comments_and_garbage():
    content = "# header\n\n203.0.113.1|high|hunt|80|2026-10-01|test\nне-индикатор|low\n"
    records, rejected = parsers.parse("txt", content)
    assert len(records) == 1
    assert rejected == 1


def test_confidence_is_clamped():
    assert parsers.confidence_of("150") == 100
    assert parsers.confidence_of("-5") == 0
    assert parsers.confidence_of("") == 0


def test_unknown_format_falls_back_to_text():
    records, rejected = parsers.parse("xml", "203.0.113.3|low|manual|50\n")
    assert len(records) == 1
    assert rejected == 0

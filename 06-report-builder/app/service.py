"""Сценарии: генерация, сохранение, выгрузка отчётов."""
import json

from app import config, markdown, reports, store


def preview(payload: dict) -> dict:
    return present(payload, reports.build(payload))


def create(payload: dict, persist: bool) -> dict:
    return save(payload, reports.build(payload)) if persist else present(payload, reports.build(payload))


def present(payload: dict, text: str) -> dict:
    return {
        "title": title_of(payload),
        "template": payload.get("template", "threat"),
        "tlp": payload.get("tlp", config.TLP[2]),
        "markdown": text,
        "html": markdown.to_html(text),
        "severity": reports.severity_counts(tuple(payload.get("findings", []))),
    }


def title_of(payload: dict) -> str:
    return str(payload.get("title") or default_title(payload))


def default_title(payload: dict) -> str:
    return reports.TEMPLATE_TITLES.get(payload.get("template", "threat"), "Отчёт")


def save(payload: dict, text: str) -> dict:
    report_id = store.save(row(payload, text))
    return {"id": report_id, **present(payload, text)}


def row(payload: dict, text: str) -> tuple:
    return (
        title_of(payload),
        payload.get("template", "threat"),
        payload.get("tlp", config.TLP[2]),
        text,
        json.dumps(payload, ensure_ascii=False),
    )


def history(limit: int) -> tuple[dict, ...]:
    return store.many(limit)


def report(report_id: int) -> dict:
    found = store.one(report_id)
    return {**found, "html": markdown.to_html(found["markdown"])} if found else {}


def markdown_of(report_id: int) -> str:
    return store.one(report_id).get("markdown", "")


def templates() -> tuple[dict, ...]:
    return tuple(
        {"id": name, "title": title, "hint": reports.TEMPLATE_HINTS.get(name, ""), "tlp": config.TLP}
        for name, title in reports.TEMPLATE_TITLES.items()
    )


def metrics() -> dict:
    return {"reports": store.total(), "by_template": store.by_template(), "tlp": config.TLP}


def sample() -> dict:
    return {
        "title": "Кампания «Gatekeeper»: фишинг через поддельные панели",
        "template": "threat",
        "tlp": "TLP:AMBER",
        "summary": (
            "С сентября 2026 года наблюдается рост числа доменов, имитирующих порталы входа. "
            "Инфраструктура использует общий TLS-сертификат и один C2-узел."
        ),
        "iocs": [
            {"kind": "domain", "value": "cdn-login.example.com"},
            {"kind": "ip", "value": "203.0.113.24"},
            {"kind": "sha256", "value": "f6b3a1c94d2e5077b19c8a4f0e2d6b85c3a7e91d4f2c08b6a5e3d7c1b9f04a26"},
        ],
        "findings": [
            {
                "severity": "critical",
                "title": "Общий сертификат на двух доменах",
                "detail": "cert SHA256:8f14…c02d используется и фишингом, и панелью.",
            },
            {
                "severity": "high",
                "title": "Beacon с рабочей станции",
                "detail": "fin-ws-07 обращался к cdn-login.example.com каждые 60 секунд.",
            },
        ],
        "recommendations": [
            "Заблокировать домены и IP на периметре и в DNS-фильтрации.",
            "Проверить fin-ws-07 на закрепление и собрать память процесса powershell.exe.",
            "Добавить хеши в блок-лист EDR и отслеживать повторные срабатывания.",
        ],
        "author": "analyst",
    }

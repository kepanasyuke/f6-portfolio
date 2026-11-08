"""Сборка Markdown-отчёта из структурированного описания."""
from datetime import date

from app import config

SEVERITY_ORDER = ("critical", "high", "medium", "low")
TEMPLATE_TITLES = {
    "threat": "Threat Intelligence: отчёт по угрозе",
    "incident": "Брифинг по инциденту",
    "actor": "Профиль злоумышленника",
}
TEMPLATE_HINTS = {
    "threat": "Кампания, инфраструктура, IOC, рекомендации",
    "incident": "Хронология, затронутые узлы, действия по реагированию",
    "actor": "Кто, зачем, чем атакует, как связан с другими группами",
}


def build(payload: dict) -> str:
    return "\n".join(part for part in parts(payload) if part)


def parts(payload: dict) -> tuple[str, ...]:
    return (
        header(payload),
        summary(payload),
        iocs(payload),
        findings(payload),
        recommendations(payload),
        footer(payload),
    )


def header(payload: dict) -> str:
    template = TEMPLATE_TITLES.get(payload.get("template", "threat"), "Отчёт")
    return f"# {payload.get('title') or template}\n\n> {template} · {tlp_of(payload)} · {today()}\n"


def tlp_of(payload: dict) -> str:
    return str(payload.get("tlp", config.TLP[2]))


def summary(payload: dict) -> str:
    text = str(payload.get("summary") or "").strip()
    return f"## Резюме\n\n{text}\n" if text else ""


def iocs(payload: dict) -> str:
    return indicators(payload) if payload.get("iocs") else ""


def indicators(payload: dict) -> str:
    return table_section("Индикаторы компрометации", ("Тип", "Значение"), ioc_rows(payload))


def ioc_rows(payload: dict) -> tuple[tuple[str, str], ...]:
    return tuple(ioc_row(item) for item in payload.get("iocs", []))


def ioc_row(item: dict) -> tuple[str, str]:
    return (str(item.get("kind", "ioc")), str(item.get("value", "")))


def findings(payload: dict) -> str:
    return observations(payload) if payload.get("findings") else ""


def observations(payload: dict) -> str:
    return table_section("Наблюдения", ("Критичность", "Наблюдение", "Детали"), finding_rows(payload))


def finding_rows(payload: dict) -> tuple[tuple[str, str, str], ...]:
    return tuple(row for row in (finding_row(item) for item in payload.get("findings", [])) if row)


def finding_row(item: dict) -> tuple[str, str, str]:
    return (
        str(item.get("severity", "medium")).lower(),
        str(item.get("title", "")),
        str(item.get("detail", "")),
    )


def recommendations(payload: dict) -> str:
    items = tuple(str(item) for item in payload.get("recommendations", []) if str(item).strip())
    return "## Рекомендации\n\n" + "\n".join(f"- {item}" for item in items) + "\n" if items else ""


def footer(payload: dict) -> str:
    return f"---\n\nИсточник: F6 Threat Intelligence · подготовил: {payload.get('author', 'analyst')}\n"


def table_section(title: str, columns: tuple[str, str, ...], rows: tuple[tuple, ...]) -> str:
    return f"## {title}\n\n{table(columns, rows)}\n"


def table(columns: tuple[str, ...], rows: tuple[tuple, ...]) -> str:
    return f"{head(columns)}\n{divider(columns)}\n{body(rows)}"


def head(columns: tuple[str, ...]) -> str:
    return "| " + " | ".join(columns) + " |"


def divider(columns: tuple[str, ...]) -> str:
    return "|" + "|".join("---" for _ in columns) + "|"


def body(rows: tuple[tuple, ...]) -> str:
    return "\n".join("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)


def today() -> str:
    return date.today().isoformat()


def severity_counts(findings_list: tuple[dict, ...]) -> dict[str, int]:
    known = {severity(item) for item in findings_list}
    return {name: count_severity(findings_list, name) for name in known}


def severity(item: dict) -> str:
    return str(item.get("severity", "medium")).lower()


def count_severity(findings_list: tuple[dict, ...], name: str) -> int:
    return sum(1 for item in findings_list if severity(item) == name)

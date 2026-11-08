"""Агрегация разделов консоли из API сервисов."""
import asyncio

from app import client, config


async def snapshots() -> dict:
    results = await asyncio.gather(*(fetch(item) for item in config.SERVICES), return_exceptions=True)
    return {item["key"]: clean(value) for item, value in zip(config.SERVICES, results, strict=False)}


async def fetch(service_item: dict) -> dict | None:
    return await client.get_json(config.summary_url(service_item))


def clean(value) -> dict | None:
    return value if isinstance(value, dict) else None


def online(payload: dict | None) -> bool:
    return payload is not None


def size(value) -> int:
    return len(value) if isinstance(value, (list, tuple, dict)) else 0


def number(value) -> int:
    return int(value) if isinstance(value, (int, float)) else 0


def pick(node, *path):
    head, tail = path[0], path[1:]
    return pick(child(node, head), *tail) if tail else child(node, head)


def child(node, key):
    return node.get(key) if isinstance(node, dict) else None


async def overview() -> dict:
    snapshot = await snapshots()
    return {"services": statuses(snapshot), "kpis": kpis(snapshot), "feed": feed(snapshot)}


def statuses(snapshot: dict) -> tuple[dict, ...]:
    return tuple(status(item, snapshot.get(item["key"])) for item in config.SERVICES)


def status(service_item: dict, payload: dict | None) -> dict:
    return {
        "key": service_item["key"],
        "title": service_item["title"],
        "port": service_item["port"],
        "online": online(payload),
    }


def kpis(snapshot: dict) -> tuple[dict, ...]:
    return tuple(measure(title, hint, value) for title, hint, value in measured(snapshot))


def measure(title: str, hint: str, value: int) -> dict:
    return {"title": title, "hint": hint, "value": value}


def measured(snapshot: dict) -> tuple[tuple[str, str, int], ...]:
    return (
        ("Индикаторы", "база IOC", number(pick(snapshot.get("iocs"), "total"))),
        ("Детекции", "срабатывания правил", size(pick(snapshot.get("hunt"), "items"))),
        ("Журналы", "события в индексе", number(pick(snapshot.get("logs"), "documents"))),
        ("Узлы графа", "инфраструктура", number(pick(snapshot.get("graph"), "nodes"))),
        ("Домены под риском", "critical у радара", critical_domains(snapshot)),
        ("Отчёты", "для портала TI", number(pick(snapshot.get("reports"), "reports"))),
        ("Проблемы хостов", "warn и critical", problem_hosts(snapshot)),
    )


def critical_domains(snapshot: dict) -> int:
    return number(pick(snapshot.get("radar"), "verdicts", "critical"))


def problem_hosts(snapshot: dict) -> int:
    return number(pick(snapshot.get("ops"), "stats", "by_status", "critical"))


def feed(snapshot: dict) -> tuple[dict, ...]:
    return tuple(item for item in live_feed(snapshot) if item)


def live_feed(snapshot: dict) -> tuple[dict, ...]:
    return (
        latest_detection(pick(snapshot.get("hunt"), "items")),
        latest_report(snapshot.get("reports")),
        worst_host(snapshot.get("ops")),
    )


def latest_detection(items) -> dict | None:
    return feed_item("detection", detection_text, items)


def latest_report(metrics) -> dict | None:
    return feed_item("report", report_text, metrics)


def feed_item(kind: str, text_of, source) -> dict | None:
    return {"kind": kind, "text": text_of(source)} if source else None


def detection_text(items) -> str:
    return f"Детекция {items[0]['rule_id']} на {items[0]['host']}"


def report_text(metrics) -> str:
    return f"Отчётов в портале: {number(pick(metrics, 'reports'))}"


def worst_host(overview_payload) -> dict | None:
    problems = pick(overview_payload, "stats", "problems")
    return {"kind": "host", "text": f"Проблемный хост: {problems[0]}"} if problems else None

async def indicators(needle: str, kind: str, severity: str) -> dict:
    return await ask("iocs", "/api/iocs", {"q": needle, "kind": kind, "severity": severity, "limit": 100})


async def hunting() -> dict:
    return {
        "rules": await ask("hunt", "/api/rules", {}),
        "detections": await ask("hunt", "/api/detections", {}),
    }


async def run_hunting() -> dict:
    return await post("hunt", "/api/evaluate", {"rule_ids": []})


async def logs(needle: str) -> dict:
    return await post("logs", "/api/search", {"query": needle, "limit": 30})


async def graph(node: str, depth: int) -> dict:
    return await graph_request(node, depth)


async def graph_request(node: str, depth: int) -> dict:
    return await pivot(node, depth) if node else await full_graph()


async def pivot(node: str, depth: int) -> dict:
    return await ask("graph", "/api/pivot", {"node": node, "depth": depth})


async def full_graph() -> dict:
    return await ask("graph", "/api/graph", {})


async def domains(brand: str) -> dict:
    return await post("radar", "/api/scan", {"brand": brand, "limit": 20})


async def reports() -> dict:
    return await ask("reports", "/api/reports", {"limit": 20})


async def create_report(payload: dict) -> dict:
    return await post("reports", "/api/reports", payload)


async def hosts() -> dict:
    return await ask("ops", "/api/overview", {})


async def check_host(name: str) -> dict:
    return await post("ops", f"/api/hosts/{name}/check", {})


async def ask(key: str, path: str, params: dict) -> dict:
    return await client.get_json(config.endpoint(key, path), params) or {}


async def post(key: str, path: str, body: dict) -> dict:
    return await client.post_json(config.endpoint(key, path), body) or {}

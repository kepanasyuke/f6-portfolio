"""Проверки состояния серверов: метрики и статусы.

Значения в стенде синтетические и детерминированные (md5 от имени хоста и
метрики), в продакшне вместо них встают вызовы node_exporter/WMI/SSH.
"""
import hashlib

METRICS = (
    {
        "name": "disk_pct",
        "title": "Диск",
        "unit": "%",
        "direction": "max",
        "warn": 80,
        "critical": 92,
        "low": 35,
        "high": 97,
    },
    {
        "name": "memory_pct",
        "title": "Память",
        "unit": "%",
        "direction": "max",
        "warn": 85,
        "critical": 95,
        "low": 22,
        "high": 97,
    },
    {
        "name": "load_1m",
        "title": "LA 1m",
        "unit": "",
        "direction": "max",
        "warn": 6,
        "critical": 10,
        "low": 1,
        "high": 14,
    },
    {
        "name": "patches_behind",
        "title": "Пропущено патчей",
        "unit": "шт",
        "direction": "max",
        "warn": 5,
        "critical": 12,
        "low": 0,
        "high": 18,
    },
    {
        "name": "cert_days_left",
        "title": "Сертификат, дней",
        "unit": "дн",
        "direction": "min",
        "warn": 21,
        "critical": 7,
        "low": 3,
        "high": 120,
    },
    {
        "name": "failed_logins_24h",
        "title": "Неудачных входов",
        "unit": "",
        "direction": "max",
        "warn": 10,
        "critical": 40,
        "low": 0,
        "high": 60,
    },
)


def values(host: dict) -> tuple[dict, ...]:
    return tuple(measure(host, metric) for metric in METRICS)


def measure(host: dict, metric: dict) -> dict:
    value = synthetic(host["name"], metric)
    return {
        "metric": metric["name"],
        "title": metric["title"],
        "value": value,
        "unit": metric["unit"],
        "status": status(value, metric),
    }


def synthetic(name: str, metric: dict) -> int:
    return spread(seed(name, metric["name"]), metric)


def seed(name: str, metric: str) -> int:
    return int(hashlib.md5(f"{name}:{metric}".encode()).hexdigest()[:6], 16)


def spread(seed_value: int, metric: dict) -> int:
    return metric["low"] + seed_value % (metric["high"] - metric["low"] + 1)


def status(value: int, metric: dict) -> str:
    return level(worsens(value, metric, "critical"), worsens(value, metric, "warn"))


def level(critical: bool, warn: bool) -> str:
    return "critical" if critical else "warn" if warn else "ok"


def worsens(value: int, metric: dict, level_name: str) -> bool:
    limit = metric[level_name]
    return value > limit if metric["direction"] == "max" else value < limit


def host_status(measured: tuple[dict, ...]) -> str:
    flags = {check["status"] for check in measured}
    return "critical" if "critical" in flags else "warn" if "warn" in flags else "ok"


def worst(measured: tuple[dict, ...]) -> tuple[dict, ...]:
    return tuple(check for check in measured if check["status"] != "ok")

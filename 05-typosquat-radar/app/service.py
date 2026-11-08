"""Сценарии: сканирование бренда, проверка домена, список наблюдения."""
from itertools import chain

from app import config, scoring, store, variants


def assess(brand: str, variant: str) -> dict:
    return record(variant, scoring.distance(brand, variant), scoring.signals(variant))


def record(variant: str, gap: int, flags: dict) -> dict:
    score = scoring.risk_of(gap, variant, flags)
    return {
        "domain": variant,
        "distance": gap,
        "risk": score,
        "verdict": scoring.verdict(score),
        "signals": flags,
    }


def generate(brand: str) -> tuple[str, ...]:
    return tuple(sorted(candidates(brand) - {brand}))


def candidates(brand: str) -> set[str]:
    return set(chain.from_iterable(generator(brand) for generator in variants.GENERATORS))


def scan(brand: str, limit: int) -> dict:
    return ranking(brand, tuple(assess(brand, variant) for variant in generate(brand)), limit)


def ranking(brand: str, items: tuple[dict, ...], limit: int) -> dict:
    return persist(brand, items, sort_items(items)[:limit])


def persist(brand: str, items: tuple[dict, ...], ordered: tuple[dict, ...]) -> dict:
    store.save_scans(brand, ordered)
    return {"brand": brand, "generated": len(items), "items": ordered}


def sort_items(items: tuple[dict, ...]) -> tuple[dict, ...]:
    return tuple(sorted(items, key=lambda item: (item["risk"], -item["distance"]), reverse=True))


def check(brand: str, domain: str) -> dict:
    return assess(brand, domain.strip().lower())


def watch(domain: str, note: str) -> dict:
    store.watch(domain, note)
    return {"domain": domain, "note": note}


def watchlist() -> tuple[dict, ...]:
    return store.watchlist()


def recent(limit: int) -> tuple[dict, ...]:
    return store.scans(limit)


def statistics() -> dict:
    history = store.scans(500)
    return {
        "scanned": store.count(),
        "verdicts": count_verdicts(history),
        "top": history[:5],
        "brand": config.BRAND,
        "techniques": tuple(generator.__name__ for generator in variants.GENERATORS),
    }


def count_verdicts(items: tuple[dict, ...]) -> dict[str, int]:
    names = {item["verdict"] for item in items}
    return {name: sum(1 for item in items if item["verdict"] == name) for name in names}

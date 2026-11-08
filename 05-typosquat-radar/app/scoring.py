"""Расстояние Левенштейна и оценка риска варианта домена."""
import hashlib

from app import config

HTTP_CODES = (200, 301, 403, 404, 200, 302)


def distance(a: str, b: str) -> int:
    return lev(a, b, len(a), len(b), {})


def lev(a: str, b: str, i: int, j: int, memo: dict) -> int:
    return memo[(i, j)] if (i, j) in memo else remember((i, j), lev_step(a, b, i, j, memo), memo)


def remember(key: tuple[int, int], value: int, memo: dict) -> int:
    memo[key] = value
    return value


def lev_step(a: str, b: str, i: int, j: int, memo: dict) -> int:
    return max(i, j) if not i or not j else lev_body(a, b, i, j, memo)


def lev_body(a: str, b: str, i: int, j: int, memo: dict) -> int:
    return lev(a, b, i - 1, j - 1, memo) if a[i - 1] == b[j - 1] else lev_gap(a, b, i, j, memo)


def lev_gap(a: str, b: str, i: int, j: int, memo: dict) -> int:
    return 1 + min(lev(a, b, i - 1, j, memo), lev(a, b, i, j - 1, memo), lev(a, b, i - 1, j - 1, memo))


def signals(domain: str) -> dict:
    return synthetic(digest(domain))


def digest(domain: str) -> int:
    return int(hashlib.md5(domain.encode("utf-8")).hexdigest()[:8], 16)


def synthetic(seed: int) -> dict:
    return {
        "registered": seed % 3 != 0,
        "mx": seed % 5 != 1,
        "http_status": HTTP_CODES[seed % len(HTTP_CODES)],
        "created_days_ago": seed % 420,
    }


def verdict(score: int) -> str:
    return "critical" if score >= 75 else "high" if score >= 55 else "medium" if score >= 35 else "low"


def risk_of(gap: int, variant: str, flags: dict) -> int:
    return clamp(base(gap) + tld_bonus(variant) + flag_bonus(flags) + script_bonus(variant))


def base(gap: int) -> int:
    return max(6, 46 - gap * 11)


def tld_bonus(variant: str) -> int:
    return 14 if variant.rsplit(".", 1)[-1] in config.RISKY_TLDS else 0


def script_bonus(variant: str) -> int:
    return 18 if any(ord(letter) > 127 for letter in variant) else 0


def flag_bonus(flags: dict) -> int:
    return registered_bonus(flags) + mx_bonus(flags) + live_bonus(flags)


def registered_bonus(flags: dict) -> int:
    return 16 if flags.get("registered") else 0


def mx_bonus(flags: dict) -> int:
    return 12 if flags.get("mx") else 0


def live_bonus(flags: dict) -> int:
    return 14 if flags.get("http_status") in (200, 302) else 0


def clamp(score: int) -> int:
    return max(0, min(100, score))

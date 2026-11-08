"""Генераторы похожих доменов: пропуск, перестановка, замена, вставка, дефис, TLD."""
HOMOGLYPHS = {
    "a": "а",
    "e": "е",
    "o": "о",
    "p": "р",
    "c": "с",
    "x": "х",
    "y": "у",
    "i": "і",
    "s": "ѕ",
    "d": "ԁ",
}
CONFUSABLES = {
    "rn": "m",
    "vv": "w",
    "cl": "d",
    "s": "5",
    "e": "3",
    "o": "0",
    "i": "1",
    "a": "4",
    "g": "9",
}
TLDS = ("example", "co", "net", "org", "io", "top", "xyz", "click")


def split(domain: str) -> tuple[str, str]:
    name, _, tld = domain.partition(".")
    return name, tld


def omissions(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(name[:index] + name[index + 1 :], tld) for index in range(1, len(name) - 1))


def repetitions(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(double(name, index), tld) for index in range(1, len(name)))


def double(name: str, index: int) -> str:
    return name[:index] + name[index] * 2 + name[index + 1 :]


def transpositions(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(swap(name, index), tld) for index in range(1, len(name) - 1))


def swap(name: str, index: int) -> str:
    return name[:index] + name[index + 1] + name[index] + name[index + 2 :]


def homoglyphs(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(mutated, tld) for mutated in masked(name))


def masked(name: str) -> tuple[str, ...]:
    positions = tuple((index, letter) for index, letter in enumerate(name) if letter in HOMOGLYPHS)
    return tuple(replace(name, index, HOMOGLYPHS[letter]) for index, letter in positions)


def confusables(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(name.replace(pair, twin, 1), tld) for pair, twin in CONFUSABLES.items() if pair in name)


def hyphenations(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(name[:index] + "-" + name[index:], tld) for index in range(2, len(name) - 1))


def tld_swaps(domain: str) -> tuple[str, ...]:
    name, tld = split(domain)
    return tuple(join(name, other) for other in TLDS if other != tld)


def subdomains(domain: str) -> tuple[str, ...]:
    return tuple(f"{prefix}.{domain}" for prefix in ("login", "secure", "account", "verify"))


def replace(name: str, index: int, letter: str) -> str:
    return name[:index] + letter + name[index + 1 :]


def join(name: str, tld: str) -> str:
    return f"{name}.{tld}"


GENERATORS = (
    omissions,
    repetitions,
    transpositions,
    homoglyphs,
    confusables,
    hyphenations,
    tld_swaps,
    subdomains,
)

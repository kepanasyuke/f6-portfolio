"""Инвертированный индекс: эмуляция поиска в стиле OpenSearch без внешнего кластера."""
import fnmatch
import math
import re
from dataclasses import dataclass

TOKEN = re.compile(r"[a-zа-я0-9_.:@/-]{2,}")
QUERY_TOKEN = re.compile(r"[a-zа-я0-9_.:@/*-]+")
WILDCARD = "*"


@dataclass(frozen=True)
class Index:
    docs: tuple[dict, ...]
    postings: dict[str, tuple[int, ...]]
    tokens: tuple[frozenset[str], ...]


def build(docs: tuple[dict, ...]) -> Index:
    token_lists = tuple(tokenize(document_text(doc)) for doc in docs)
    return Index(docs=docs, postings=postings(token_lists), tokens=token_lists)


def document_text(doc: dict) -> str:
    return " ".join(str(value) for value in doc.values())


def postings(token_lists: tuple[frozenset[str], ...]) -> dict[str, tuple[int, ...]]:
    names = vocabulary(token_lists)
    return {token: positions_for(token, token_lists) for token in names}


def positions_for(token: str, token_lists: tuple[frozenset[str], ...]) -> tuple[int, ...]:
    return tuple(index for index, items in enumerate(token_lists) if token in items)


def vocabulary(token_lists: tuple[frozenset[str], ...]) -> set[str]:
    return {token for items in token_lists for token in items}


def tokenize(text: str) -> frozenset[str]:
    return frozenset(TOKEN.findall(text.lower()))


def search(index: Index, query: str, limit: int = 50) -> tuple[dict, ...]:
    return rank(index, query)[:limit]


def rank(index: Index, query: str) -> tuple[dict, ...]:
    return tuple(sorted(scored(index, expand_all(index, query)), key=score_key, reverse=True))


def expand_all(index: Index, query: str) -> tuple[frozenset[str], ...]:
    return tuple(expand(index, term) for term in QUERY_TOKEN.findall(query.lower()))


def expand(index: Index, term: str) -> frozenset[str]:
    return by_mask(index, term) if WILDCARD in term else frozenset({term})


def by_mask(index: Index, term: str) -> frozenset[str]:
    return frozenset(token for token in index.postings if fnmatch.fnmatchcase(token, term))


def scored(index: Index, terms: tuple[frozenset[str], ...]) -> tuple[dict, ...]:
    positions = tuple(position for position, tokens in enumerate(index.tokens) if matches(tokens, terms))
    return tuple(document(index, position, terms) for position in positions)


def matches(tokens: frozenset[str], terms: tuple[frozenset[str], ...]) -> bool:
    return all(tokens & term for term in terms)


def document(index: Index, position: int, terms: tuple[frozenset[str], ...]) -> dict:
    return {**index.docs[position], "_score": relevance(index, terms)}


def relevance(index: Index, terms: tuple[frozenset[str], ...]) -> float:
    return round(sum(weight(index, term) for term in terms), 3)


def weight(index: Index, term: frozenset[str]) -> float:
    frequency = sum(len(index.postings.get(token, ())) for token in term)
    return math.log(len(index.docs) / max(frequency, 1)) + 1


def score_key(doc: dict) -> tuple[float, str]:
    return (doc["_score"], doc.get("@timestamp", ""))


def statistics(index: Index) -> dict:
    return {
        "documents": len(index.docs),
        "terms": len(index.postings),
        "categories": count_by(index.docs, "event.category"),
        "hosts": count_by(index.docs, "host"),
    }


def count_by(docs: tuple[dict, ...], field: str) -> dict[str, int]:
    values = tuple(str(doc.get(field, "")) for doc in docs if doc.get(field))
    return {value: values.count(value) for value in set(values)}

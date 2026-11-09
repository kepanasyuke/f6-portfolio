"""Дополнительные проверки обхода графа и API карты инфраструктуры."""
import pytest
from app import graph, service, store

SMALL = {
    "nodes": [
        {"id": "a", "kind": "ip", "value": "203.0.113.1", "risk": 80},
        {"id": "b", "kind": "domain", "value": "b.example.com", "risk": 60},
        {"id": "c", "kind": "hash", "value": "d41d8cd98f00b204e9800998ecf8427e", "risk": 40},
        {"id": "d", "kind": "email", "value": "x@example.com", "risk": 20},
    ],
    "edges": [
        {"src": "a", "dst": "b", "relation": "resolves_to", "confidence": 90},
        {"src": "b", "dst": "c", "relation": "drops", "confidence": 70},
        {"src": "c", "dst": "d", "relation": "registered_by", "confidence": 50},
    ],
}


@pytest.fixture()
def seeded(tmp_path, monkeypatch):
    monkeypatch.setenv("F6_DB", str(tmp_path / "small.sqlite3"))
    store.load(SMALL)
    return tmp_path


def test_distances_respect_depth(seeded):
    assert graph.distances("a", 1) == {"a": 0, "b": 1}
    assert graph.distances("a", 3) == {"a": 0, "b": 1, "c": 2, "d": 3}


def test_distances_are_undirected(seeded):
    assert graph.distances("d", 1) == {"d": 0, "c": 1}


def test_unknown_node_has_no_neighbours(seeded):
    assert graph.distances("нет-такого", 2) == {"нет-такого": 0}


def test_nodes_by_ids_returns_matching_only(seeded):
    assert {node["id"] for node in graph.nodes_by_ids(("a", "c"))} == {"a", "c"}


def test_edges_within_ignores_outside_links(seeded):
    edges = graph.edges_within(("a", "b"))
    assert [(edge["src"], edge["dst"]) for edge in edges] == [("a", "b")]


def test_search_matches_part_of_value(seeded):
    assert [node["id"] for node in graph.search("example")] == ["b", "d"]


def test_statistics_counts_kinds_and_relations(seeded):
    stats = graph.statistics()
    assert stats["nodes"] == 4
    assert stats["edges"] == 3
    assert stats["by_kind"]["ip"] == 1
    assert stats["by_relation"]["drops"] == 1


def test_clamp_limits_depth():
    assert service.clamp(0) == 1
    assert service.clamp(99) == 4
    assert service.clamp(3) == 3


def test_pivot_returns_center_and_depths(client):
    payload = client.get("/api/pivot", params={"node": "dom-cdn-login", "depth": 1}).json()
    assert payload["center"] == "dom-cdn-login"
    assert payload["depths"]["dom-cdn-login"] == 0
    assert payload["nodes"]


def test_node_endpoint_returns_empty_object_for_unknown(client):
    assert client.get("/api/nodes/нет").json() == {}


def test_graph_endpoint_has_stats(client):
    payload = client.get("/api/graph").json()
    assert payload["stats"]["nodes"] == len(payload["nodes"])
    assert payload["stats"]["edges"] == len(payload["edges"])


def test_import_merges_without_duplicates(client):
    before = client.get("/api/stats").json()["nodes"]
    payload = {"nodes": [{"id": "ip-203-0-113-24", "kind": "ip", "value": "203.0.113.24"}], "edges": []}
    assert client.post("/api/import", json=payload).json()["imported"] == 1
    assert client.get("/api/stats").json()["nodes"] == before


def test_schema_has_foreign_keys_and_view(client):
    sql = client.get("/api/schema").json()["sql"]
    assert "REFERENCES nodes" in sql
    assert "CREATE OR REPLACE VIEW links" in sql


def test_overview_statistics_match_tables(client):
    payload = client.get("/api/graph").json()
    assert payload["stats"]["by_kind"]["ip"] >= 1
    assert len(payload["nodes"][0]) >= 3

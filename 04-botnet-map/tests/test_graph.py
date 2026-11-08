from app import graph, store


def test_distances_follow_edges(tmp_path, monkeypatch):
    monkeypatch.setenv("F6_DB", str(tmp_path / "g.sqlite3"))
    store.load(
        {
            "nodes": [
                {"id": "a", "kind": "ip", "value": "203.0.113.1"},
                {"id": "b", "kind": "domain", "value": "b.example.com"},
                {"id": "c", "kind": "hash", "value": "d41d8cd98f00b204e9800998ecf8427e"},
            ],
            "edges": [
                {"src": "a", "dst": "b", "relation": "resolves_to"},
                {"src": "b", "dst": "c", "relation": "drops"},
            ],
        }
    )
    assert graph.distances("a", 2) == {"a": 0, "b": 1, "c": 2}
    assert graph.distances("a", 1) == {"a": 0, "b": 1}


def test_traversal_is_undirected(tmp_path, monkeypatch):
    monkeypatch.setenv("F6_DB", str(tmp_path / "g2.sqlite3"))
    store.load(
        {
            "nodes": [{"id": "a", "kind": "ip", "value": "1.1.1.1"}, {"id": "b", "kind": "ip", "value": "2.2.2.2"}],
            "edges": [{"src": "a", "dst": "b", "relation": "proxies_to"}],
        }
    )
    assert graph.distances("b", 1) == {"b": 0, "a": 1}


def test_subgraph_includes_nodes_and_edges(client):
    payload = client.get("/api/pivot", params={"node": "ip-203-0-113-24", "depth": 1}).json()
    ids = {node["id"] for node in payload["nodes"]}
    assert "ip-203-0-113-24" in ids
    assert "dom-cdn-login" in ids
    assert payload["depths"]["ip-203-0-113-24"] == 0
    assert payload["edges"]


def test_pivot_depth_is_clamped(client):
    payload = client.get("/api/pivot", params={"node": "ip-203-0-113-24", "depth": 99}).json()
    assert max(payload["depths"].values()) <= 4


def test_unknown_node_returns_empty_marker(client):
    payload = client.get("/api/pivot", params={"node": "nope", "depth": 2}).json()
    assert payload["nodes"] == []


def test_statistics(client):
    payload = client.get("/api/stats").json()
    assert payload["nodes"] >= 18
    assert payload["edges"] >= 20
    assert payload["by_kind"]["ip"] >= 6


def test_search_by_value(client):
    payload = client.get("/api/nodes", params={"q": "example.com"}).json()
    assert any("example.com" in item["value"] for item in payload["items"])


def test_schema_is_postgres(client):
    payload = client.get("/api/schema").json()
    assert payload["dialect"] == "postgresql"
    assert "CREATE TABLE" in payload["sql"]
    assert "reachable" in payload["sql"]


def test_import_adds_nodes(client):
    before = client.get("/api/stats").json()["nodes"]
    payload = client.post(
        "/api/import",
        json={"nodes": [{"id": "ip-198-51-100-199", "kind": "ip", "value": "198.51.100.199"}], "edges": []},
    ).json()
    assert payload["imported"] == 1
    assert client.get("/api/stats").json()["nodes"] == before + 1

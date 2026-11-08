-- Схема для PostgreSQL: та же модель, что и в SQLite-стенде.
-- Используется, когда граф переезжает с локального файла в общий кластер.

CREATE TABLE IF NOT EXISTS nodes (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('ip', 'domain', 'hash', 'cert', 'email', 'asn', 'host')),
    value       TEXT NOT NULL,
    first_seen  DATE NOT NULL DEFAULT CURRENT_DATE,
    risk        SMALLINT NOT NULL DEFAULT 50 CHECK (risk BETWEEN 0 AND 100),
    tags        TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS edges (
    src         TEXT NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    dst         TEXT NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    relation    TEXT NOT NULL,
    confidence  SMALLINT NOT NULL DEFAULT 50 CHECK (confidence BETWEEN 0 AND 100),
    first_seen  DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (src, dst, relation)
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON edges (src);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges (dst);
CREATE INDEX IF NOT EXISTS idx_nodes_value ON nodes (value);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes (kind);

-- Ненаправленное представление для обхода в обе стороны.
CREATE OR REPLACE VIEW links AS
    SELECT src, dst, relation, confidence FROM edges
    UNION ALL
    SELECT dst, src, relation, confidence FROM edges;

-- Обход в ширину по графу от произвольной точки.
CREATE OR REPLACE FUNCTION reachable(start_id TEXT, max_depth INT)
RETURNS TABLE (id TEXT, depth INT) LANGUAGE sql AS $$
    WITH RECURSIVE reach(id, depth) AS (
        SELECT start_id, 0
        UNION
        SELECT links.dst, reach.depth + 1
        FROM links JOIN reach ON links.src = reach.id
        WHERE reach.depth < max_depth
    )
    SELECT reach.id, MIN(reach.depth)::INT AS depth FROM reach GROUP BY reach.id;
$$;

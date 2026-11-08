# 04 · Botnet Map

Карта инфраструктуры: узлы (IP, домены, хеши, сертификаты, регистранты, ASN, скомпрометированные хосты) и рёбра с уверенностью. Пивот — обход графа в обе стороны.

## Как устроен обход

Обход не пишется циклами, а делегируется базе: рекурсивный CTE по представлению `links`, где `edges` развёрнуты в обе стороны.

```sql
WITH RECURSIVE reach(id, depth) AS (
    SELECT ?, 0
    UNION
    SELECT links.dst, reach.depth + 1
    FROM links JOIN reach ON links.src = reach.id
    WHERE reach.depth < ?
)
SELECT id, MIN(depth) FROM reach GROUP BY id;
```

Для боевого PostgreSQL в `data/schema.postgres.sql` лежит та же модель (CHECK на `kind`, FK, индексы) и функция `reachable(start_id, max_depth)`.

## API

| Метод | Путь | Смысл |
| --- | --- | --- |
| GET | `/api/graph` | все узлы и рёбра + агрегаты |
| GET | `/api/stats` | счётчики по видам и связям |
| GET | `/api/nodes?q=` | поиск узла по значению |
| GET | `/api/nodes/{id}` | карточка узла |
| GET | `/api/pivot?node=&depth=` | подграф в радиусе N шагов (1–4) |
| GET | `/api/schema` | DDL и функция для PostgreSQL |
| POST | `/api/import` | импорт узлов и рёбер |

## Запуск и тесты

```powershell
.\run.ps1                                  # http://127.0.0.1:8104
..\.venv\Scripts\python.exe -m pytest . -q
```

Фронтенд рисует граф на canvas: раскладка пружинами считается в браузере, клик по узлу делает пивот на один шаг и подсвечивает связи с подписями отношений.

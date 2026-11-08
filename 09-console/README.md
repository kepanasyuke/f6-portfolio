# 09 · Console

Единое приложение поверх бэкендов стенда: один интерфейс на все бизнес-задачи команды Threat Intelligence.

## Как устроено

Консоль не хранит данные — она ходит по HTTP в API семи сервисов и собирает ответы:

| Раздел | Источник |
| --- | --- |
| Обзор | `GET /api/stats`, `/api/detections`, `/api/metrics`, `/api/overview` всех сервисов |
| Индикаторы | Feed Harvester `GET /api/iocs` |
| Хантинг | Hunt Rules `GET /api/rules`, `/api/replay`, `POST /api/evaluate` |
| Журналы | Log Forge `GET /api/search` |
| Инфраструктура | Botnet Map `GET /api/graph`, `/api/pivot` |
| Домены | Typosquat Radar `POST /api/scan` |
| Отчёты | Report Builder `GET/POST /api/reports` |
| Хосты | Ops Agent `GET /api/overview`, `POST /api/hosts/{name}/check` |

Если сервис не отвечает, консоль не падает: KPI считаются по доступным источникам, а сервис помечается `offline`. Ошибки транспорта превращаются в значения через `asyncio.gather(return_exceptions=True)` — без `try/except` и ранних выходов, как требует стиль проекта.

## API консоли

`/api/health`, `/api/overview`, `/api/indicators`, `/api/hunting`, `POST /api/hunting/run`, `/api/logs`, `/api/graph`, `/api/domains`, `/api/reports` (+ POST), `/api/hosts` (+ `POST /api/hosts/{name}/check`).

## Запуск

```powershell
.\run.ps1          # http://127.0.0.1:8210
```

Порт 8210 выбран вместе со всем стендом в диапазоне 8200–8210: диапазон 8100–8110 на этой машине занят сторонним приложением.

## Тесты

```powershell
..\.venv\Scripts\python.exe -m pytest . -q
```

Тесты подменяют транспорт `httpx.MockTransport`, поэтому не требуют запущенных сервисов: проверяются сборка сводки, проксирование разделов и деградация при недоступных сервисах.

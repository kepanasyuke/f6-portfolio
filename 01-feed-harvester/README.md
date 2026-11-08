# 01 · Feed Harvester

Парсинг внешних фидов и хранение индикаторов компрометации.

- **Форматы:** CSV, JSON, построчный TXT с деобфускацией (`hxxp`, `[.]`, `(.)`, `[at]`).
- **Нормализация:** определяет тип (ipv4, domain, url, md5, sha256, email), критичность, уверенность 0–100, теги.
- **Хранилище:** SQLite, дедупликация по `value`, при повторе берётся максимум уверенности и объединяются теги.
- **API:** `/api/iocs`, `/api/stats`, `/api/feeds`, `/api/ingest`, `/api/ingest/local`, `/api/ingest/all`.

## Запуск

```powershell
.\run.ps1
# http://127.0.0.1:8201 — интерфейс, /api/docs — OpenAPI
```

## Тесты

```powershell
..\.venv\Scripts\python.exe -m pytest . -q
```

## Как устроено

| Модуль | Роль |
| --- | --- |
| `app/parsers.py` | декодеры форматов, деобфускация, определение типа |
| `app/store.py` | схема SQLite, upsert, фильтры (без конкатенации значений в SQL) |
| `app/service.py` | сценарии: приём, поиск, агрегаты, автосев |
| `app/api.py` | REST, валидация формата через Pydantic |

Стиль кода подчинён правилам F6 из корневого `README.md`: функции в 1–2 инструкции, ровно один `return`, без `while`/`break`/`continue`.

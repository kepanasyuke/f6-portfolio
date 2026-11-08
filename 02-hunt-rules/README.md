# 02 · Hunt Rules

Движок правил хантинга: YAML-правило → прогон по потоку событий → детекции в SQLite.

## DSL правила

```yaml
id: F6-0003
title: Сетевое обращение к домену из фида DGA
severity: medium
tactic: command-and-control
technique: T1568.002
condition: all          # all | any
selection:
  event.type: network
  destination.domain:
    - cdn-login.example.com
    - "*.example.net"   # glob
  command_line: "re:(?i)iex"   # регулярное выражение
```

Поддерживается: точное значение (без учёта регистра), список = «любое из», glob `*`/`?`, префикс `re:` для регулярок, точечные пути (`process.parent.name`).

## API

| Метод | Путь | Смысл |
| --- | --- | --- |
| GET | `/api/rules` | библиотека правил и файлы-источники |
| POST | `/api/rules` | добавить правило из YAML (SQLite) |
| POST | `/api/validate` | проверка YAML без сохранения |
| GET | `/api/events` | поток событий |
| POST | `/api/evaluate` | прогон (опционально `rule_ids`) |
| POST | `/api/replay` | прогон + запись детекций |
| GET | `/api/detections` | сохранённые детекции |

## Запуск и тесты

```powershell
.\run.ps1                                  # http://127.0.0.1:8102
..\.venv\Scripts\python.exe -m pytest . -q
```

Дедупликация детекций — по паре `(rule_id, event_id)`, повторный replay не размножает записи.

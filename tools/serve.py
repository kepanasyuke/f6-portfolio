r"""Дев-запуск стенда отдельными процессами, которые живут дольше родительской оболочки.

Запуск: ..\.venv\Scripts\python.exe tools\serve.py start|stop|status
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
MANIFEST = LOGS / "serve.json"
FLAGS = (
    subprocess.DETACHED_PROCESS
    | subprocess.CREATE_NEW_PROCESS_GROUP
    | subprocess.CREATE_BREAKAWAY_FROM_JOB
)
SERVICES = (
    ("site", 8200, None),
    ("01-feed-harvester", 8201, "01-feed-harvester"),
    ("02-hunt-rules", 8202, "02-hunt-rules"),
    ("03-log-forge", 8203, "03-log-forge"),
    ("04-botnet-map", 8204, "04-botnet-map"),
    ("05-typosquat-radar", 8205, "05-typosquat-radar"),
    ("06-report-builder", 8206, "06-report-builder"),
    ("07-ops-agent", 8207, "07-ops-agent"),
    ("08-data-portal", 8209, "08-data-portal"),
    ("09-console", 8210, "09-console"),
)
ACTIONS = {"start": "start", "stop": "stop", "status": "status"}


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else "start"
    return ACTIONS.get(action, "status") and dispatch(action)


def dispatch(action: str) -> int:
    return {"start": start, "stop": stop, "status": status}[action]()


def start() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    return announce(spawn_all())


def spawn_all() -> tuple:
    started = tuple(spawn(name, port, folder) for name, port, folder in SERVICES)
    return remember(started)


def remember(started: tuple) -> tuple:
    MANIFEST.write_text(json.dumps(started, ensure_ascii=False), encoding="utf-8")
    return started


def announce(started: tuple) -> int:
    print(f"запущено процессов: {len(started)}")
    return 0


def spawn(name: str, port: int, folder: str | None) -> dict:
    process = launch(name, port, folder)
    return {"name": name, "port": port, "pid": process.pid}


def launch(name: str, port: int, folder: str | None):
    return subprocess.Popen(
        arguments(port, folder),
        cwd=working_dir(folder),
        stdout=log(name, "out"),
        stderr=log(name, "err"),
        creationflags=FLAGS,
        close_fds=True,
    )


def working_dir(folder: str | None) -> str:
    return str(ROOT / folder) if folder else str(ROOT)


def arguments(port: int, folder: str | None) -> list[str]:
    return site_arguments(port) if folder is None else service_arguments(port, folder)


def site_arguments(port: int) -> list[str]:
    return [str(PYTHON), "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(ROOT)]


def service_arguments(port: int, folder: str) -> list[str]:
    return [
        str(PYTHON),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--app-dir",
        str(ROOT / folder),
    ]


def log(name: str, kind: str):
    return open(LOGS / f"{name}.{kind}.log", "ab", buffering=0)


def stop() -> int:
    return print_stopped(entries())


def print_stopped(items: list[dict]) -> int:
    print(f"остановлено: {sum(terminate(item) for item in items)} из {len(items)}")
    return 0


def terminate(item: dict) -> bool:
    result = subprocess.run(["taskkill", "/PID", str(item["pid"]), "/F"], capture_output=True, check=False)
    return result.returncode == 0


def status() -> int:
    return print_status(entries())


def print_status(items: list[dict]) -> int:
    print("\n".join(f"{item['port']} {item['name']}: {alive(item['pid'])}" for item in items))
    return 0


def alive(pid: int) -> str:
    probe = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    return "жив" if str(pid) in probe.stdout else "мёртв"


def entries() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []


if __name__ == "__main__":
    sys.exit(main(sys.argv))

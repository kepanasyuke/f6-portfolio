"""Нормализация журналов: syslog, nginx combined, CSV выгрузка Windows."""
import csv
import io
import re

from app import config

SYSLOG = re.compile(
    r"^(?P<ts>[A-Z][a-z]{2}\s+\d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) "
    r"(?P<process>\w+)\[(?P<pid>\d+)\]: (?P<message>.*)$"
)
AUTH_OK = re.compile(r"Accepted password for (?P<user>\S+) from (?P<ip>[\d.]+)")
AUTH_FAIL = re.compile(r"Failed password for (?P<user>\S+) from (?P<ip>[\d.]+)")
AUTH_INVALID = re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>[\d.]+)")
NGINX = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+) [^"]*" '
    r'(?P<status>\d{3}) (?P<size>\d+) "[^"]*" "(?P<agent>[^"]*)"$'
)
MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def parse(format_name: str, content: str) -> tuple[dict, ...]:
    return DECODERS.get(format_name, decode_syslog)(content)


def decode_syslog(content: str) -> tuple[dict, ...]:
    return tuple(auth_document(line) for line in content.splitlines() if line.strip())


def auth_document(line: str) -> dict:
    match = SYSLOG.match(line)
    return auth_fields(match, line) if match else unmatched(line)


def auth_fields(match, line: str) -> dict:
    return {**base_auth(match), **outcome_of(match.group("message")), "message": line.strip()}


def base_auth(match) -> dict:
    return {
        "@timestamp": syslog_time(match.group("ts")),
        "host": match.group("host"),
        "event.category": "authentication",
        "process.name": match.group("process"),
        "process.pid": int(match.group("pid")),
        "event.dataset": "auth",
    }


def outcome_of(message: str) -> dict:
    attempts = (
        outcome_match(AUTH_OK, "success", message),
        outcome_match(AUTH_FAIL, "failure", message),
        invalid_user(message),
    )
    return next((item for item in attempts if item), {})


def outcome_match(pattern: re.Pattern, outcome: str, message: str) -> dict:
    found = pattern.search(message)
    return credential(found, outcome) if found else {}


def credential(found, outcome: str) -> dict:
    return {"event.outcome": outcome, "user.name": found.group("user"), "source.ip": found.group("ip")}


def invalid_user(message: str) -> dict:
    found = AUTH_INVALID.search(message)
    return credential(found, "failure") if found else {}


def syslog_time(stamp: str) -> str:
    return iso_time(stamp.split())


def iso_time(parts: list[str]) -> str:
    month, day, clock = parts[0], int(parts[1]), parts[2]
    return f"{config.DEFAULT_YEAR}-{MONTHS.get(month, 1):02d}-{day:02d}T{clock}Z"


def decode_nginx(content: str) -> tuple[dict, ...]:
    return tuple(request_document(line) for line in content.splitlines() if line.strip())


def request_document(line: str) -> dict:
    match = NGINX.match(line)
    return request_fields(match, line) if match else unmatched(line)


def request_fields(match, line: str) -> dict:
    return {
        "@timestamp": http_time(match.group("ts")),
        "event.category": "web",
        "event.dataset": "nginx",
        "source.ip": match.group("ip"),
        "http.request.method": match.group("method"),
        "url.path": match.group("path"),
        "http.response.status_code": int(match.group("status")),
        "http.response.body.bytes": int(match.group("size")),
        "user_agent.original": match.group("agent"),
        "message": line.strip(),
    }


def http_time(stamp: str) -> str:
    date, _, clock = stamp.partition(":")
    return f"{iso_clock(date.replace('/', '-'), clock)}{offset_tail(clock)}"


def iso_clock(date: str, rest: str) -> str:
    day, month, year = date.split("-")
    return f"{year}-{month_number(month):02d}-{int(day):02d}T{clock_part(rest)}"


def clock_part(rest: str) -> str:
    return rest.split(" ")[0]


def offset_tail(rest: str) -> str:
    return rest.split(" ")[1].replace("+", "+") if " " in rest else "Z"


def month_number(name: str) -> int:
    return MONTHS.get(name, 1)


def decode_windows(content: str) -> tuple[dict, ...]:
    return tuple(windows_document(row) for row in csv.DictReader(io.StringIO(content)) if row)


def windows_document(row: dict) -> dict:
    return {
        "@timestamp": row.get("timestamp", ""),
        "host": row.get("host", ""),
        "event.category": "process",
        "event.dataset": "windows-security",
        "event.code": row.get("event_id", ""),
        "user.name": row.get("user", ""),
        "process.name": row.get("process", ""),
        "message": row.get("message", ""),
    }


def unmatched(line: str) -> dict:
    return {"@timestamp": "", "event.category": "unknown", "event.dataset": "raw", "message": line.strip()}


DECODERS = {
    "syslog": decode_syslog,
    "auth": decode_syslog,
    "nginx": decode_nginx,
    "windows": decode_windows,
    "csv": decode_windows,
}
FORMATS = {"auth": "syslog", "access": "nginx", "windows": "windows", "secure": "syslog"}

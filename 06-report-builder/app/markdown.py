"""Минимальный рендер Markdown в HTML: заголовки, списки, цитаты, таблицы, инлайн-разметка."""
import re
from html import escape
from itertools import groupby

INLINE = (
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"`(.+?)`"), r"<code>\1</code>"),
    (re.compile(r"\[(.+?)\]\((.+?)\)"), r'<a href="\2" rel="noreferrer">\1</a>'),
)
PATTERNS = (
    ("rule", lambda line: len(line) >= 3 and set(line) <= {"-", "*", "_"}),
    ("h3", lambda line: line.startswith("### ")),
    ("h2", lambda line: line.startswith("## ")),
    ("h1", lambda line: line.startswith("# ")),
    ("bullet", lambda line: line.startswith("- ")),
    ("ordered", lambda line: bool(re.match(r"^\d+\. ", line))),
    ("quote", lambda line: line.startswith("> ")),
    ("table", lambda line: line.startswith("|")),
)
SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")
ORDERED = re.compile(r"^\d+\. ")


def inline(text: str) -> str:
    return fold(escape(text), INLINE)


def fold(text: str, rules: tuple) -> str:
    return text if not rules else fold(rules[0][0].sub(rules[0][1], text), rules[1:])


def classify(line: str) -> str:
    return kind_of(line.strip())


def kind_of(line: str) -> str:
    return next((kind for kind, check in PATTERNS if check(line)), "paragraph") if line else "blank"


def to_html(markdown: str) -> str:
    return render_blocks(tuple(markdown.splitlines()))


def render_blocks(lines: tuple[str, ...]) -> str:
    return "".join(render(kind, tuple(group)) for kind, group in groupby(lines, classify))


def render(kind: str, lines: tuple[str, ...]) -> str:
    return RENDERERS[kind](lines)


def render_blank(_lines: tuple[str, ...]) -> str:
    return ""


def render_rule(_lines: tuple[str, ...]) -> str:
    return "<hr />"


def render_h1(lines: tuple[str, ...]) -> str:
    return "".join(f"<h1>{inline(line.strip()[2:])}</h1>" for line in lines)


def render_h2(lines: tuple[str, ...]) -> str:
    return "".join(f"<h2>{inline(line.strip()[3:])}</h2>" for line in lines)


def render_h3(lines: tuple[str, ...]) -> str:
    return "".join(f"<h3>{inline(line.strip()[4:])}</h3>" for line in lines)


def render_bullet(lines: tuple[str, ...]) -> str:
    return f"<ul>{render_items(lines, 2)}</ul>"


def render_ordered(lines: tuple[str, ...]) -> str:
    return f"<ol>{render_items(lines, len(ORDERED.match(lines[0]).group(0)))}</ol>"


def render_items(lines: tuple[str, ...], offset: int) -> str:
    return "".join(f"<li>{inline(line.strip()[offset:])}</li>" for line in lines)


def render_quote(lines: tuple[str, ...]) -> str:
    return f"<blockquote>{inline(' '.join(line.strip()[2:] for line in lines))}</blockquote>"


def render_table(lines: tuple[str, ...]) -> str:
    rows = tuple(line for line in lines if not SEPARATOR.match(line.strip()))
    return f"<table>{render_rows(rows)}</table>"


def render_rows(lines: tuple[str, ...]) -> str:
    return "".join(render_row(line, position) for position, line in enumerate(lines))


def render_row(line: str, position: int) -> str:
    return f"<tr>{''.join(render_cell(cell, position) for cell in cells(line))}</tr>"


def cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def render_cell(cell: str, position: int) -> str:
    return f"<th>{inline(cell)}</th>" if not position else f"<td>{inline(cell)}</td>"


def render_paragraph(lines: tuple[str, ...]) -> str:
    return f"<p>{inline(' '.join(line.strip() for line in lines))}</p>"


RENDERERS = {
    "blank": render_blank,
    "rule": render_rule,
    "h1": render_h1,
    "h2": render_h2,
    "h3": render_h3,
    "bullet": render_bullet,
    "ordered": render_ordered,
    "quote": render_quote,
    "table": render_table,
    "paragraph": render_paragraph,
}

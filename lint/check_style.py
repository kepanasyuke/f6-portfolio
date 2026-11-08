import ast
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_STATEMENTS = 2
MAX_RETURNS = 1
SKIP_DIRS = {".venv", "__pycache__", "node_modules", "build", "dist", ".git", "tests"}
FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
BANNED_NODES = {ast.While: "while", ast.Break: "break", ast.Continue: "continue"}


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    rule: str
    message: str

    def as_text(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def iter_sources(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if not SKIP_DIRS.intersection(path.parts)))


def load_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def body_statements(node: ast.AST) -> tuple[ast.stmt, ...]:
    return tuple(statement for statement in node.body if not is_docstring(statement))


def is_docstring(node: ast.AST) -> bool:
    return isinstance(node, ast.Expr) and is_string(node.value)


def is_string(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def walk_without_nested(node: ast.AST) -> tuple[ast.AST, ...]:
    nested = tuple(child for child in ast.iter_child_nodes(node) if not isinstance(child, FUNCTION_NODES))
    return (node, *tuple(item for child in nested for item in walk_without_nested(child)))


def count_returns(node: ast.AST) -> int:
    return len(tuple(child for child in walk_without_nested(node) if isinstance(child, ast.Return)))


def check_tree(path: Path, tree: ast.Module) -> tuple[Violation, ...]:
    return function_violations(path, tree) + banned_violations(path, tree)


def function_violations(path: Path, tree: ast.Module) -> tuple[Violation, ...]:
    functions = tuple(node for node in ast.walk(tree) if isinstance(node, FUNCTION_NODES))
    return tuple(violation for node in functions for violation in check_function(path, node))


def banned_violations(path: Path, tree: ast.Module) -> tuple[Violation, ...]:
    return tuple(check_banned(path, node) for node in ast.walk(tree) if type(node) in BANNED_NODES)


def check_function(path: Path, node: ast.AST) -> tuple[Violation, ...]:
    violations = (
        length_violation(path, node),
        return_violation(path, node),
    )
    return tuple(item for item in violations if item)


def length_violation(path: Path, node: ast.AST) -> Violation | None:
    return excessive(path, node, "F6S001", len(body_statements(node)), MAX_STATEMENTS, "инструкций")


def return_violation(path: Path, node: ast.AST) -> Violation | None:
    return excessive(path, node, "F6S002", count_returns(node), MAX_RETURNS, "выходов")


def excessive(path: Path, node: ast.AST, rule: str, actual: int, limit: int, unit: str) -> Violation | None:
    return None if actual <= limit else make(path, node, rule, limit_message(node, actual, limit, unit))


def limit_message(node: ast.AST, actual: int, limit: int, unit: str) -> str:
    return f"{node.name}: {actual} {unit}, максимум {limit}"


def make(path: Path, node: ast.AST, rule: str, message: str) -> Violation:
    return Violation(str(path), node.lineno, rule, message)


def check_banned(path: Path, node: ast.AST) -> Violation:
    return make(path, node, "F6S003", f"запрещена конструкция {BANNED_NODES[type(node)]}")


def check_file(path: Path) -> tuple[Violation, ...]:
    return check_tree(path, load_tree(path))


def collect(root: Path) -> tuple[Violation, ...]:
    return tuple(violation for path in iter_sources(root) for violation in check_file(path))


def describe(violations: tuple[Violation, ...]) -> str:
    return f"F6 style check: {len(violations)} нарушений\n" + "\n".join(item.as_text() for item in violations)


def report(violations: tuple[Violation, ...]) -> int:
    print(describe(violations))
    return 1 if violations else 0


def configure_stdout() -> None:
    sys.stdout.reconfigure(encoding="utf-8")


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    return report(collect(root))


if __name__ == "__main__":
    configure_stdout()
    sys.exit(main(sys.argv))

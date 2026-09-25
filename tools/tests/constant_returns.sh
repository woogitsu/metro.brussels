#!/usr/bin/env bash
set -eu
python3 - <<'PY'
#!/usr/bin/env python3
"""6.D345: census of constant returns in top-level non-test Python readers.

This is a syntax census, not the lost 6.D315/326 shape classifier. It reports
the exact population it scans and never presents historical counts as current.
"""

import ast
from collections import Counter
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools" / "tests"))
from tree_walk import znajdz  # noqa: E402 — shared .gitignore-aware traversal


def own_exits(function):
    """Yield returns/yields owned by function, excluding nested callables."""
    stack = list(reversed(function.body))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)):
            yield node
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def classify(exits):
    returns = [item.value if item.value is not None else ast.Constant(value=None)
               for item in exits if isinstance(item, ast.Return)]
    constants = [value for value in returns if isinstance(value, ast.Constant)]
    if not constants:
        return None
    other = [value for value in returns if not isinstance(value, ast.Constant)]
    kinds = {type(value.value).__name__ for value in constants}
    if (other or len(kinds) > 1 or
            any(isinstance(item, (ast.Yield, ast.YieldFrom)) for item in exits)):
        group = "mixed"
    elif all(value.value is None for value in constants):
        group = "none_only"
    else:
        group = "constants_only"
    nonconstants = [type(value).__name__ for value in other]
    if len(kinds) > 1:
        nonconstants.append("ConstantKinds=" + "/".join(sorted(kinds)))
    return group, len(constants), nonconstants


def census():
    readers = []
    for found in znajdz(str(ROOT / "tools" / "tests"), "*.py", root=str(ROOT)):
        path = Path(found)
        if path.parent != ROOT / "tools" / "tests":
            continue  # same module-level population as the historical census
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("test_") or node.name == "main":
                continue
            exits = list(own_exits(node))
            if not exits:
                continue
            result = classify(exits)
            if result is None:
                continue
            name = f"{path.relative_to(ROOT).as_posix()}:{node.lineno}:{node.name}"
            group, number, other = result
            readers.append((name, group, number, other))
    return readers


if __name__ == "__main__":
    fixture = ast.parse("def f():\n    if flag:\n        return None\n    return []\n")
    if classify(list(own_exits(fixture.body[0])))[0] != "mixed":
        raise SystemExit("synthetic mixed-return control failed")
    fixture = ast.parse("def f():\n    if flag:\n        return None\n    return True\n")
    if classify(list(own_exits(fixture.body[0])))[0] != "mixed":
        raise SystemExit("synthetic mixed-return control failed")
    rows = census()
    counts = Counter(group for _, group, _, _ in rows)
    print(f"readers_with_constant={len(rows)}")
    print(f"constant_returns={sum(n for _, _, n, _ in rows)}")
    for group in ("constants_only", "none_only", "mixed"):
        print(f"{group}={counts[group]}")
    if sum(counts.values()) != len(rows):
        raise SystemExit("category counts do not sum to the population")
    for name, group, n, others in rows:
        print(f"{group}\t{name}\tconstants={n}\tother={','.join(others)}")
PY

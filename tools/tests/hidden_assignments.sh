#!/usr/bin/env bash
set -eu
python3 - <<'PY'
"""6.D346 syntax census. Run from repository root."""
import ast
from collections import Counter
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'tools' / 'tests'))
from tree_walk import znajdz


def names(target):
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for elt in target.elts for name in names(elt)]
    if isinstance(target, ast.Starred):
        return names(target.value)
    return []


def own_nodes(function):
    stack = list(reversed(function.body))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        yield node
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def direct_shape(node):
    if isinstance(node, (ast.List, ast.ListComp)):
        return 'list'
    if isinstance(node, (ast.Tuple,)):
        return 'tuple'
    if isinstance(node, (ast.Set, ast.SetComp)):
        return 'set'
    if isinstance(node, (ast.Dict, ast.DictComp)):
        return 'dict'
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == 'len':
            return 'int'
        if (node.func.id == 'sum' and node.args and
                isinstance(node.args[0], ast.GeneratorExp) and
                isinstance(node.args[0].elt, ast.Constant) and
                type(node.args[0].elt.value) is int):
            return 'int'
        if node.func.id in ('sorted', 'list'):
            return 'list'
    return None


def unpacked_expr(target, value, wanted):
    if isinstance(target, ast.Name):
        return value if target.id == wanted else None
    if not isinstance(target, (ast.Tuple, ast.List)):
        return None
    if not isinstance(value, (ast.Tuple, ast.List)) or len(target.elts) != len(value.elts):
        return None
    for part, expression in zip(target.elts, value.elts):
        found = unpacked_expr(part, expression, wanted)
        if found is not None:
            return found
    return None


sample = ast.parse('def f():\n    out, n = [], 0\n    n += 1\n    return out\n')
sample_nodes = list(own_nodes(sample.body[0]))
sample_assign = next(n for n in sample_nodes if isinstance(n, ast.Assign))
if direct_shape(unpacked_expr(sample_assign.targets[0], sample_assign.value, 'out')) != 'list':
    raise SystemExit('fixture: literal tuple unpacking lost the list shape')
if direct_shape(unpacked_expr(sample_assign.targets[0], sample_assign.value, 'n')) != 'int':
    raise SystemExit('fixture: literal tuple unpacking lost the int shape')
sample = ast.parse('def f():\n    out, n = read()\n    return out\n')
sample_nodes = list(own_nodes(sample.body[0]))
sample_assign = next(n for n in sample_nodes if isinstance(n, ast.Assign))
if unpacked_expr(sample_assign.targets[0], sample_assign.value, 'out') is not None:
    raise SystemExit('fixture: call result was treated as direct tuple shape')


all_unpack = []
all_aug = []
reader_rows = []
for found in znajdz(str(ROOT / 'tools' / 'tests'), '*.py', root=str(ROOT)):
    path = Path(found)
    if path.parent != ROOT / 'tools' / 'tests':
        continue
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source, filename=str(path))
    short = path.relative_to(ROOT).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, (ast.Tuple, ast.List)):
                    all_unpack.append((short, node.lineno, names(target), ast.unparse(node.value)))
        elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
            all_aug.append((short, node.lineno, names(node.target), ast.unparse(node.value),
                            type(node.target).__name__))
    for fn in tree.body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if fn.name.startswith('test_') or fn.name == 'main':
            continue
        nodes = list(own_nodes(fn))
        returned = {n.value.id for n in nodes if isinstance(n, ast.Return)
                    and isinstance(n.value, ast.Name)}
        for name in sorted(returned):
            unpack_nodes = [n for n in nodes if isinstance(n, ast.Assign) and any(
                isinstance(t, (ast.Tuple, ast.List)) and name in names(t)
                for t in n.targets)]
            aug_nodes = [n for n in nodes if isinstance(n, ast.AugAssign)
                         and isinstance(n.op, ast.Add)
                         and isinstance(n.target, ast.Name) and n.target.id == name]
            unpack = [(n.lineno, ast.unparse(n.value)) for n in unpack_nodes]
            aug = [(n.lineno, ast.unparse(n.value)) for n in aug_nodes]
            if unpack or aug:
                candidate_shapes = []
                for assignment in unpack_nodes:
                    for target in assignment.targets:
                        if isinstance(target, (ast.Tuple, ast.List)) and name in names(target):
                            expression = unpacked_expr(target, assignment.value, name)
                            candidate_shapes.append(direct_shape(expression))
                if aug_nodes:
                    first_aug = min(node.lineno for node in aug_nodes)
                    plain = [n for n in nodes if isinstance(n, ast.Assign)
                             and n.lineno < first_aug
                             and any(isinstance(t, ast.Name) and t.id == name
                                     for t in n.targets)]
                    candidate_shapes.extend(direct_shape(n.value) for n in plain)
                resolved = (bool(candidate_shapes) and None not in candidate_shapes
                            and len(set(candidate_shapes)) == 1)
                if resolved and candidate_shapes[0] == 'int':
                    resolved = all(direct_shape(node.value) == 'int' for node in aug_nodes)
                reader_rows.append((short, fn.lineno, fn.name, name, unpack, aug,
                                    candidate_shapes[0] if resolved else 'UNKNOWN'))

print(f'unpack_sites={len(all_unpack)}')
print(f'unpack_statements={len(set((row[0], row[1]) for row in all_unpack))}')
print(f'plus_equals_sites={len(all_aug)}')
print(f'plus_equals_name_targets={sum(bool(row[2]) for row in all_aug)}')
print(f'returned_name_pairs={len(reader_rows)}')
print(f'returned_unpack_pairs={sum(bool(row[4]) for row in reader_rows)}')
print(f'returned_plus_equals_pairs={sum(bool(row[5]) for row in reader_rows)}')
print(f'returned_assignment_sites={sum(len(row[4]) + len(row[5]) for row in reader_rows)}')
print(f'resolved_without_next_jump={sum(row[6] != "UNKNOWN" for row in reader_rows)}')
print(f'unknown_without_next_jump={sum(row[6] == "UNKNOWN" for row in reader_rows)}')
if (sum(row[6] != 'UNKNOWN' for row in reader_rows) +
        sum(row[6] == 'UNKNOWN' for row in reader_rows) != len(reader_rows)):
    raise SystemExit('resolved and unknown readers do not partition the population')
for row in reader_rows:
    print('PAIR', *row, sep='\t')
PY

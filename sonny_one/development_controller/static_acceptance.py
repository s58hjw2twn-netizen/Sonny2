"""Static acceptance checks for RES-001 proposed patches.

This gate checks diff shape and required semantics without executing any
candidate code. It is an additional filter, not a substitute for isolated
execution, independent tests, or review.
"""
from __future__ import annotations

import ast

from sonny_one.development_controller.coding_context import TARGET


def check_mean_change(before: str, after: str) -> dict:
    if not isinstance(before, str) or not isinstance(after, str):
        raise ValueError("source must be text")
    old = ast.parse(before)
    new = ast.parse(after)
    def split_module(module):
        body = list(module.body)
        doc = None
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            doc = body.pop(0).value.value
        if any(not isinstance(node, ast.FunctionDef) for node in body):
            raise ValueError("top-level executable statements and imports prohibited")
        return doc, body
    old_doc, old_body = split_module(old)
    new_doc, new_body = split_module(new)
    if old_doc != new_doc:
        raise ValueError("module documentation changed")
    old_defs = {node.name: node for node in old_body}
    new_defs = {node.name: node for node in new_body}
    if set(old_defs) != {"mean", "smallest", "largest"} or set(new_defs) != set(old_defs):
        raise ValueError("unexpected function changes")
    for name in ("smallest", "largest"):
        if ast.dump(old_defs[name], include_attributes=False) != ast.dump(
            new_defs[name], include_attributes=False
        ):
            raise ValueError("unrelated function modified")
    mean = new_defs["mean"]
    if mean.decorator_list or mean.args.defaults or mean.args.kw_defaults:
        raise ValueError("decorators and defaults prohibited")
    for node in ast.walk(mean):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal,
                             ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node is not mean:
            raise ValueError("nested definitions and imports prohibited")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in {"sum", "len", "ValueError"}:
                raise ValueError("unapproved function call")
    if len(mean.args.args) != 1 or mean.args.args[0].arg != "values":
        raise ValueError("mean signature changed")
    if not any(isinstance(n, ast.Raise)
               and isinstance(n.exc, ast.Call)
               and isinstance(n.exc.func, ast.Name)
               and n.exc.func.id == "ValueError"
               for n in ast.walk(mean)):
        raise ValueError("mean must explicitly raise ValueError")
    if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "sum" for n in ast.walk(mean)):
        raise ValueError("mean must retain sum")
    return {"target": TARGET, "static_checks_passed": True,
            "candidate_executed": False, "independent_tests_passed": False}

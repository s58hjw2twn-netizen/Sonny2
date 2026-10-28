"""Safety regression tests for the local-only MCP research spike.

These tests require only Python's standard library and intentionally do not
claim an MCP network handshake or OAuth verification.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "sonny" / "mcp_local_spike.py"

def test_local_spike_is_loopback_only():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    constructors = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "FastMCP"
    ]
    assert len(constructors) == 1
    kwargs = {item.arg: item.value for item in constructors[0].keywords}
    assert ast.literal_eval(kwargs["host"]) == "127.0.0.1"
    assert ast.literal_eval(kwargs["stateless_http"]) is True
    assert ast.literal_eval(kwargs["json_response"]) is True

def test_local_spike_has_only_read_only_status_tool():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    decorated = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "mcp"
            and dec.func.attr == "tool"
            for dec in node.decorator_list
        )
    ]
    assert [node.name for node in decorated] == ["protocol_status"]
    function = decorated[0]
    assert len(function.body) == 2  # docstring and static return
    assert isinstance(function.body[-1], ast.Return)
    assert isinstance(function.body[-1].value, ast.Dict)
    assert all(isinstance(v, ast.Constant) for v in function.body[-1].value.values)

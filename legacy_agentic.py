#!/usr/bin/env python3
"""
Legacy subprocess plugin for Open Agentic 2.0.

This script:

- Reads a single JSON object from stdin:
    {"op": "<operation>", "params": {...}}
- Writes a single JSON object to stdout:
    {
        "ok": bool,
        "result": any,
        "evidence": {"coverage": float, "sources": [...]},
        "reasons": [str, ...]
    }

It is designed to be called by LegacySubprocess in agentic2_micro_plugin.py.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any, Dict


Output = Dict[str, Any]


def _error(reason: str) -> Output:
    return {
        "ok": False,
        "result": None,
        "evidence": None,
        "reasons": [reason],
    }


def _ok(result: Any, sources=None, coverage: float = 0.80) -> Output:
    if sources is None:
        sources = ["legacy"]
    return {
        "ok": True,
        "result": result,
        "evidence": {
            "coverage": float(coverage),
            "sources": list(sources),
        },
        "reasons": [],
    }


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_echo(params: Dict[str, Any]) -> Output:
    """
    Simple echo tool for demos and tests.
    """
    msg = str(params.get("msg", "") or "")
    if not msg:
        return _error("empty msg")
    return _ok(msg, sources=["legacy", "echo"], coverage=0.85)


def handle_summarize(params: Dict[str, Any]) -> Output:
    """
    Very small summarizer: just trims long strings.
    """
    text = str(params.get("text", "") or "")
    if not text:
        return _error("missing text")
    summary = (text[:200] + "…") if len(text) > 200 else text
    return _ok(
        {"summary": summary},
        sources=["legacy", "summarize"],
        coverage=0.85,
    )


def handle_health(params: Dict[str, Any]) -> Output:
    """
    Health-check endpoint so you can verify the plugin is alive.
    """
    return _ok(
        {"status": "ok", "info": "legacy_agentic alive"},
        sources=["legacy", "health"],
        coverage=1.0,
    )


HANDLERS = {
    "echo": handle_echo,
    "summarize": handle_summarize,
    "health": handle_health,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw or "{}")
    except Exception:
        out = _error("invalid JSON on stdin")
        print(json.dumps(out))
        return

    op = str(data.get("op") or data.get("operation") or "").strip()
    params = data.get("params") or {}

    if not op:
        print(json.dumps(_error("missing op")))
        return

    if not isinstance(params, dict):
        print(json.dumps(_error("params must be an object")))
        return

    handler = HANDLERS.get(op)
    if handler is None:
        print(json.dumps(_error(f"unknown op: {op}")))
        return

    try:
        out = handler(params)
    except Exception:
        # Fail safe: log details to stderr, return a generic error to the caller.
        sys.stderr.write("legacy_agentic internal error:\n")
        traceback.print_exc(file=sys.stderr)
        out = _error("internal error")

    print(json.dumps(out))


if __name__ == "__main__":
    main()

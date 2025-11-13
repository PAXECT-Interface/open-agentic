"""
Test utilities for working with Open Agentic audit files.

These helpers are intentionally small and safe:
- They never modify audits.
- They only read and classify them.
"""

from __future__ import annotations

import glob
import json
import pathlib
from typing import Dict, Iterable, List, Optional


def iter_audit_paths(pattern: str = "audit_*.jsonl") -> Iterable[pathlib.Path]:
    """
    Yield all audit jsonl paths that match the given glob pattern.
    """
    for p in sorted(glob.glob(pattern)):
        yield pathlib.Path(p)


def read_lines(path: pathlib.Path) -> List[str]:
    """
    Read an audit file into a list of lines. Returns [] if reading fails.
    """
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def first_key_id(lines: List[str]) -> Optional[str]:
    """
    Return the first non-null key_id found in the given audit lines, or None.
    """
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        kid = ev.get("key_id")
        if kid is not None:
            return kid
    return None


def load_events(path: pathlib.Path) -> List[Dict]:
    """
    Load all events from an audit file as JSON objects.
    Invalid lines are skipped.
    """
    out: List[Dict] = []
    for line in read_lines(path):
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict):
            out.append(ev)
    return out

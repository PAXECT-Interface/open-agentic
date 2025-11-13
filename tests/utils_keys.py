"""
Test utilities for handling HMAC key IDs used in Open Agentic audits.

These helpers are intentionally conservative:
- They never create or modify real keys.
- They only inspect key_id usage and help you reason about where keys are needed.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .utils_audit import iter_audit_paths, read_lines, first_key_id


def collect_key_ids() -> Dict[str, int]:
    """
    Scan all audit_*.jsonl files and return a map:
        {key_id: count_of_files_using_this_key_id}

    key_id == None (plain SHA) is not included.
    """
    counts: Dict[str, int] = {}
    for path in iter_audit_paths():
        lines = read_lines(path)
        kid = first_key_id(lines)
        if kid is None:
            continue
        counts[kid] = counts.get(kid, 0) + 1
    return counts


def collect_plain_audits() -> List[pathlib.Path]:
    """
    Return a list of audit files that do not use a key_id (plain SHA256 chain).
    """
    plain: List[pathlib.Path] = []
    for path in iter_audit_paths():
        lines = read_lines(path)
        kid = first_key_id(lines)
        if kid is None:
            plain.append(path)
    return plain


def parse_keys_json_env() -> Dict[str, str]:
    """
    Parse KEYS_JSON from the environment, if present.

    Expected format:
        {"<key_id>": "<hex-key>", ...}

    Returns an empty dict if the variable is not set or invalid.
    """
    raw = os.environ.get("KEYS_JSON")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    # Keep only string-to-string mappings
    return {
        str(k): str(v)
        for k, v in data.items()
        if isinstance(k, str) and isinstance(v, str)
    }


def keys_dir_candidates(base: str = "keys") -> Iterable[Tuple[str, pathlib.Path]]:
    """
    Yield (key_id, path) pairs for files named <key_id>.key in the given base dir.
    """
    d = pathlib.Path(base)
    if not d.is_dir():
        return []
    out: List[Tuple[str, pathlib.Path]] = []
    for p in d.glob("*.key"):
        key_id = p.stem
        out.append((key_id, p))
    return out

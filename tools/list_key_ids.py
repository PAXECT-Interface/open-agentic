#!/usr/bin/env python3
# List all key_ids found in audit_*.jsonl (safe to run locally; CI ignores if none)

import json, glob, pathlib, sys

def iter_audits():
    for p in sorted(glob.glob("audit_*.jsonl")):
        yield pathlib.Path(p)

def first_key_id(lines):
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        kid = ev.get("key_id")
        if kid is not None:
            return kid
    return None

def main():
    counts = {}
    plain = 0
    for path in iter_audits():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        kid = first_key_id(lines)
        if kid is None:
            plain += 1
        else:
            counts[kid] = counts.get(kid, 0) + 1

    print("=== Key IDs in audits ===")
    for kid, n in sorted(counts.items()):
        print(f"{kid:>12}  ({n} files)")
    print(f"\nPlain SHA-audits (key_id=None): {plain}")

if __name__ == "__main__":
    main()

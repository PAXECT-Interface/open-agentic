#!/usr/bin/env python3
"""
Audit-chain maintenance helper for Open Agentic 2.0.

- Scans all audit_*.jsonl files in the repository root
- Validates the hash chain using Audit.validate_chain
- If the chain is broken:
  - Moves the original file to audit_corrupted/<name>
  - Writes a <name>_salvaged.jsonl file with the valid prefix only
"""

import pathlib
from typing import List, Tuple

from agentic2_micro_plugin import Audit

CORRUPTED_DIR = pathlib.Path("audit_corrupted")


def _read_lines(path: pathlib.Path) -> List[str]:
    return path.read_text().splitlines()


def _salvage_file(path: pathlib.Path, lines: List[str]) -> None:
    """
    Find the first line where the chain breaks, move the original file
    to audit_corrupted/, and write a _salvaged version with only
    the valid prefix of lines.
    """
    good_lines: List[str] = []
    broken_at: Tuple[int, str] | None = None

    for idx, line in enumerate(lines, start=1):
        good_lines.append(line)
        if not Audit.validate_chain(good_lines, key_hex=None):
            # Last appended line breaks the chain; remove it again.
            good_lines.pop()
            broken_at = (idx, line)
            break

    if broken_at is None:
        print(f"Chain appears valid while salvaging, nothing to do: {path.name}")
        return

    CORRUPTED_DIR.mkdir(exist_ok=True)
    corrupted_dest = CORRUPTED_DIR / path.name
    path.replace(corrupted_dest)

    line_no, bad_line = broken_at
    print(f"Broken chain detected in {path.name} at line {line_no}")
    print(f"Offending line:")
    print(bad_line)
    print(f"Original audit moved to {corrupted_dest}")

    salvaged_name = f"{path.stem}_salvaged{path.suffix}"
    salvaged_path = path.with_name(salvaged_name)
    salvaged_path.write_text("\n".join(good_lines) + "\n")
    print(f"Salvaged audit written to {salvaged_path.name}")


def main() -> None:
    root = pathlib.Path(".")
    audits = sorted(
        root.glob("audit_*.jsonl"),
        key=lambda p: p.stat().st_mtime,
    )

    if not audits:
        print("No audit_*.jsonl files found.")
        return

    for path in audits:
        lines = _read_lines(path)
        if not lines:
            print(f"Empty audit file skipped: {path.name}")
            continue

        if Audit.validate_chain(lines, key_hex=None):
            print(f"Chain OK: {path.name}")
        else:
            _salvage_file(path, lines)


if __name__ == "__main__":
    main()

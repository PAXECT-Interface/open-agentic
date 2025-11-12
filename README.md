

---

# Open Agentic — Agentic 2.0 Framework

**Open, verifiable, and safe** — a lightweight foundation for auditable AI agents.
Fail-closed orchestration • Tamper-evident audit chains • Zero-trust verification

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-brightgreen)]()

---

## Overview

Open Agentic 2.0 is a compact framework for verifiable agent execution.
Every action is recorded in an append-only cryptographic audit chain (SHA-256 or HMAC), making each run tamper-evident, reproducible, and auditable.

### Motivation

Modern AI apps suffer from instability, corruption, and hallucinations.
Open Agentic introduces a verifiable kernel where each step is evidence-based, policy-constrained, and logged for post-hoc review.

---

## Core Features

| Area                       | Description                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| Orchestrator (fail-closed) | Executes only allowlisted tools within time/step budgets; abstains on uncertainty.                |
| Audit Chain                | Append-only JSONL with per-event fsync; chained SHA-256 or HMAC; short key_id fingerprint.        |
| Policy Engine              | Allowlist, per-tool budgets, max steps, wall-clock time.                                          |
| Verifier                   | Requires evidence; enforces min_coverage/min_sources; task-specific output shape checks.          |
| Plugins                    | Legacy Subprocess (stdin/stdout JSON) and Meta HTTP (POST JSON) with timeouts and trimmed errors. |
| Testing                    | Pytest suite for functional behavior and audit chain validation.                                  |

---

## Installation

```bash
git clone https://github.com/<org>/open-agentic.git
cd open-agentic
python3 -m venv .venv
source .venv/bin/activate
# stdlib-only; PyYAML is optional if you load YAML configs
pip install pyyaml  # optional
```

---

## Quick Start

Run a demo plan:

```bash
python agentic2_micro_plugin.py --plan plan.json --policy policy.yaml --bundle
```

Verify audit integrity and list key IDs:

```bash
pytest -q tests/test_audit_chain_all.py -vv
python tools/list_key_ids.py
```

Example report:

```
=== Audit Chain Report ===
ok: 4, broken: 0, skipped_no_key: 23
```

---

## Architecture

```
 Orchestrator (Policy)
      └── Verifier (evidence, coverage, sources, shape)
             │
             ▼
       Tools Registry ──> echo | summarize | legacy | meta
             │
             ▼
      Audit Chain (HMAC/SHA-256, fsync per event)
```

---

## Repository Structure

```
open-agentic/
├── agentic2_micro_plugin.py      # Main orchestrator
├── legacy_agentic.py             # Legacy subprocess plugin (stdin/stdout JSON)
├── meta_stub.py                  # HTTP plugin stub for local testing
├── plan.json / policy.yaml / plugins.yaml
├── tests/
│   ├── test_agentic2.py
│   ├── test_audit_chain_all.py
│   ├── utils_audit.py
│   └── utils_keys.py
└── tools/
    └── list_key_ids.py
```

---

## Security Model

* Fail-closed by default: no output passes without verified evidence.
* Tamper-evident logging: each event is chained to the previous and flushed to disk.
* Zero-trust boundaries: plugins are isolated via subprocess or HTTP.
* Deterministic bundles: optional `bundle_<trace>.json` with plan/policy/code hashes for reproducibility.

---

## CLI Reference (micro)

```
python agentic2_micro_plugin.py \
  --plan plan.json \
  --policy policy.yaml \
  --plugins plugins.yaml \
  --hmac <hex-key> \
  --min_coverage 0.75 \
  --min_sources 2 \
  --bundle \
  --dry-run
```

* `--hmac`: hex key for HMAC audit chains (optional; without it, plain SHA-256 is used).
* `--min_coverage`, `--min_sources`: verifier thresholds.
* `--bundle`: writes a reproducibility bundle with code/policy hashes.
* `--dry-run`: validates plan/policy and exits without executing tools.

---

## Key Management

* HMAC runs log a short `key_id` (first 12 hex of SHA-256 over the raw key bytes).
* Provide keys via:

  * Environment variable `KEYS_JSON` mapping `{key_id: key_hex}`, or
  * Files at `keys/<key_id>.key` containing the full hex key.
* `tools/list_key_ids.py` scans audits, prints all key_ids, and can generate placeholder files to help key distribution.

---

## Testing

Run the full suite:

```bash
pytest -q -vv
```

Key tests:

* `tests/test_agentic2.py`: orchestrator, policy budgets, verifier thresholds, task-shape checks.
* `tests/test_audit_chain_all.py`: validates hash chains across all `audit_*.jsonl` files, skipping those without available keys.
* Session summary in `tests/conftest.py`: prints an audit integrity report after tests.

---

## Example Audit Event (truncated)

```json
{
  "ts": 1762886368.792943,
  "trace": "34997dfe-594e-4112-a7b8-5290c80a1d6e",
  "type": "success",
  "details": {
    "task": "meta",
    "result": "{\"extracted\":\"dummy content from https://example.org/doc\"}",
    "evidence": {"coverage": 0.85, "sources": ["meta_stub", "crawler"]}
  },
  "prev": "…",
  "key_id": "b16de09ae524",
  "chain": "55af0c3fde94379f3d6a3f530c96ee76…"
}
```

---

## Contributing

Contributions are welcome: plugins, adapters, tests, and documentation.
Please ensure all changes pass the test suite and keep the tamper-evident guarantees intact.

```bash
pytest -q -vv
```

---

## License

MIT © 2025 PAXECT — Open Agentic Project
Free for academic, research, and commercial use, provided audit integrity is preserved.

---



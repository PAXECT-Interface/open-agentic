<p align="center">
  <img src="logo-open-agentic.png" alt="Open Agentic 2.0 logo" width="220">
</p>


---

# Open Agentic — Agentic 2.0 Framework

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-brightgreen)]()
[![CI](https://github.com/PAXECT-Interface/open-agentic/actions/workflows/ci.yml/badge.svg)](https://github.com/PAXECT-Interface/open-agentic/actions/workflows/ci.yml)
![Release](https://img.shields.io/github/v/release/PAXECT-Interface/open-agentic)

Open Agentic 2.0 — v0.1.0 (Public Preview) — Nov 12, 2025

Open Agentic 2.0 is founded and maintained by **PAXECT** and released under the Apache-2.0 license as a community-driven, audit-first agent framework.


**Open, verifiable, and safe** — a lightweight foundation for auditable AI agents.
Fail-closed orchestration • Tamper-evident audit chains • Zero-trust verification

---

## Overview

Open Agentic 2.0 is a compact framework for **verifiable agent execution**.
Every action is recorded in an append-only **cryptographic audit chain** (SHA-256 or HMAC), making each run **tamper-evident, reproducible, and auditable**.

### Motivation

Modern AI apps suffer from instability, corruption, and hallucinations.
Open Agentic introduces a **verifiable kernel** where each step is evidence-based, policy-constrained, and logged for post-hoc review.

---

## Why Open Agentic?

* **Audit-first:** every step is cryptographically chained and fsync’d for tamper evidence.
* **Fail-closed by design:** if evidence or shape checks fail, the orchestrator abstains.
* **Zero-trust boundaries:** legacy code via subprocess, remote agents via HTTP—always isolated and time-boxed.
* **Minimal surface area:** pure stdlib (PyYAML optional), simple manifests, predictable CLI.
* **Production-friendly:** deterministic bundles (hashes for code/policy/plan), simple key management, full pytest suite.
* **Roadmap & community**- Roadmap & community: [GitHub Discussions](https://github.com/PAXECT-Interface/open-agentic/discussions) · [GitHub Issues](https://github.com/PAXECT-Interface/open-agentic/issues) — see these for planned versions and ways to get involved.
 

---


## Core Features

| Area                       | Description                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| Orchestrator (fail-closed) | Executes only allowlisted tools within time/step budgets; abstains on uncertainty.                |
| Audit Chain                | Append-only JSONL with per-event fsync; chained SHA-256 or HMAC; short `key_id` fingerprint.      |
| Policy Engine              | Allowlist, per-tool budgets, max steps, wall-clock time.                                          |
| Verifier                   | Requires evidence; enforces `min_coverage`/`min_sources`; task-specific output shape checks.      |
| Plugins                    | Legacy Subprocess (stdin/stdout JSON) and Meta HTTP (POST JSON) with timeouts and trimmed errors. |
| Testing                    | Pytest suite for functional behavior and audit chain validation.                                  |

---

## Getting Started

1. **Clone & enter**

```bash
git clone https://github.com/PAXECT-Interface/open-agentic.git
cd open-agentic
```

2. **Create a virtual environment**

```bash
python -m venv .venv    # on some systems: python3 -m venv .venv

# Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell/cmd):
.venv\Scripts\activate
```

3. **Install dependencies**

Minimal setup (only YAML support):

```bash
pip install pyyaml
```

Or install all development dependencies:

```bash
pip install -r requirements.txt
```

4. **Run the demo plan**

```bash
python agentic2_micro_plugin.py --plan plan.json --policy policy.yaml --bundle
```

5. **Verify audit integrity and list key IDs**

```bash
pytest -q tests/test_audit_chain_all.py -vv
python tools/list_key_ids.py
```

---

## Environment & Supported Platforms

Open Agentic 2.0 targets **Python 3.10+** on:

* Linux
* macOS
* Windows (PowerShell or cmd)

The core uses the Python standard library plus a few small dependencies declared in `requirements.txt`.


---
## Quick Start

Run the standard demo:

```bash
python agentic2_micro_plugin.py --plan plan.json --policy policy.yaml --bundle
```

Example audit report:

```
=== Audit Chain Report ===
ok: 4, broken: 0, skipped_no_key: 23
```

### Minimal Echo Demo

Run a single tool directly from Python:

```bash
python - <<'PY'
from agentic2_micro_plugin import TOOLS
out = TOOLS["echo"]({"msg": "Hello, Open Agentic 2.0!"})
print(out)
PY
```

Expected output (shape may vary):

```python
{'ok': True,
 'result': 'Hello, Open Agentic 2.0!',
 'evidence': {'coverage': 0.8, 'sources': ['echo', 'caller']},
 'reasons': []}
```

---

## Comparison to AutoGen

| Aspect          | **Open Agentic 2.0**                                      | **Microsoft AutoGen**                      |
| --------------- | --------------------------------------------------------- | ------------------------------------------ |
| Audit Chain     | Cryptographic chain (SHA-256 or HMAC), fsync per event    | Logging only; no cryptographic chaining    |
| Fail-Closed     | Orchestrator abstains/blocks on uncertainty               | Agents continue unless explicitly coded    |
| Policy Engine   | Allowlist + per-tool budgets + max steps/time (YAML/JSON) | No built-in policy layer                   |
| Verifier        | Evidence required; min_coverage/min_sources; shape checks | No built-in verifier                       |
| Isolation       | Subprocess/HTTP plugins with strict timeouts              | In-process agents; optional external tools |
| Dependencies    | Python stdlib (+ optional PyYAML)                         | OpenAI/Azure SDKs; optional MCP/npm        |
| Reproducibility | Optional `bundle_<trace>.json` with hashes                | Not a core feature                         |
| License         | Apache-2.0                                                | MIT                                        |

Reference: **[microsoft/autogen](https://github.com/microsoft/autogen)**

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

* **Fail-closed by default:** no output passes without verified evidence.
* **Tamper-evident logging:** each event is chained to the previous and flushed to disk.
* **Zero-trust boundaries:** plugins are isolated via subprocess or HTTP.
* **Deterministic bundles:** optional `bundle_<trace>.json` with plan/policy/code hashes for reproducibility.

**Security notes**

* Never commit real HMAC keys. The `keys/` directory should be git-ignored.
* Prefer ephemeral keys for local testing; distribute production keys out-of-band.

---

## CLI Reference (micro)

```bash
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
* `tools/list_key_ids.py` scans audits, prints all `key_id`s, and can generate placeholder files to help key distribution.

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

## Demos & Screenshots

* **Asciinema demo (coming soon)** — visualize a run and the resulting audit chain.
* **Screenshots (coming soon)** — quick overview of audit reports and CI status.

---

## Changelog

See **[CHANGELOG.md](CHANGELOG.md)** for what’s new in v2.0 and subsequent releases.

---

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines. We welcome contributions of all kinds: bug fixes, new features, tests, examples, and documentation improvements.

* Issues: **[GitHub Issues](https://github.com/PAXECT-Interface/open-agentic/issues)**
* Discussions: **[GitHub Discussions](https://github.com/PAXECT-Interface/open-agentic/discussions)**
* Community chat: **Discord (coming soon)**
* News & updates: **Project blog (coming soon)**

---

## FAQ

See **[FAQ](FAQ.md)** for answers to common topics (auditing, HMAC keys, plugin manifests, evidence thresholds). If you don’t find what you’re looking for, open a discussion.

---

## Legal Notices

Unless otherwise noted:

* **Code** in this repository is licensed under the **Apache License, Version 2.0**. See **[LICENSE](LICENSE)**.
* **Documentation** (README, guides, FAQs) is also provided under **Apache-2.0**, unless a file header states a different license.

**Trademarks.** “Open Agentic” and any associated logos are names used by the community project. The licenses for this project do **not** grant rights to use project names, logos, or trademarks. Please follow applicable trademark guidelines of the respective owners. If you reference the project, use plain text attribution and link to the repo.

**Privacy.** This open-source project does not collect personal data by default. If you deploy services (e.g., web endpoints, telemetry, error reporting), provide your own privacy notice and comply with applicable laws and policies.

**Reservation of Rights.** Contributors reserve all other rights not expressly granted under the applicable licenses.

---

*Looking to extend or embed Open Agentic in production? See the “Security & Audit” section for guidance on HMAC key management, fsync policies, and chain validation.*

2025 PAXECT — Open Agentic Project

---







<p align="center">
  <img src="ChatGPT Image 13 nov 2025, 10_50_22.png" alt="Open Agentic 2.0 logo" width="220">
</p>

---

# Open Agentic — Agentic 2.0 Framework

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-brightgreen)]()
[![CI](https://github.com/PAXECT-Interface/open-agentic/actions/workflows/ci.yml/badge.svg)](https://github.com/PAXECT-Interface/open-agentic/actions/workflows/ci.yml)
![Release](https://img.shields.io/github/v/release/PAXECT-Interface/open-agentic)
[![Governance Layer](https://img.shields.io/badge/role-agentic_governance_layer-0059b3)]()





Open Agentic 2.0 — v0.1.0 (Public Preview) — Nov 12, 2025

Open Agentic 2.0 is founded and maintained by **PAXECT** and released under the Apache-2.0 license as a community-driven, audit-first agent framework.

> **Positioning:** Open Agentic is a *thin, pluggable governance layer* for AI agents.  
> You can use it standalone, or put it **in front of existing stacks** (AutoGen, custom “meta agents”, legacy tools) as an evidence-based control layer.

**Open, verifiable, and safe** — a lightweight foundation for auditable AI agents.  
Fail-closed orchestration • Tamper-evident audit chains • Zero-trust verification

---

## Overview

Open Agentic 2.0 is a compact framework for **verifiable agent execution**.

Every action is recorded in an append-only **cryptographic audit chain** (SHA-256 or HMAC), making each run **tamper-evident, reproducible, and auditable**.

The core orchestrator:

- Executes only allowlisted tools
- Enforces budgets and evidence thresholds
- Abstains on uncertainty instead of “hallucinating” a best guess

---

## Motivation

Modern AI apps and agent frameworks (including AutoGen-style multi-agent systems) share the same problems:

- Hard to see **who did what**, with which model/tool, and why
- No guarantees that data or results haven’t been **tampered with**
- “Best-effort” behavior instead of **fail-closed** when evidence is weak

Open Agentic focuses on one thing: a **verifiable kernel** that can sit underneath or in front of your agents:

- Each step is **policy-constrained** (allowlist + budgets)
- Each result is **evidence-based** (coverage + sources)
- Each event is **chained and fsync’d** for audit and forensics

You can keep your existing agents, tools and LLM prompts — Open Agentic becomes the **governance and audit layer** around them.

---

## Why Open Agentic?

- **Audit-first:** every step is cryptographically chained and fsync’d for tamper evidence.
- **Fail-closed by design:** if evidence or shape checks fail, the orchestrator abstains.
- **Zero-trust boundaries:** legacy code via subprocess; remote/meta agents via HTTP — always isolated and time-boxed.
- **Minimal surface area:** pure stdlib (PyYAML optional), simple manifests, predictable CLI.
- **Production-friendly:** deterministic bundles (`bundle_<trace>.json` with hashes for code/policy/plan), simple key management, full pytest suite.
- **Plug & play governance:** can wrap AutoGen agents, in-house meta agents, or classic microservices as tools under a single policy and audit model.

---

## Core Features

| Area                       | Description                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| Orchestrator (fail-closed) | Executes only allowlisted tools within time/step budgets; abstains on uncertainty.               |
| Audit Chain                | Append-only JSONL with per-event fsync; chained SHA-256 or HMAC; short `key_id` fingerprint.     |
| Policy Engine              | Allowlist, per-tool budgets, max steps, wall-clock time.                                         |
| Verifier                   | Requires evidence; enforces `min_coverage` / `min_sources`; task-specific output shape checks.   |
| Plugins                    | Legacy Subprocess (stdin/stdout JSON) and Meta HTTP (POST JSON) with timeouts and trimmed errors.|
| Testing & Playbook         | Pytest suite + root-level **Test Playbook** (`OPEN_AGENTIC_TESTS.md`) for reproducible scenarios.|

---

## Getting Started

### 1. Clone & enter

```bash
git clone https://github.com/PAXECT-Interface/open-agentic.git
cd open-agentic
````

### 2. Create a virtual environment

```bash
python -m venv .venv    # on some systems: python3 -m venv .venv

# Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell/cmd):
.venv\Scripts\activate
```

### 3. Install dependencies

Minimal setup (YAML + dev dependencies):

```bash
pip install -r requirements.txt
```

For ultra-minimal experiments you can also just:

```bash
pip install pyyaml
```

…but the test suite expects the full `requirements.txt`.

### 4. Run the demo plan

```bash
python agentic2_micro_plugin.py \
  --plan plan.json \
  --policy policy.yaml \
  --bundle
```

### 5. Verify audit integrity and list key IDs

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

Example audit report (from tests):

```text
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
{
  'ok': True,
  'result': 'Hello, Open Agentic 2.0!',
  'evidence': {'coverage': 0.8, 'sources': ['echo', 'caller']},
  'reasons': []
}
```

---

## Using Open Agentic as a Layer on Top of AutoGen / Meta Agents

Open Agentic is not a “chatbot framework” by itself.
Think of it as a **governance and audit kernel** that you can put around existing agent systems such as:

* Microsoft **AutoGen**
* Custom meta-agents
* In-house orchestrators
* Classic microservices

The pattern is simple:

1. **Wrap your agent as a tool**

   * Expose the agent as either:

     * a **subprocess** that reads/writes JSON on stdin/stdout, or
     * an **HTTP endpoint** that accepts/returns JSON.
   * In Open Agentic this is how `legacy_agentic.py` (subprocess) and `meta_stub.py` (HTTP) work.

2. **Describe it in `plugins.yaml`**

   * Give the tool a name (`autogen_chat`, `meta_coordinator`, …).
   * Specify how to call it (subprocess command or URL).
   * Define expected input/output shape.

3. **Constrain it with policy + verifier**

   * Use `policy.yaml` to:

     * put a **budget** on steps, time and invocations per tool,
     * allowlist only the tools you trust.
   * Use verifier thresholds (`min_coverage`, `min_sources`) so that:

     * if the agent returns weak or empty evidence, the orchestrator **does not treat it as done**.
   * Evidence from your AutoGen/meta agent becomes part of the same cryptographic audit chain.

4. **Audit everything**

   * Each call to your AutoGen/meta agent is an event in `audit_<trace>.jsonl`.
   * You can replay and analyze: what the agent saw, what it returned, which policies were applied.

The included `evil_meta_low_evidence.py` shows the value of this model:

* It behaves like a “helpful” meta agent (`ok: true`) but always returns weak evidence.
* With `min_coverage=0.75` and `min_sources=2`, Open Agentic counts only **2 of 3** steps as done.
* The audit log + bundle make this difference explicit and verifiable.

The same principle applies if you swap in a real AutoGen-based agent instead of the evil stub.

---

## Comparison to AutoGen

Open Agentic is not a competitor to AutoGen — it is a **governance and audit layer** that can sit on top.

| Aspect              | **Open Agentic 2.0**                                             | **Microsoft AutoGen**                   |
| ------------------- | ---------------------------------------------------------------- | --------------------------------------- |
| Primary focus       | Evidence-based orchestration + cryptographic audit chain         | Multi-agent conversations / workflows   |
| Audit Chain         | SHA-256 / HMAC chain, fsync per event                            | Logging only; no cryptographic chaining |
| Fail-Closed         | Orchestrator abstains/blocks on uncertainty                      | Agents continue unless explicitly coded |
| Policy Engine       | Allowlist, budgets, max steps/time (YAML/JSON)                   | No built-in policy/verifier kernel      |
| Verifier            | Evidence required (`coverage`, `sources`, shape checks)          | No first-class evidence model           |
| Integration pattern | Treat AutoGen agents as tools (subprocess/HTTP) under governance | AutoGen orchestrates agents itself      |
| Dependencies        | Python stdlib (+ optional PyYAML)                                | OpenAI/Azure SDKs, optional MCP/npm     |
| Reproducibility     | `bundle_<trace>.json` with hashes for code/policy/plan           | Not a core feature                      |
| License             | Apache-2.0                                                       | MIT                                     |

Recommended pattern:

* Use **AutoGen** (or any agent system) to explore strategies and interactions.
* Put **Open Agentic** in front as the **control plane** when you care about:

  * auditability,
  * regulatory evidence,
  * incident forensics,
  * clear “who did what and under which policy”.

---

## Architecture

```text
 Orchestrator (Policy)
      └── Verifier (evidence, coverage, sources, shape)
             │
             ▼
       Tools Registry ──> echo | summarize | legacy | meta | evil_meta
             │
             ▼
      Audit Chain (HMAC/SHA-256, fsync per event)
```

* **legacy**: `legacy_agentic.py` subprocess (e.g. old code, scripts, even AutoGen-based apps)
* **meta**: `meta_stub.py` HTTP tool for normal meta-agent behavior
* **evil_meta**: `evil_meta_low_evidence.py` to simulate low-evidence or adversarial agents

---

## Repository Structure

```text
open-agentic/
├── agentic2_micro_plugin.py       # Main micro-orchestrator
├── legacy_agentic.py              # Legacy subprocess plugin (stdin/stdout JSON)
├── meta_stub.py                   # HTTP plugin stub for local testing
├── evil_meta_low_evidence.py      # Adversarial meta-agent (weak evidence demo)
├── maintain_audits.py             # Audit-chain maintenance / self-healing helper
├── plan.json                      # Demo plan
├── policy.yaml                    # Default policy (budgets, thresholds)
├── plugins.yaml                   # Tool/plugin registry
├── OPEN_AGENTIC_TESTS.md          # Root test scenarios / Test Playbook
├── tests/
│   ├── test_agentic2.py           # Orchestrator + verifier tests
│   ├── test_audit_chain_all.py    # Audit-chain validation
│   ├── test_smoke.py              # Basic smoke tests
│   ├── utils_audit.py             # Shared audit helpers
│   └── utils_keys.py              # Key ID utilities for HMAC
├── tools/
│   └── list_key_ids.py            # Helper to list key IDs from audits
├── requirements.txt
├── pytest.ini
├── README.md
├── SECURITY.md
├── FAQ.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
└── ChatGPT Image 13 nov 2025, 10_50_22.png  # Logo
```

For a detailed, copy-pasteable test flow (including adversarial and swarm scenarios), see:

* **`OPEN_AGENTIC_TESTS.md` – “Open Agentic 2.0 – Test Playbook”**

---

## Security Model

* **Fail-closed by default:** no output passes without verified evidence.
* **Tamper-evident logging:** each event is chained to the previous and flushed to disk.
* **Zero-trust boundaries:** plugins are isolated via subprocess or HTTP; legacy/third-party code never runs in-process with the orchestrator.
* **Deterministic bundles:** optional `bundle_<trace>.json` with plan/policy/code hashes for reproducibility and audits.

### Security notes

* Never commit real HMAC keys. The `keys/` directory (if you use one) should be git-ignored.
* Prefer ephemeral keys for local testing; distribute production keys out-of-band.
* Combine Open Agentic with your existing observability (logs/metrics/traces) for end-to-end incident analysis.

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
* `--min_coverage`, `--min_sources`: verifier thresholds for evidence.
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

## Testing & Test Playbook

Run the full pytest suite:

```bash
pytest -q -vv
```

Key tests:

* `tests/test_agentic2.py`: orchestrator, policy budgets, verifier thresholds, task-shape checks.
* `tests/test_audit_chain_all.py`: validates hash chains across all `audit_*.jsonl` files, skipping those without available keys.
* `tests/test_smoke.py`: basic sanity checks for orchestrator and audit machinery.

For **step-by-step root-level scenarios**, see:

* **`OPEN_AGENTIC_TESTS.md`** – includes:

  * Happy-path runs (`done: 3`)
  * Audit tampering + self-healing via `maintain_audits.py`
  * Direct legacy/meta checks
  * Adversarial meta (`evil_meta_low_evidence.py`, `done: 2`)
  * Mixed healthy/adversarial runs
  * Swarm-style stress scenarios

These flows are designed so developers on Linux and macOS can reproduce everything locally.

---

## Demos & Screenshots

* **Asciinema demo (planned)** — show a full run and audit-chain validation.
* **Screenshots (planned)** — CI status, audit reports, and bundle inspection.

---

## Changelog

See **[CHANGELOG.md](CHANGELOG.md)** for what’s new in v2.0 and future releases.

---

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines.

We welcome:

* Bug fixes and hardening

* New plugin types (tools)

* Better policies, examples and documentation

* Integrations with other agent stacks (AutoGen, LangGraph, custom orchestration, etc.)

* Issues: **[GitHub Issues](https://github.com/PAXECT-Interface/open-agentic/issues)**

* Discussions: **[GitHub Discussions](https://github.com/PAXECT-Interface/open-agentic/discussions)**

---

## FAQ

See **[FAQ](FAQ.md)** for answers on:

* audit chains (SHA vs HMAC),
* key management,
* plugin manifests,
* evidence thresholds,
* using Open Agentic as a governance layer for legacy/third-party agents.

---

## Legal Notices

Unless otherwise noted:

* **Code** in this repository is licensed under the **Apache License, Version 2.0**. See **[LICENSE](LICENSE)**.
* **Documentation** (README, guides, FAQs) is also provided under **Apache-2.0**, unless a file header states a different license.

**Trademarks.** “Open Agentic” and any associated logos are names used by the community project. The licenses for this project do **not** grant rights to use project names, logos, or trademarks. Please follow applicable trademark guidelines of the respective owners. If you reference the project, use plain text attribution and link to the repo.

**Privacy.** This open-source project does not collect personal data by default. If you deploy services (e.g., web endpoints, telemetry, error reporting), provide your own privacy notice and comply with applicable laws and policies.

**Reservation of Rights.** Contributors reserve all other rights not expressly granted under the applicable licenses.

---

*Looking to use Open Agentic as the safety/audit kernel under a larger agent platform?
Start with the demo plan, read [OPEN_AGENTIC_TESTS.md](OPEN_AGENTIC_TESTS.md) , then wrap your existing agents as tools under a single policy and audit chain.*

---
##  Support

For validation, integration help, or CI assistance:
📧 **[PAXECT-Team@outlook.com](mailto:PAXECT-Team@outlook.com)**

2025 PAXECT — Open Agentic Project








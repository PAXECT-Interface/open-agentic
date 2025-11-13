
# Open Agentic 2.0 – FAQ

This FAQ covers common questions about the Open Agentic 2.0 micro framework: what it does, how it works, and how to use it safely.

---

## What is Open Agentic 2.0?

Open Agentic 2.0 is a small, audit-first framework for running AI-powered “agents” in a verifiable way.

Instead of letting tools and models run freely, every step is:

- **Policy-controlled** (allowlist + budgets + time/step limits)
- **Evidence-verified** (coverage + number of sources)
- **Cryptographically chained** into an append-only audit log (SHA-256 or HMAC)

The goal is **trustworthy, tamper-evident execution**, not another “smart agent that does everything”.

---

## What problem does it solve?

Many agent frameworks are powerful but opaque:

- They mix side effects and tools without clear boundaries.
- Logs are easy to tamper with.
- There is no clear notion of “evidence” or “verification”.

Open Agentic takes the opposite stance:

- “If something cannot be justified, it should not ship a result.”
- “If logs can be tampered with, they are not really logs.”
- “If a tool is not allowlisted, it should never run.”

---

## How does the audit chain work?

Every event (run start, step start, success, abstain, etc.) is written as a JSON object and linked into a chain:

```text
chain_i = HMAC(key, chain_{i-1} + canonical_event_i)
````

or, if no HMAC key is used:

```text
chain_i = SHA256(chain_{i-1} + canonical_event_i)
```

This makes post-hoc tampering detectable.
The `Audit.validate_chain(...)` helper can verify a log file offline.

---

## Do I need HMAC keys to use this?

No.

* If you don’t provide an HMAC key, the audit chain uses plain SHA-256.
* You can still verify integrity with `Audit.validate_chain(lines, key_hex=None)`.

If you do want HMAC:

* Pass `--hmac <hex-key>` to the CLI.
* A short `key_id` is logged with each event.
* Keys are expected to be distributed out-of-band (e.g., secrets manager).

---

## How do I run the demo?

1. Start the meta HTTP stub in one shell:

   ```bash
   python meta_stub.py
   ```

2. In another shell, run the micro orchestrator with the sample plan and policy:

   ```bash
   python agentic2_micro_plugin.py \
     --plan plan.json \
     --policy policy.yaml \
     --plugins plugins.yaml \
     --bundle
   ```

This will:

* Call the `legacy` subprocess plugin (`legacy_agentic.py`)
* Call the `meta` HTTP stub (`meta_stub.py`)
* Run the local `summarize` tool
* Produce an `audit_<trace>.jsonl` and an optional `bundle_<trace>.json`

---

## How do I run the tests?

From the project root:

```bash
pytest -q -vv
```

Useful files:

* `tests/test_smoke.py` – basic “does it run and chain?” smoke test
* `tests/test_agentic2.py` – end-to-end test using `plan.json` and `policy.yaml`
* `tests/test_audit_chain_all.py` – validates audit chains (plain SHA), skips HMAC audits without keys
* `tools/list_key_ids.py` – simple helper to inspect key_ids in audit files

---

## Is this production-ready?

This repository is a **micro-core**, not a full platform.
It is intentionally small and auditable, and focuses on:

* Policy-enforced orchestration
* Cryptographic audit chains
* Basic evidence verification

For real production deployments you should still add:

* Operational logging / metrics
* Secure key management (KMS / secrets manager)
* Resource limits around subprocesses and HTTP calls
* Your own business-specific policies and tools

Think of this as a **foundation** for verifiable agents, not a full SaaS product.

---

## How do I contribute?

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

In short:

* Fork the repo
* Create a branch
* Add tests for your change
* Open a pull request

Bug reports, documentation improvements, and small focused features are all welcome.

---

## Where can I ask questions?

* GitHub Issues: bug reports and feature requests
* GitHub Discussions: design questions and broader ideas

If you build something cool on top of Open Agentic, please consider sharing it there so others can learn from it.





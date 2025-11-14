
# Open Agentic 2.0 – Root Test Scenarios

This document describes the core root-level tests that developers can run locally
(on Linux or macOS) to verify Open Agentic 2.0.  
Additional scenarios (e.g. swarm of adversarial agents) will be added later.

All commands assume:

- Repository root: `~/open-agentic`
- Virtualenv active: `source .venv/bin/activate`


---

## 1. Core pytest suite (root tests)

The main automated tests live under `tests/`:

- `tests/test_agentic2.py` – end-to-end tests for Open Agentic 2.0
- `tests/test_audit_chain_all.py` – audit-chain validation
- `tests/test_smoke.py` – smoke test for Audit and Orchestrator

Run the full suite:

```bash
cd ~/open-agentic
source .venv/bin/activate
pytest -q -vv
````

Expected:

* 4 tests collected
* All tests pass

---

## 2. Audit tampering and self-healing (`maintain_audits.py`)

This scenario shows:

* Tampering with an `audit_*.jsonl` file breaks the SHA chain and is detected.
* `maintain_audits.py` quarantines the corrupted audit and writes a `_salvaged` version.
* The audit-chain test becomes green again without manual file editing.

### 2.1 Start the healthy meta-agent

In Terminal 1:

```bash
cd ~/open-agentic
source .venv/bin/activate
python meta_stub.py
# Meta stub listening on http://127.0.0.1:8081
```

Leave this terminal running.

### 2.2 Run Open Agentic 2.0 (happy path, `done: 3`)

In Terminal 2:

```bash
cd ~/open-agentic
source .venv/bin/activate

python agentic2_micro_plugin.py \
  --plan plan.json \
  --policy policy.yaml \
  --plugins plugins.yaml \
  --min_coverage 0.75 \
  --min_sources 2 \
  --bundle
```

Example output shape:

```json
{
  "done": 3,
  "status": "OK",
  "trace": "1503d1d5-8fc1-481f-b750-e2836b9950e9",
  "audit_file": "audit_1503d1d5-8fc1-481f-b750-e2836b9950e9.jsonl",
  "bundle_file": "bundle_1503d1d5-8fc1-481f-b750-e2836b9950e9.json"
}
```

This confirms:

* The plan has three steps.
* All steps satisfy the evidence thresholds.
* A new `audit_*.jsonl` and `bundle_*.json` are written.

### 2.3 Intentionally corrupt the newest audit file

Use the newest `audit_*.jsonl` created in step 2.2:

```bash
cd ~/open-agentic
source .venv/bin/activate

python - <<'PY'
import pathlib

root = pathlib.Path(".")
audits = sorted(
    root.glob("audit_*.jsonl"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not audits:
    raise SystemExit("No audit_*.jsonl found")

f = audits[0]
print("Manipulating audit file:", f)

lines = f.read_text().splitlines()
if not lines:
    raise SystemExit("Audit file is empty")

# Simple corruption: change the first occurrence of "a" to "b" in the last line
lines[-1] = lines[-1].replace("a", "b", 1)
f.write_text("\n".join(lines) + "\n")
print("Last line has been corrupted.")
PY
```

Expected console output:

```text
Manipulating audit file: audit_1503d1d5-8fc1-481f-b750-e2836b9950e9.jsonl
Last line has been corrupted.
```

### 2.4 Verify that the audit-chain test fails

```bash
cd ~/open-agentic
source .venv/bin/activate

pytest -q tests/test_audit_chain_all.py -vv
```

Expected: the test fails, for example:

```text
AssertionError: Broken chain (plain SHA): audit_1503d1d5-8fc1-481f-b750-e2836b9950e9.jsonl
```

This proves that any modification of the audit log is detected by `Audit.validate_chain(...)`.

### 2.5 Run `maintain_audits.py` to self-heal and re-test

```bash
cd ~/open-agentic
source .venv/bin/activate

python maintain_audits.py
```

Typical output:

* Reports which `audit_*.jsonl` has a broken chain.
* Shows the line number where the chain breaks.
* Moves the original file to:
  `audit_corrupted/audit_<trace>.jsonl`
* Writes:
  `audit_<trace>_salvaged.jsonl` with only the valid prefix of lines.

Then run the audit-chain test again:

```bash
pytest -q tests/test_audit_chain_all.py -vv
```

Expected:

* 1 test collected (from `test_audit_chain_all.py`)
* Test passes

At this point:

* All `audit_*.jsonl` files in the repository root have valid SHA chains.
* The corrupted original is preserved under `audit_corrupted/` for forensic analysis.
* Developers do not need to manually edit any audit files; running `maintain_audits.py`
  is enough to restore a consistent state.



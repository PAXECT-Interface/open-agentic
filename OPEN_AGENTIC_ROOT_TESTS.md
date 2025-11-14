
# Open Agentic 2.0 – Test Playbook

This document describes the current test structure and manual test flows for Open Agentic 2.0.
It is intended for developers who want to verify behavior end-to-end, including adversarial
scenarios against legacy agents.

All commands assume:

- Repository root: `~/open-agentic`
- Virtualenv active: `source .venv/bin/activate`

## Repository sync

Make sure your local clone is up to date with `main`:

```bash
cd ~/open-agentic
git pull origin main
source .venv/bin/activate
```

All test commands in this document assume you are on the latest `main` branch.

---

## 1. Core pytest suite (root tests)

The main automated tests live under `tests/`:

* `tests/test_agentic2.py` – end-to-end tests for Open Agentic 2.0
* `tests/test_audit_chain_all.py` – audit-chain validation
* `tests/test_smoke.py` – basic smoke tests for Audit and Orchestrator

Run the full suite:

```bash
cd ~/open-agentic
source .venv/bin/activate
pytest -q -vv
```

Expected outcome (current state):

* 4 tests collected
* All tests pass

---

## 2. Happy-path run with healthy legacy + meta (`done: 3`)

### 2.1 Start the healthy meta-agent

In Terminal 1:

```bash
cd ~/open-agentic
source .venv/bin/activate
python meta_stub.py
# Meta stub listening on http://127.0.0.1:8081
```

Leave this terminal running.

### 2.2 Run Open Agentic 2.0

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

Example output:

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
* All steps meet the evidence thresholds.
* A new `audit_*.jsonl` and `bundle_*.json` are written.

---

## 3. Audit tampering and self-healing (`maintain_audits.py`)

This scenario shows:

* Tampering with the audit log breaks the SHA chain and is detected.
* `maintain_audits.py` quarantines the corrupted audit and writes a `_salvaged` version.
* The audit-chain test becomes green again without manual file editing.

### 3.1 Intentionally corrupt the newest audit file

Use the latest `audit_*.jsonl` produced in the previous step:

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

### 3.2 Verify that the audit-chain test fails

```bash
cd ~/open-agentic
source .venv/bin/activate

pytest -q tests/test_audit_chain_all.py -vv
```

Expected: the test fails with a message similar to:

```text
AssertionError: Broken chain (plain SHA): audit_1503d1d5-8fc1-481f-b750-e2836b9950e9.jsonl
```

### 3.3 Run `maintain_audits.py` to self-heal

```bash
cd ~/open-agentic
source .venv/bin/activate

python maintain_audits.py
```

Typical output:

* Reports which audit file has a broken chain.
* Shows where the chain breaks (line number and line content).
* Moves the original file to: `audit_corrupted/audit_<trace>.jsonl`
* Writes a new file: `audit_<trace>_salvaged.jsonl` with only the valid prefix of lines.

Then re-run the audit-chain test:

```bash
pytest -q tests/test_audit_chain_all.py -vv
```

Expected: the test now passes, because all `audit_*.jsonl` files in the root have valid chains.
The corrupted original is preserved under `audit_corrupted/` for forensic analysis.

---

## 4. Direct legacy and meta checks

These checks exercise the legacy agent and meta agent directly, without the full orchestrator.

### 4.1 Legacy agent direct call

```bash
cd ~/open-agentic
source .venv/bin/activate

python - <<'PY'
import json, subprocess

payload = {"op": "echo", "params": {"msg": "Hello from legacy direct"}}
p = subprocess.Popen(
    ["python3", "legacy_agentic.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)
out, _ = p.communicate(json.dumps(payload))
print(out)
PY
```

Expected JSON:

* `ok: true`
* `result: "Hello from legacy direct"`
* `evidence.coverage` around `0.85`
* `evidence.sources` containing `["legacy", "echo"]`

### 4.2 Meta stub direct HTTP call

Assuming `meta_stub.py` is running on `127.0.0.1:8081`:

```bash
curl -s -X POST http://127.0.0.1:8081 \
  -H "Content-Type: application/json" \
  -d '{"op": "echo", "params": {"msg": "Hello from meta direct"}}'
```

Expected JSON:

* `ok: true`
* `result: "Hello from meta direct"`
* `evidence.coverage` around `0.85`
* `evidence.sources` containing `["meta", "echo"]`

These tests confirm that both legacy and meta agents behave correctly as individual tools.

---

## 5. Adversarial meta-agent (low evidence)

This scenario introduces a meta-agent that pretends everything is fine (`ok: true`), but returns evidence that does not meet the policy thresholds. It is useful to test that the verifier and policy do not trust such responses.

### 5.1 Start the evil meta-agent

First, stop any running `meta_stub.py` on port 8081, then:

```bash
cd ~/open-agentic
source .venv/bin/activate
python evil_meta_low_evidence.py
# Evil meta (low evidence) listening on http://127.0.0.1:8081
```

This server returns:

* `ok: true`
* `coverage: 0.10` (below `min_coverage=0.75`)
* `sources: []` (below `min_sources=2`)

### 5.2 Run Open Agentic 2.0 against the evil meta-agent

In another terminal:

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

Expected behavior:

* The meta step produces weak evidence.
* The verifier or policy should not accept this evidence as satisfying the thresholds.
* The final summary (`done` count, reasons in the bundle) reflects that the meta step was rejected or not trusted.

Developers can inspect the generated `bundle_*.json` to see per-step evidence, coverage, sources and reasons.

---



## 6. Mixed healthy / adversarial runs

This scenario exercises Open Agentic 2.0 under alternating conditions:

* Healthy meta-agent (strong evidence)
* Adversarial meta-agent (weak evidence)
* Audit integrity maintained across runs via `maintain_audits.py`

It shows that the governance layer behaves consistently over time, even when the environment changes.

### 6.1 Run with healthy meta (`done: 3`)

Terminal 1:

```bash
cd ~/open-agentic
source .venv/bin/activate
python meta_stub.py
# Meta stub listening on http://127.0.0.1:8081
```

Terminal 2:

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

Expected:

* `done: 3`
* `status: "OK"`
* New `audit_*.jsonl` and `bundle_*.json`.

### 6.2 Run with adversarial meta (`done: 2`)

Stop the healthy meta-agent (`Ctrl+C` in Terminal 1) and start the evil meta-agent:

```bash
cd ~/open-agentic
source .venv/bin/activate
python evil_meta_low_evidence.py
# Evil meta (low evidence) listening on http://127.0.0.1:8081
```

In Terminal 2, run Open Agentic 2.0 again:

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

Expected:

* The JSON summary shows `done: 2` and `status: "OK"`.
* A new `bundle_*.json` is created for this run.

You can inspect the latest bundle:

```bash
python - <<'PY'
import json, pathlib

root = pathlib.Path(".")
bundles = sorted(
    root.glob("bundle_*.json"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if not bundles:
    raise SystemExit("No bundle_*.json found")

f = bundles[0]
print("Inspecting bundle:", f)
data = json.loads(f.read_text())
print(json.dumps(data, indent=2))
PY
```

The bundle reflects:

* A plan with three tasks (`legacy`, `meta`, `summarize`).
* Only two tasks fully counted as `done`, because the meta step does not meet `min_coverage` / `min_sources` and is not trusted as strong evidence.

### 6.3 Audit-chain consistency across runs

After running both the healthy and adversarial scenarios, verify that all audit files are still consistent:

```bash
cd ~/open-agentic
source .venv/bin/activate

pytest -q tests/test_audit_chain_all.py -vv
```

If any audit has been manually or externally tampered, the test will fail.

To repair and quarantine corrupted audits:

```bash
cd ~/open-agentic
source .venv/bin/activate

python maintain_audits.py
pytest -q tests/test_audit_chain_all.py -vv
```

Expected:

* All `audit_*.jsonl` files in the repository root have valid chains.
* Any corrupted audits have been moved to `audit_corrupted/` with a corresponding `_salvaged` version in the root.

---

## 7. Swarm-style stress scenario (multiple runs)

This scenario simulates a small "swarm" of runs over time, mixing healthy and adversarial
conditions. It does not introduce new code, but reuses the existing meta stub, evil meta
and audit maintenance logic.

The goal is to show that:

* Open Agentic 2.0 remains consistent over many runs.
* Evidence thresholds are enforced (some runs have `done: 3`, some `done: 2`).
* Audit-chain integrity is maintained, and `maintain_audits.py` can still repair
  and quarantine corrupted audits if needed.

### 7.1 Batch of healthy runs (`done: 3`)

Terminal 1 – start healthy meta:

```bash
cd ~/open-agentic
source .venv/bin/activate
python meta_stub.py
# Meta stub listening on http://127.0.0.1:8081
```

Terminal 2 – run Open Agentic 2.0 multiple times:

```bash
cd ~/open-agentic
source .venv/bin/activate

for i in 1 2 3; do
  echo "Run $i (healthy meta)..."
  python agentic2_micro_plugin.py \
    --plan plan.json \
    --policy policy.yaml \
    --plugins plugins.yaml \
    --min_coverage 0.75 \
    --min_sources 2 \
    --bundle
done
```

Expected:

* Each run prints JSON with `done: 3` and `status: "OK"`.
* Several new `audit_*.jsonl` and `bundle_*.json` files are created.

### 7.2 Batch of adversarial runs (`done: 2`)

Stop the healthy meta (`Ctrl+C` in Terminal 1), then start the low-evidence meta:

```bash
cd ~/open-agentic
source .venv/bin/activate
python evil_meta_low_evidence.py
# Evil meta (low evidence) listening on http://127.0.0.1:8081
```

In Terminal 2, run another batch:

```bash
cd ~/open-agentic
source .venv/bin/activate

for i in 1 2 3; do
  echo "Run $i (evil meta)..."
  python agentic2_micro_plugin.py \
    --plan plan.json \
    --policy policy.yaml \
    --plugins plugins.yaml \
    --min_coverage 0.75 \
    --min_sources 2 \
    --bundle
done
```

Expected:

* Some runs show `done: 2` and `status: "OK"`.
* The plan in the corresponding `bundle_*.json` still contains three tasks (`legacy`, `meta`, `summarize`), but only two are fully accepted according to the policy/evidence thresholds.

You can inspect the latest bundle:

```bash
python - <<'PY'
import json, pathlib

root = pathlib.Path(".")
bundles = sorted(
    root.glob("bundle_*.json"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if not bundles:
    raise SystemExit("No bundle_*.json found")

f = bundles[0]
print("Inspecting bundle:", f)
data = json.loads(f.read_text())
print(json.dumps(data, indent=2))
PY
```

This shows that the plan is stable, while the effective `done` count depends on whether
the meta-agent evidence satisfies the thresholds.

### 7.3 Audit-chain validation after swarm runs

After both the healthy and adversarial batches:

```bash
cd ~/open-agentic
source .venv/bin/activate

pytest -q tests/test_audit_chain_all.py -vv
```

Expected:

* If no manual tampering was done, the test should pass.
* If any audit file was corrupted (for example during separate tamper tests), the test
  will fail and report which `audit_*.jsonl` has a broken chain.

To repair and quarantine corrupted audits:

```bash
cd ~/open-agentic
source .venv/bin/activate

python maintain_audits.py
pytest -q tests/test_audit_chain_all.py -vv
```

Expected:

* All `audit_*.jsonl` files in the repository root have valid chains again.
* Any corrupted audits were moved to `audit_corrupted/` with a corresponding `_salvaged`
  version remaining in the root.















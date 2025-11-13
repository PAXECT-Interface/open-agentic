"""
End-to-end style tests for the Agentic 2.0 micro orchestrator.

These tests use the real plan.json and policy.yaml files to make sure
the core wiring behaves as documented in the README.
"""

from __future__ import annotations

import json
import pathlib

from agentic2_micro_plugin import (
    Audit,
    Orchestrator,
    Policy,
    Verifier,
    _load_plan,
    _load_policy,
    main,
)


def test_orchestrator_with_plan_and_policy(tmp_path):
    """
    Load policy.yaml and plan.json and run the orchestrator once.

    The demo plan contains three steps:
      1) legacy (unknown tool if plugins are not loaded)
      2) meta   (unknown tool if plugins are not loaded)
      3) summarize (local tool, should succeed)

    Even without plugins loaded, the summarize step should execute,
    so we expect status == "OK" and done == 1.
    """
    policy, policy_meta = _load_policy("policy.yaml")
    plan = _load_plan("plan.json")

    audit_path = tmp_path / "audit.jsonl"
    audit = Audit(path=str(audit_path))
    verifier = Verifier(require_evidence=True, min_coverage=0.75, min_sources=2)

    orch = Orchestrator(policy, verifier, audit, run_meta=policy_meta)
    res = orch.run(plan)

    assert res["status"] == "OK"
    assert res["done"] == 1

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert Audit.validate_chain(lines, key_hex=None) is True


def test_main_dry_run_does_not_execute_tools(capsys):
    """
    Running the CLI with --dry-run should validate plan and policy
    and then exit without executing any tools.
    """
    main(["--plan", "plan.json", "--policy", "policy.yaml", "--dry-run"])

    captured = capsys.readouterr()
    out = captured.out.strip()
    data = json.loads(out)

    assert data["status"] == "NOOP"
    assert data["done"] == 0
    assert "trace" in data
    assert "audit_file" in data

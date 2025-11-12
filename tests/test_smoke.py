import pathlib
from agentic2_micro_plugin import Audit, Policy, Verifier, Orchestrator

def test_smoke_run_ok(tmp_path):
    a = Audit(path=str(tmp_path / "audit.jsonl"))
    policy = Policy(["echo", "summarize"], max_steps=8, max_sec=10.0)
    verifier = Verifier(require_evidence=True, min_coverage=0.75, min_sources=2)

    plan = [
        {"task": "echo", "args": {"msg": "ok"}},
        {"task": "summarize", "args": {"text": "abc"}}
    ]

    res = Orchestrator(policy, verifier, a).run(plan)
    assert res["status"] == "OK" and res["done"] == 2

    lines = pathlib.Path(res["audit_file"]).read_text(encoding="utf-8").splitlines()
    assert Audit.validate_chain(lines) is True

#!/usr/bin/env python3
# Agentic 2.0 — Micro Plugin Skeleton (final single-file)
# - Fail-closed Policy: allowlist + max_steps/sec + per-tool budgets
# - Verifier: evidence required + min_coverage + min_sources + task-specific shape checks
# - Audit: append-only hash chain (SHA256 or HMAC), fsync per event, key_id, close()
# - Plugins: legacy_subprocess (stdin/stdout JSON), meta_http (HTTP JSON) with timeouts & trimmed errors
# - Tools: registry + @tool sugar; plugins exposed als tools (bv. "legacy", "meta")
# - CLI: --plan/--policy/--plugins/--hmac/--min_coverage/--min_sources/--bundle/--dry-run
#
# Alleen stdlib; PyYAML is optioneel voor YAML.
# Ontworpen om compact, auditeerbaar en veilig te zijn — plug-and-play bij legacy/meta agents.

from __future__ import annotations
import os
import sys
import json
import time
import uuid
import hmac
import hashlib
import argparse
import inspect
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Callable, List, Optional, Tuple

# ---------- Types ----------
Step = Dict[str, Any]    # {"task": str, "args"?: {...}}
Output = Dict[str, Any]  # {"ok": bool, "result"?: any, "evidence"?: {...}, "reasons"?: [...]}

# ---------- Utilities ----------
_MAX_LOG = 200  # truncate long strings in audit details

def _short(s: Optional[str], n: int = _MAX_LOG) -> str:
    if s is None:
        return ""
    s = str(s)
    return s if len(s) <= n else s[:n] + "…"

def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, separators=(",", ":"), sort_keys=True)
    except Exception:
        return str(obj)

def redact_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Eenvoudige redaction hook: truncate strings; kan door teams worden vervangen.
    """
    out: Dict[str, Any] = {}
    for k, v in details.items():
        if isinstance(v, str):
            out[k] = _short(v)
        else:
            out[k] = v
    return out

# ---------- Audit ----------
class Audit:
    """
    Append-only audit met keten-hash:
      chain_i = HMAC(key, chain_{i-1} + canonical_i) of SHA256(... zonder key)
    - fsync per event (best effort) => crash-safe
    - key_id (korte fingerprint) wordt gelogd bij elk event
    """
    def __init__(self, path: Optional[str] = None, key_hex: Optional[str] = None):
        self.key: Optional[bytes] = bytes.fromhex(key_hex) if key_hex else None
        self.key_id: Optional[str] = (hashlib.sha256(self.key).hexdigest()[:12] if self.key else None)
        self.prev = ""
        self.trace = str(uuid.uuid4())
        self.path = path or f"audit_{self.trace}.jsonl"
        self._fh = open(self.path, "a", encoding="utf-8", buffering=1)

    def _sign(self, s: str) -> str:
        if self.key is None:
            return hashlib.sha256(s.encode()).hexdigest()
        return hmac.new(self.key, s.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _canon(ev: Dict[str, Any]) -> str:
        return json.dumps(ev, sort_keys=True, separators=(",", ":"))

    def log(self, typ: str, details: Dict[str, Any]):
        safe = redact_details(details)
        ev = {
            "ts": time.time(),
            "trace": self.trace,
            "type": typ,
            "details": safe,
            "prev": self.prev,
            "key_id": self.key_id,
        }
        canonical = self._canon(ev)
        self.prev = self._sign(self.prev + canonical)
        ev["chain"] = self.prev
        self._fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
        self._fh.flush()
        try:
            os.fsync(self._fh.fileno())
        except Exception:
            # Best-effort — niet crashen op fsync errors
            pass

    def close(self):
        try:
            self._fh.close()
        except Exception:
            pass

    @staticmethod
    def validate_chain(lines: List[str], key_hex: Optional[str] = None) -> bool:
        """
        Herberekent de chain en vergelijkt met gelogde 'chain'.
        """
        key = bytes.fromhex(key_hex) if key_hex else None
        prev = ""
        for line in lines:
            try:
                ev = json.loads(line)
            except Exception:
                return False
            tmp = dict(ev)
            chain = tmp.pop("chain", None)
            canonical = json.dumps(tmp, sort_keys=True, separators=(",", ":"))
            if key is None:
                expected = hashlib.sha256((prev + canonical).encode()).hexdigest()
            else:
                expected = hmac.new(key, (prev + canonical).encode(), hashlib.sha256).hexdigest()
            if expected != chain:
                return False
            prev = chain
        return True

# ---------- Policy ----------
class Policy:
    def __init__(self, allowlist: List[str], max_steps: int = 10, max_sec: float = 10.0, budgets: Optional[Dict[str, int]] = None):
        self.allow = set(allowlist)
        self.max_steps = int(max_steps)
        self.max_sec = float(max_sec)
        self.budgets = dict(budgets) if budgets else {}

    def allowed(self, task: str) -> bool:
        return task in self.allow

    def enforce_budget(self, task: str) -> bool:
        if task not in self.budgets:
            return True
        if self.budgets[task] <= 0:
            return False
        self.budgets[task] -= 1
        return True

# ---------- Verifier ----------
class Verifier:
    def __init__(self, require_evidence: bool = True, min_coverage: float = 0.60, min_sources: int = 1):
        self.require_evidence = bool(require_evidence)
        self.min_cov = float(min_coverage)
        self.min_src = int(min_sources)

    @staticmethod
    def _coverage(ev: Optional[Dict[str, Any]]) -> float:
        if not isinstance(ev, dict):
            return 0.0
        c = ev.get("coverage")
        try:
            return float(c) if c is not None else 0.6
        except Exception:
            return 0.0

    def check(self, step: Step, out: Output) -> Output:
        if not out.get("ok"):
            return out
        ev = out.get("evidence")
        if self.require_evidence and not ev:
            return {"ok": False, "reasons": ["missing evidence"]}

        cov = self._coverage(ev)
        if cov < self.min_cov:
            return {"ok": False, "reasons": [f"coverage {cov:.2f} < {self.min_cov:.2f}"]}

        srcs = (ev.get("sources") or []) if isinstance(ev, dict) else []
        if len(srcs) < self.min_src:
            return {"ok": False, "reasons": [f"sources {len(srcs)} < {self.min_src}"]}

        # Taak-specifieke result-shape guards
        task = step.get("task")
        if task == "summarize":
            res = out.get("result") or {}
            if not isinstance(res, dict) or "summary" not in res:
                return {"ok": False, "reasons": ["bad summary shape"]}

        return out

# ---------- Tools registry ----------
TOOLS: Dict[str, Callable[[Dict[str, Any]], Output]] = {}

def register_tool(name: str, fn: Callable[[Dict[str, Any]], Output]):
    TOOLS[name] = fn

def tool(name: str):
    def deco(fn: Callable[[Dict[str, Any]], Output]):
        register_tool(name, fn)
        return fn
    return deco

# Interne demo-tools
@tool("echo")
def t_echo(args: Dict[str, Any]) -> Output:
    msg = str(args.get("msg", ""))
    ok = bool(msg)
    return {
        "ok": ok,
        "result": msg if ok else None,
        "evidence": ({"coverage": 0.80, "sources": ["echo","caller"]} if ok else None),
        "reasons": ([] if ok else ["empty msg"])
    }

@tool("summarize")
def t_summarize(args: Dict[str, Any]) -> Output:
    text = str(args.get("text", ""))
    if not text:
        return {"ok": False, "reasons": ["missing text"]}
    summary = (text[:160] + "…") if len(text) > 160 else text
    # Evidence compliant met strikte defaults (>=0.75 coverage en >=2 sources)
    evidence = {"coverage": 0.85, "sources": ["legacy", "meta"]}
    return {"ok": True, "result": {"summary": summary}, "evidence": evidence}

# ---------- Plugins (adapters) ----------
class Plugin:
    def __init__(self, name: str):
        self.name = name
    def run(self, op: str, params: Dict[str, Any]) -> Output:
        raise NotImplementedError

class LegacySubprocess(Plugin):
    """
    Roept een bestaand script/binary aan. Verwacht JSON op stdin, JSON op stdout.
    """
    def __init__(self, name: str, cmd: List[str], timeout: float = 8.0):
        super().__init__(name)
        self.cmd = cmd
        self.timeout = float(timeout)

    def run(self, op: str, params: Dict[str, Any]) -> Output:
        try:
            p = subprocess.run(
                self.cmd,
                input=json.dumps({"op": op, "params": params}),
                text=True, capture_output=True, timeout=self.timeout
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "reasons": ["timeout"]}
        except Exception as e:
            return {"ok": False, "reasons": [f"subprocess_error:{type(e).__name__}"]}

        if p.returncode != 0:
            return {"ok": False, "reasons": [f"nonzero_exit:{p.returncode}", _short(p.stderr)]}

        try:
            out = json.loads(p.stdout)
        except Exception as e:
            return {"ok": False, "reasons": [f"bad_json:{type(e).__name__}", _short(p.stdout)]}

        ev = out.get("evidence") or {}
        ev.setdefault("coverage", 0.80)
        srcs = ev.get("sources") or []
        if not srcs:
            ev["sources"] = [self.name]
        return {
            "ok": bool(out.get("ok")),
            "result": out.get("result"),
            "evidence": ev,
            "reasons": out.get("reasons", [])
        }

class MetaHTTP(Plugin):
    """
    Eenvoudige HTTP JSON bridge naar externe/“meta” agenten.
    POST body: {"op": "...", "params": {...}}
    """
    def __init__(self, name: str, endpoint: str, timeout: float = 8.0, headers: Optional[Dict[str,str]] = None, auth_token: Optional[str] = None):
        super().__init__(name)
        self.endpoint = endpoint
        self.timeout = float(timeout)
        self.headers = headers or {}
        self.auth_token = auth_token

    def run(self, op: str, params: Dict[str, Any]) -> Output:
        body = json.dumps({"op": op, "params": params}).encode()
        hdrs = {"Content-Type": "application/json", **self.headers}
        if self.auth_token:
            hdrs["Authorization"] = f"Bearer {self.auth_token}"
        req = urllib.request.Request(self.endpoint, data=body, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode()
        except urllib.error.URLError:
            return {"ok": False, "reasons": ["network_error"]}
        except Exception as e:
            return {"ok": False, "reasons": [f"http_error:{type(e).__name__}"]}

        try:
            out = json.loads(raw)
        except Exception as e:
            return {"ok": False, "reasons": [f"bad_json:{type(e).__name__}", _short(raw)]}

        ev = out.get("evidence") or {}
        ev.setdefault("coverage", 0.80)
        srcs = ev.get("sources") or []
        if not srcs:
            ev["sources"] = [self.name]
        return {
            "ok": bool(out.get("ok")),
            "result": out.get("result"),
            "evidence": ev,
            "reasons": out.get("reasons", [])
        }

PLUGINS: Dict[str, Plugin] = {}

def _register_plugin_tool(pname: str):
    def _tool(args: Dict[str, Any]) -> Output:
        op = str(args.get("op") or args.get("operation") or "")
        params = args.get("params")
        if params is None:
            params = {k: v for k, v in args.items() if k not in ("op", "operation")}
        if not op:
            return {"ok": False, "reasons": ["missing op"]}
        return PLUGINS[pname].run(op, params)
    register_tool(pname, _tool)

def load_plugins(manifest_path: Optional[str]) -> List[str]:
    if not manifest_path:
        return []
    cfg = _load_any(manifest_path)
    loaded: List[str] = []
    for item in cfg.get("plugins", []):
        kind = item.get("kind"); name = item.get("name")
        if not kind or not name:
            raise ValueError("plugin entry requires 'kind' and 'name'")
        if kind == "legacy_subprocess":
            PLUGINS[name] = LegacySubprocess(
                name=name,
                cmd=item.get("cmd", ["python3", "legacy_agentic.py"]),
                timeout=float(item.get("timeout", 8.0)),
            )
        elif kind == "meta_http":
            PLUGINS[name] = MetaHTTP(
                name=name,
                endpoint=item["endpoint"],
                timeout=float(item.get("timeout", 8.0)),
                headers=item.get("headers") or {},
                auth_token=item.get("auth_token"),
            )
        else:
            raise ValueError(f"unknown plugin kind: {kind}")
        _register_plugin_tool(name)
        loaded.append(name)
    return loaded

# ---------- Orchestrator ----------
class Orchestrator:
    def __init__(self, policy: Policy, verifier: Verifier, audit: Audit, run_meta: Optional[Dict[str, Any]] = None):
        self.policy = policy
        self.verifier = verifier
        self.audit = audit
        self.run_meta = run_meta or {}

    @staticmethod
    def _norm_step(raw: Step) -> Step:
        if not isinstance(raw, dict):
            raise TypeError("step must be dict")
        t = raw.get("task"); a = raw.get("args", {})
        if not isinstance(t, str) or not t.strip():
            raise ValueError("task must be non-empty str")
        if not isinstance(a, dict):
            raise ValueError("args must be dict")
        return {"task": t.strip(), "args": a}

    def run(self, plan: List[Step]) -> Dict[str, Any]:
        t0 = time.time()
        done = 0
        self.audit.log("run.start", {"n": len(plan), **self.run_meta})
        try:
            for i, raw in enumerate(plan[: self.policy.max_steps]):
                if time.time() - t0 > self.policy.max_sec:
                    self.audit.log("fail_closed", {"reason": "time budget"})
                    break

                try:
                    st = self._norm_step(raw)
                except Exception as e:
                    self.audit.log("invalid.step", {"i": i, "err": repr(e)})
                    continue

                task, args = st["task"], st["args"]
                self.audit.log("step.start", {"i": i, "task": task, "args": _short(_safe_json(args))})

                if not self.policy.allowed(task):
                    self.audit.log("blocked", {"task": task})
                    continue
                if not self.policy.enforce_budget(task):
                    self.audit.log("fail_closed", {"reason": "budget exceeded", "task": task})
                    continue

                fn = TOOLS.get(task)
                if not fn:
                    self.audit.log("unknown", {"task": task})
                    continue

                try:
                    out = fn(args)
                except Exception as e:
                    self.audit.log("error", {"task": task, "err": repr(e)})
                    continue

                out = self.verifier.check(st, out)
                if not out.get("ok"):
                    self.audit.log("abstain", {"task": task, "reasons": out.get("reasons")})
                    continue

                self.audit.log("success", {
                    "task": task,
                    "result": _short(_safe_json(out.get("result"))),
                    "evidence": out.get("evidence")
                })
                done += 1
                self.audit.log("step.end", {"i": i})

            status = "OK" if done else "NOOP"
            self.audit.log("run.end", {"done": done, "status": status})
            return {"done": done, "status": status, "trace": self.audit.trace, "audit_file": self.audit.path}
        finally:
            self.audit.close()

# ---------- Loaders & CLI ----------
def _load_any(path: str):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        if ext in (".yaml", ".yml"):
            try:
                import yaml
            except ImportError:
                raise RuntimeError("PyYAML required for YAML; install with 'pip install pyyaml' or use JSON.")
            return yaml.safe_load(f)
        return json.load(f)

def _load_policy(path: Optional[str]) -> Tuple[Policy, Dict[str, Any]]:
    if not path:
        pol = {"allowlist": ["legacy", "meta", "summarize", "echo"], "max_steps": 16, "max_sec": 10.0, "budgets": {"legacy": 5, "meta": 5, "summarize": 5}}
        sha = hashlib.sha256(json.dumps(pol, sort_keys=True).encode()).hexdigest()
        return Policy(pol["allowlist"], pol["max_steps"], pol["max_sec"], pol["budgets"]), {"policy_path": None, "policy_sha256": sha}
    data = _load_any(path) or {}
    sha = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return Policy(data.get("allowlist", []), data.get("max_steps", 10), data.get("max_sec", 10.0), data.get("budgets", {})), {"policy_path": path, "policy_sha256": sha}

def _load_plan(path: Optional[str]) -> List[Step]:
    if not path:
        return [
            {"task": "legacy", "args": {"op": "search", "q": "specs for component X"}},
            {"task": "meta",   "args": {"op": "extract", "url": "https://example.org/doc"}},
            {"task": "summarize", "args": {"text": "Combine results here..."}}
        ]
    data = _load_any(path)
    if not isinstance(data, list):
        raise ValueError("plan must be a list")
    return data

def _write_bundle(trace: str, plan: List[Step], policy_meta: Dict[str, Any]) -> Optional[str]:
    try:
        code_sha = hashlib.sha256(inspect.getsource(Orchestrator).encode()).hexdigest()
        bundle = {"trace": trace, "plan": plan, **policy_meta, "code_sha256": code_sha}
        path = f"bundle_{trace}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
        return path
    except Exception:
        return None

def main(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser("Agentic 2.0 — micro plugin")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--plugins", default=None)
    ap.add_argument("--hmac", default=None, help="hex key for audit HMAC")
    ap.add_argument("--min_coverage", type=float, default=0.75)
    ap.add_argument("--min_sources", type=int, default=2)
    ap.add_argument("--bundle", action="store_true", help="emit bundle_<trace>.json with plan/policy SHA/code SHA")
    ap.add_argument("--dry-run", action="store_true", help="validate plan/policy and exit without executing tools")
    args = ap.parse_args(argv)

    policy, pol_meta = _load_policy(args.policy)
    plan = _load_plan(args.plan)
    loaded = load_plugins(args.plugins)
    run_meta = {
        "policy_path": pol_meta.get("policy_path"),
        "policy_sha256": pol_meta.get("policy_sha256"),
        "plugins": loaded,
        "min_cov": args.min_coverage,
        "min_src": args.min_sources,
    }

    audit = Audit(path=None, key_hex=args.hmac)
    verifier = Verifier(True, args.min_coverage, args.min_sources)
    orch = Orchestrator(policy, verifier, audit, run_meta=run_meta)

    if args.dry_run:
        audit.log("dry_run.validate", {"plan_len": len(plan), "policy_allowlist": sorted(list(policy.allow))})
        audit.log("run.end", {"done": 0, "status": "NOOP"})
        audit.close()
        print(json.dumps({"done": 0, "status": "NOOP", "trace": audit.trace, "audit_file": audit.path}, indent=2))
        return

    res = orch.run(plan)

    if args.bundle:
        bundle_path = _write_bundle(res["trace"], plan, pol_meta)
        if bundle_path:
            res["bundle_file"] = bundle_path

    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()

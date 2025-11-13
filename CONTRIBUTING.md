

---

# Contributing to Open Agentic

Thanks for your interest in contributing! We welcome bug fixes, new features, tests, examples, and documentation.

> By participating, you agree that your contributions are licensed under the project’s **Apache-2.0** license.

## Quick Start (PR checklist)

1. **Fork** this repository on GitHub and **clone** your fork locally:

   ```bash
   git clone https://github.com/<your-user>/open-agentic.git
   cd open-agentic
   git remote add upstream https://github.com/PAXECT-Interface/open-agentic.git
   ```
2. **Create a branch** for your change:

   ```bash
   git checkout -b feat/my-change
   ```
3. **Set up dev environment** (PyYAML is optional, only if you use YAML configs):

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -U pip
   pip install pytest pyyaml
   ```
4. **Run tests** locally (they should pass before you open a PR):

   ```bash
   pytest -q -vv
   ```
5. **Commit** with a clear message and push:

   ```bash
   git add -A
   git commit -m "feat: concise summary of change"
   git push origin feat/my-change
   ```
6. **Open a Pull Request** against `main`:

   * Describe the problem and solution.
   * Add screenshots or sample output if useful.
   * Note breaking changes and docs/tests you updated.

## Development Guidelines

* **Stdlib-first & minimal surface.** Prefer the standard library; keep dependencies small (PyYAML is optional).
* **Fail-closed semantics.** Don’t bypass the verifier, policy allowlist, or budgets. If in doubt, *abstain*.
* **Determinism & auditability.** Preserve output shapes; keep logs and audit chains reproducible.
* **Small PRs.** Focused changes are easier to review and revert if needed.
* **Tests.** Add or update tests for any user-visible change (new tool, plugin, or verifier rule).

## Testing

* Run the full test suite:

  ```bash
  pytest -q -vv
  ```
* Audit integrity tests:

  ```bash
  python -m pytest -q tests/test_audit_chain_all.py -vv
  ```

  If HMAC keys are missing, tests will **skip** those audits. Use:

  ```bash
  python tools/list_key_ids.py
  # optionally create placeholder key files
  python tools/list_key_ids.py --emit-placeholders
  ```

## Commit & PR Conventions

* **Conventional commit** style is encouraged:

  * `feat: …`, `fix: …`, `docs: …`, `test: …`, `refactor: …`, `chore: …`
* One logical change per PR; include migration notes for breaking changes.
* Update **README/FAQ** if you change CLI flags, config formats, or default behavior.

## Security & Keys

* **Never commit secrets.** `keys/` is git-ignored; keep it that way.
* Prefer **ephemeral keys** for local runs; distribute production keys out-of-band.
* If you suspect a security issue, open a private channel (do **not** file a public issue with details). You can file a minimal issue pointing to a “security contact requested”.

## Adding Tools / Plugins

* **Tools** must return:

  ```python
  {
    "ok": bool,
    "result": ...,
    "evidence": {"coverage": float, "sources": [..]},
    "reasons": [...]
  }
  ```
* **Plugins** (e.g., `legacy_subprocess`, `meta_http`) must enforce strict timeouts and return minimal JSON with evidence.
* The **verifier** will reject outputs missing evidence, below thresholds, or with wrong shapes.

## Style

* Python 3.10+.
* Keep modules small and well-commented; prioritize clarity over cleverness.
* Avoid global state; pass configuration explicitly (`--plan`, `--policy`, `--plugins`, etc.).

## Issue Reporting

When filing an issue, include:

* **Environment** (OS, Python version)
* **Steps to reproduce** (minimal plan/policy/plugins, if possible)
* **Expected vs actual behavior**
* **Logs** or **audit excerpts** (scrub secrets; do not share real keys)

### Community & contributors

Open Agentic 2.0 is intentionally open and community-driven.

If you’d like to help:

- open an issue or discussion with ideas or questions,
- pick up an issue labeled `good first issue` or `help wanted`,
- improve docs, examples, or tests,
- or try the framework in your own projects and share feedback.

If you’re interested in becoming a regular contributor or maintainer, start a
Discussion and introduce yourself – the goal is for Open Agentic 2.0 to grow
with a healthy, transparent community around it.


## License

By contributing, you agree your contributions are licensed under the project’s **Apache License, Version 2.0** (see `LICENSE`).

---

*Thank you for helping make Open Agentic better and more reliable for everyone!*


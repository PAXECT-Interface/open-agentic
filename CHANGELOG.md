# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2025-11-12
### Added
- Initial public preview of **Open Agentic 2.0**.
- Fail-closed orchestrator with policy allowlist, budgets, and time limits.
- Cryptographic audit chain (SHA-256 or HMAC) with per-event fsync.
- Verifier: evidence required + `min_coverage` / `min_sources` + shape checks.
- Plugin adapters: `legacy_subprocess` (stdin/stdout JSON) & `meta_http` (POST JSON).
- Pytest suite: functional + audit-chain validation; key utilities & reports.
- `tools/list_key_ids.py` for key ID inventory and placeholder generation.

### Notes
- API surface is intentionally small; minor breaking changes may occur before 1.0.

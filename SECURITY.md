# Security Policy for Open Agentic 2.0

Open Agentic 2.0 is an audit-first, fail-closed framework.  
We take security and integrity seriously and welcome responsible disclosure.

## Supported versions

This project is still in **Public Preview (v0.x)**.  
Security issues are still important, but the API surface may change.

| Version | Supported |
|--------|-----------|
| 0.x    | ✅ Yes    |
| < 0.x  | ❌ No     |

When in doubt, always report – we prefer one report too many over one too few.

## How to report a vulnerability

If you think you found a security or integrity issue (for example):

- audit chains that can be forged or broken without detection,
- ways to bypass fail-closed behaviour or the policy/verifier,
- leakage of sensitive data in logs, audits, or error messages,
- unsafe defaults in `plan.json`, `policy.yaml`, or `plugins.yaml`,

**please do not open a public Issue immediately.**  
Instead:

1. Use GitHub’s private **“Report a vulnerability”** flow if available, or  
2. Contact the maintainer privately (for now):  
   - GitHub profile: [`PAXECT-Interface`](https://github.com/PAXECT-Interface)  
   - Or open a short Issue titled _"Potential security issue (request for private contact)"_ without technical details.

We will:

- acknowledge your report as quickly as we reasonably can,
- discuss impact and possible fixes with you,
- prepare a fix and coordinate a disclosure timeline if the issue is valid.

## Non-security issues

Please use **GitHub Issues** (bug, enhancement, docs) for:

- crashes without security impact,
- CI failures,
- documentation problems,
- feature requests.

These are important, but they are not treated as security vulnerabilities.

## Keys and secrets

Open Agentic 2.0 is designed so that **real HMAC keys and secrets should never
be committed to the repository**.

- Do not open pull requests that include real keys, tokens, or secrets.
- If you accidentally commit a secret, rotate it immediately and open an Issue
  asking for help cleaning up the history if needed.

## Thanks

Responsible disclosure helps keep the whole community safe.  
Thank you for taking the time to report issues instead of exploiting them.

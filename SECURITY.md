# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| Latest (`main`) | ✅ |

We maintain security fixes on the `main` branch only. Please make sure you are running the latest version before reporting a vulnerability.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report them privately:

1. Go to the repository's [Security Advisories](https://github.com/radheshpai87/checkDK/security/advisories/new) page and click **"Report a vulnerability"**
2. Or email the maintainer directly via the contact listed on the GitHub profile

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept (if safe to share)
- Affected component (backend, frontend, CLI, Docker config, etc.)
- Any suggested fix if you have one

---

## What to Expect

- **Acknowledgement** within 48 hours
- **Assessment** (severity, scope, fix timeline) within 5 business days
- **Fix + coordinated disclosure** — we'll notify you before publishing a public advisory
- Credit in the release notes if you'd like it

---

## Scope

Things we consider in scope:

- Authentication bypass or JWT forgery
- OAuth token leakage or callback URL manipulation
- Server-side code execution via uploaded config files
- Privilege escalation via API endpoints
- Secrets or credentials exposed in logs, responses, or source code

Out of scope:

- Vulnerabilities in third-party dependencies that have no available fix yet
- Rate limiting / denial-of-service on the demo deployment
- Issues requiring physical access to a machine

---

## Disclosure Policy

We follow [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure). We ask that you give us reasonable time to patch before public disclosure.

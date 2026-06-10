# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.x (current) | Yes |

## Reporting a vulnerability

Do not open a public GitHub issue for security vulnerabilities.

Email: security@groovexlabs.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected component (API, database layer, auth, evidence hashing)
- Potential impact

Response within 72 hours. If a valid vulnerability is confirmed, a fix will be issued before public disclosure. Credit given unless anonymity is requested.

## Security design principles

These apply to every line of code in this repository:

1. **Never trust input** — validate at every layer boundary, not just the API edge
2. **Privacy by design** — collect only what is legally required, retain only as long as required
3. **Least privilege** — each role can only access what its function requires; nothing more
4. **Secure by default** — the default configuration is the hardened configuration
5. **Defense in depth** — each layer is hardened assuming the layer above it is compromised
6. **Fail-safe** — on any error involving evidence or audit data, fail closed, not open

## What is in scope

- Evidence integrity (hashing, signing, tamper detection)
- Chain of custody (append-only guarantees, signature verification)
- Authentication and session management
- Audit log integrity
- API input validation and injection prevention
- Role-based access control enforcement

## What is out of scope

- The underlying operating system
- Docker runtime vulnerabilities
- The PostgreSQL engine itself (report to PostgreSQL security team)

## Dependency scanning

Every pull request is scanned by:
- `bandit` — Python static analysis for security issues
- `pip-audit` — known CVE check on all dependencies
- GrooveGuard — MCP server and API surface scan

## Evidence of security review

All changes to `forenchain/security/` require review from at least one maintainer before merge.
Changes to evidence hashing or audit log code require explicit sign-off with a comment explaining why the change does not break integrity guarantees.

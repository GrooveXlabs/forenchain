# ForenChain

Open forensic evidence chain-of-custody platform for Indian state agencies.

---

## The problem

Haryana's FSL operates on Trakea — a barcoded, biometrically authenticated evidence tracking system that the Punjab and Haryana High Court has formally endorsed for district courts. Punjab's FSL, SSOC, and CDAC Chandigarh have no equivalent. Evidence custody is tracked manually. Forensic reports reach courts late, incomplete, or impossible to verify.

ForenChain is the open answer to that gap.

---

## What it does

- Generates QR-coded, SHA-256 hashed evidence records at the point of collection
- Maintains a cryptographically signed, append-only chain of custody
- Tracks forensic report status from FSL submission through court delivery
- Provides a read-only court portal for real-time case and report tracking
- Logs every system action in a tamper-evident, immutable audit trail
- On-premise deployable — no external cloud dependency for sensitive state data

---

## Compliance

| Standard | Coverage |
|----------|---------|
| IT Act 2000 (Section 65B) | Electronic evidence integrity and admissibility |
| DPDP Act 2023 | Data minimisation, purpose limitation, right to erasure exceptions for evidence |
| CERT-In security guidelines | API hardening, incident response, log retention |
| STQC certification | Roadmap in `docs/compliance/stqc-roadmap.md` |

---

## Stack

| Layer | Tech | Reason |
|-------|------|--------|
| API | FastAPI (Python 3.11+) | Async, auto-documented, typed end-to-end |
| Database | PostgreSQL + pgaudit | Audit extension built-in, row-level security native |
| Evidence integrity | SHA-256 + HMAC-SHA256 | Tamper detection, content verification |
| Auth | JWT + TOTP (MFA) | Standard, auditable, no vendor dependency |
| Frontend | React 18 + TypeScript | Court portal and officer dashboard |
| Deployment | Docker Compose | On-premise or cloud, no lock-in |

---

## Security posture

Evidence integrity is a legal requirement, not a product feature. The entire system is built around that single constraint.

- Input validated at every layer boundary — no unvalidated data moves between components
- Evidence hashes computed server-side only — client values are never trusted
- Chain of custody is append-only — no transfer record is ever modified or deleted
- Every action is written to an immutable audit log before the action executes
- MFA required for FSL officers and all users with write access
- Secrets are environment-injected, never in code — scanned on every commit via GrooveGuard
- Defense in depth: each layer is hardened assuming every layer above it can fail

---

## Development — TDD first

Tests are written before the code they test. This is not optional.

```bash
git clone https://github.com/groovexlabs/forenchain
cd forenchain
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

pip install -e ".[dev]"
make test
```

```bash
make test            # full test suite with coverage
make test-security   # bandit static analysis + dependency safety check
make lint            # ruff + mypy strict mode
make all             # lint + security + tests in sequence
```

Coverage minimum: **90%**. CI blocks merge below this threshold.

---

## Roles

| Role | Can Do |
|------|--------|
| Investigator | Create evidence records, initiate custody transfers |
| FSL Officer | Receive evidence, submit forensic reports, update report status |
| Court | Read-only — case status, report availability, custody chain |
| Admin | User management, audit log review, system configuration |

---

## Deployment — on-premise

Designed to run entirely within a state agency's network perimeter:

```bash
cp .env.example .env
# fill in database credentials and secret keys
docker compose up -d
```

No outbound internet required after the initial image pull. Full guide: `docs/deployment/on-premise.md`.

---

## Part of the GrooveXlabs ecosystem

ForenChain integrates with:

- **GrooveGuard** — scans ForenChain's own MCP endpoints for security regressions on every commit
- **ThreatHound** — feeds ForenChain audit logs into the SOC for anomaly detection
- **PurpleForge** — maps ForenChain attack surface to defensive controls

---

Built in Mohali, Punjab.
ForenChain is auditable by design. Agencies using it can read every line of code that handles their evidence.

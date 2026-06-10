# ForenChain — Architecture Reference

## Design Philosophy

ForenChain is built around one non-negotiable constraint: **evidence integrity is a legal requirement, not a feature.** Every architectural decision follows from that.

Three properties must hold at all times:
1. No evidence record can be modified after creation
2. No custody transfer can be deleted
3. Every action has an audit record that predates the action

If any of these three properties can be violated — even by a database administrator, even by the application itself — the system cannot be trusted in court.

---

## Layer Structure

```
┌──────────────────────────────────────────────────────┐
│  INFRASTRUCTURE  (FastAPI, SQLAlchemy, JWT, QR, PDF) │
│  Knows about: HTTP, SQL, files, tokens               │
│  Does NOT know about: domain rules                   │
├──────────────────────────────────────────────────────┤
│  APPLICATION  (Use Cases, Repository ABCs)           │
│  Knows about: domain models, port interfaces         │
│  Does NOT know about: HTTP, specific DB engine       │
├──────────────────────────────────────────────────────┤
│  DOMAIN  (Pydantic models, hashing, signing)         │
│  Knows about: nothing external. Pure Python, no I/O. │
└──────────────────────────────────────────────────────┘
```

### Hard Boundary Rules

- `forenchain/domain/` has zero imports from FastAPI, SQLAlchemy, or any networking library. It must be testable with no database and no HTTP server.
- `forenchain/application/` imports from domain and from port ABCs. It never imports a concrete repository implementation or a FastAPI type.
- `forenchain/infrastructure/` is the only layer that imports FastAPI, SQLAlchemy, passlib, pyotp, and qrcode.

**Why these rules matter:** A government technical reviewer can audit `forenchain/domain/` in isolation and verify the business rules without understanding the infrastructure. The 45 domain tests prove the rules hold without running a server.

---

## File Structure

```
forenchain/
├── domain/
│   ├── models/
│   │   ├── evidence.py       — Evidence, EvidenceCreateRequest (immutable, frozen)
│   │   ├── custody.py        — CustodyTransfer, CustodyTransferRequest (append-only)
│   │   ├── audit.py          — AuditLog, AuditAction (immutable, append-only)
│   │   ├── user.py           — User, UserRole, value objects
│   │   └── report.py         — ForensicReport, ReportStatus
│   └── security/
│       └── hashing.py        — SHA-256, HMAC-SHA256, hash_transfer, verify_evidence_hash
│
├── application/
│   ├── ports/                — Abstract repository interfaces (ABCs)
│   │   ├── evidence_repository.py
│   │   ├── custody_repository.py
│   │   ├── audit_repository.py
│   │   └── user_repository.py
│   ├── use_cases/
│   │   ├── evidence/
│   │   │   ├── create_evidence.py    — hash + HMAC + QR + audit-first write
│   │   │   └── get_evidence.py       — fetch + integrity re-verify on read
│   │   ├── custody/
│   │   │   ├── transfer_custody.py   — validate, hash, append, update status
│   │   │   └── get_chain.py          — full ordered chain for evidence_id
│   │   └── auth/
│   │       ├── login.py              — password + TOTP + JWT issue
│   │       └── logout.py             — JTI to denylist
│   └── services/
│       ├── audit_service.py   — audit_before decorator (write-before-action pattern)
│       └── hash_service.py    — injects HMAC_SECRET from config into domain functions
│
├── infrastructure/
│   ├── database/
│   │   ├── session.py         — SQLAlchemy async engine, session factory
│   │   ├── tables.py          — ORM table definitions (NOT domain models)
│   │   └── repositories/      — Concrete implementations of port ABCs
│   ├── auth/
│   │   ├── jwt_handler.py     — create_access_token, verify_token, denylist check
│   │   ├── totp_handler.py    — pyotp: generate_secret, verify_code
│   │   ├── password_handler.py — passlib bcrypt: hash + verify
│   │   └── dependencies.py    — FastAPI Depends: get_current_user, require_role
│   └── api/
│       ├── main.py            — FastAPI app factory, middleware, lifespan
│       ├── middleware/        — request_id, rate_limiter, security_headers
│       └── v1/
│           ├── routers/       — auth, evidence, custody, reports, audit, health
│           └── schemas/       — HTTP boundary Pydantic schemas (NOT domain models)
│
├── config/
│   └── settings.py            — pydantic-settings: typed config from environment
│
└── alembic/
    └── versions/
        └── 0001_initial_schema.py  — all tables, constraints, indexes, DB role grants
```

---

## Database Design

### Append-Only Enforcement

The application database user (`forenchain_app`) has these permissions:

| Table | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| evidence | ✓ | ✓ | — | — |
| custody_transfers | ✓ | ✓ | — | — |
| audit_logs | ✓ | ✓ | — | — |
| forensic_reports | ✓ | ✓ | ✓ (status only) | — |
| users | ✓ | ✓ | ✓ | — |
| jwt_denylist | ✓ | ✓ | — | — |

This means: if the application server is fully compromised, an attacker with the app's database credentials still cannot delete an evidence record or a custody transfer. The append-only guarantee holds at the DB level, not just the application level.

### pgaudit

All writes to `evidence`, `custody_transfers`, and `audit_logs` are captured by pgaudit at the WAL level. pgaudit writes to the PostgreSQL log stream — outside the `audit_logs` table. A privileged insider who truncates `audit_logs` cannot erase the pgaudit record of having done so.

### Row-Level Security

Each evidence record carries an `agency` field. RLS policies prevent officers from one agency reading records from another. The session variable `app.current_agency` is set from the JWT on every connection. This prevents inter-agency data leakage even if the application's role check is bypassed.

---

## Security Threat Model

### Corrupt Officer (Evidence Tampering)
- **Attack:** Modify evidence description after creation
- **Stop:** No `PUT`/`PATCH` route exists for evidence. DB role has no `UPDATE` on `evidence`.
- **Attack:** Supply a fake `from_badge` on custody transfer
- **Stop:** `CustodyTransferRequest` has no `from_badge` field. App layer reads it from the JWT.

### Corrupt FSL Officer (Report Tampering)
- **Attack:** Resubmit `POST /reports` with different findings for same evidence
- **Stop:** Each submission creates a new record with a new `report_hash`. The old record is not overwritten.
- **Attack:** Alter `submitted_at` to backdate a report
- **Stop:** `submitted_at` is `DEFAULT NOW()` at the DB level. Client-supplied timestamps are ignored.

### External Attacker
- **Attack:** Brute-force login
- **Stop:** 5 failed attempts locks account for 15 minutes. Enforced at both app and DB level.
- **Attack:** Credential theft + login without device
- **Stop:** TOTP is required. Stolen password alone is insufficient.
- **Attack:** Replay stolen JWT
- **Stop:** 15-minute token expiry. JTI denylist checked on every request.
- **Attack:** SQL injection through API parameters
- **Stop:** Pydantic character allowlist validators + DB `CHECK` constraints + SQLAlchemy parameterised queries (three independent layers).

### Privileged DB Insider
- **Attack:** `DELETE FROM custody_transfers WHERE ...`
- **Stop:** `forenchain_app` role has no `DELETE` privilege. Command fails with permissions error.
- **Attack:** Modify audit_logs to hide tracks
- **Stop:** pgaudit captures the attempt at WAL level, independent of `audit_logs` table.
- **Attack:** Direct `UPDATE evidence SET description = '...'`
- **Stop:** `forenchain_app` has no `UPDATE` on `evidence`. Hash mismatch detected by integrity check endpoint.

---

## Authentication Flow

```
Officer → POST /auth/login {badge_id, password, totp_code}
         ↓
1. Fetch user by badge_id
2. Check account not locked (failed_login_count >= 5 → locked 15 min)
3. verify_password(submitted, stored_bcrypt_hash)
4. Check user.totp_enabled — if False, return 403 "provision MFA first"
5. verify_totp_code(user.totp_secret, submitted_code)
6. Reset failed_login_count to 0
7. Issue JWT: sub=badge_id, role=..., agency=..., jti=uuid4(), exp=now+15min
8. Write USER_LOGIN to audit_logs
9. Return {access_token, expires_in: 900}

Per-request:
1. Extract Authorization: Bearer <token>
2. Verify JWT signature + expiry
3. Check jti NOT IN jwt_denylist
4. Check user.is_active = True
5. Check role claim satisfies endpoint requirement
6. Set app.current_agency session variable for RLS
```

---

## Section 65B Certificate (IT Act 2000)

For electronic evidence to be court-admissible, a Section 65B certificate must accompany it. ForenChain automates this:

1. Fetch evidence record, re-verify its `hash_sha256`
2. Fetch full custody chain, compute `chain_hash = SHA-256(concat of all transfer_hashes in order)`
3. Assemble certificate fields (evidence descriptor + chain summary + system declaration)
4. `certificate_hash = SHA-256(canonical_json(all_fields))`
5. `hmac_signature = HMAC-SHA256(certificate_hash, HMAC_SECRET)` — tamper detection
6. Render to signed PDF
7. Store in `certificates_65b` table

The certificate is the system's single most legally sensitive output. Its hash and HMAC are verifiable by any party with access to the ForenChain verification endpoint, without revealing the HMAC secret.

---

## Compliance Summary

| Standard | Requirement | ForenChain Implementation |
|----------|-------------|--------------------------|
| IT Act 2000 s.65B | Chain of custody + system operation certificate | Automated certificate generation, hash-verified evidence trail |
| DPDP Act 2023 | Data minimisation, purpose limitation | Description field capped at 500 chars; RLS prevents cross-purpose access |
| CERT-In 2022 | 180-day log retention | audit_logs is append-only; pgaudit logs must be archived |
| CERT-In 2022 | 6-hour incident reporting | integrity-check endpoint triggers incident workflow on hash mismatch |
| Indian Evidence Act | Electronic record admissibility | SHA-256 hash + HMAC provides tamper detection; 65B cert provides legal cover |

---

## Build Sequence

1. **Domain** — frozen models, hashing, signing. No external deps.
2. **Database** — schema, constraints, DB role grants, pgaudit config.
3. **Auth** — JWT, TOTP, bcrypt, denylist.
4. **Use Cases** — evidence creation, custody transfer, login/logout.
5. **API Routes** — thin HTTP wrappers over use cases.
6. **Section 65B** — certificate generation and PDF rendering.
7. **Security Hardening** — RBAC tests, injection tests, append-only enforcement tests.

Each phase is fully testable before the next begins.

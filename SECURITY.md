# Security Policy

ZLITS is intended to operate as **sovereign national infrastructure** holding personal and
animal data under the Cyber & Data Protection Act [Chapter 12:07] (POTRAZ). We take security and
responsible disclosure seriously and welcome good-faith research within the rules below.

## Reporting a vulnerability

**Do not open a public issue for security problems.** Report privately to:

- **Email:** `security@zlits.gov.zw` *(the operator/State security mailbox; live once the `*.gov.zw` domain is provisioned — until then use the steward contact in GOVERNANCE.md)*
- **PGP (optional):** `[fingerprint / key URL]`

Please include: a description, the affected component and version/commit, reproduction steps, and
the impact you believe it has. We will acknowledge, keep you updated, and credit you (if you wish)
when a fix ships.

### Our response targets
| Stage | Target |
|---|---|
| Acknowledge receipt | within **3 business days** |
| Initial assessment / triage | within **10 business days** |
| Fix or mitigation plan | communicated after triage, severity-dependent |
| Coordinated public disclosure | by agreement, normally after a fix is available |

## Scope

**In scope**
- The API contract and schemas in this repository (e.g. an under-specified auth, idempotency or
  verification flow that would weaken any conformant implementation).
- The reference implementation (`reference-impl/`) and the portal UI (`web/`).
- The **sandbox** registry endpoints, when published.

**Out of scope / do not touch**
- The **production** registry and any **real national, personal, or herd data**. Test only against
  the sandbox or your own local instance — never against production data.
- Denial-of-service / volumetric testing, social engineering, and physical attacks.
- Findings in third-party integrators' own products (report those to the integrator).

## What we especially want to hear about

Given what ZLITS protects, prioritise:
- **Authentication / authorization bypass** — per-operator key scoping, RBAC, or cross-tenant
  data access (one operator reading another's submissions).
- **Certificate integrity** — forging, replaying, or tampering with a registry-signed certificate,
  or anything touching the signing key or the public `GET /v1/verify/{token}` trust anchor.
- **Zone-data tampering** — spoofing or replaying veterinary/FMD-zone deltas to defeat offline
  enforcement.
- **Idempotency / replay** weaknesses on write endpoints.
- **Personal-data exposure** of keepers/holdings (POTRAZ-relevant).
- Standard web/app classes: injection, SSRF, broken access control, secret leakage.

## Safe harbour

We will not pursue or support legal action against researchers who, in good faith:
- stay within this scope, use only sandbox/local data, and avoid privacy violations,
  data destruction, and service degradation; and
- give us reasonable time to remediate before any public disclosure.

If you are unsure whether an action is authorised, ask first at the contact above.

## Data-breach note (operator obligation)

Because the State is the **data controller** and the operator the **processor**, any incident
involving personal data triggers the operator's obligation to notify the controller (the State /
DVS) and to support POTRAZ-required handling. Security reports that may involve personal data are
escalated on that basis.

---

*Governance: [GOVERNANCE.md](./GOVERNANCE.md) · Trademark/impersonation: [TRADEMARK.md](./TRADEMARK.md) ·
Licensing: [LICENSING.md](./LICENSING.md)*

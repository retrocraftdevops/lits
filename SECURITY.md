# Security Policy

LITS is an open **standard** for national livestock registries that hold personal and animal
data. We take security and responsible disclosure seriously and welcome good-faith research within
the rules below. Each national instance runs its own service and publishes its own security
contact; this policy covers the open contract and conformance suite in this repository.

## Reporting a vulnerability

**Do not open a public issue for security problems.** Report privately to the steward contact in
[GOVERNANCE.md](./GOVERNANCE.md). A live national instance publishes its own `security@*.gov.<cc>`
mailbox.

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
- The conformance suite.
- The **sandbox** registry endpoints, when published.

The runnable implementation and portals are held in a separate private repository with its own
security policy.

**Out of scope / do not touch**
- Any **production** registry and any **real national, personal, or herd data**. Test only against a
  sandbox or your own local instance — never against production data.
- Denial-of-service / volumetric testing, social engineering, and physical attacks.
- Findings in third-party integrators' own products (report those to the integrator).

## What we especially want to hear about

Given what LITS protects, prioritise:
- **Authentication / authorization bypass** — per-operator key scoping, RBAC, or cross-tenant data
  access (one operator reading another's submissions).
- **Certificate integrity** — forging, replaying or tampering with a registry-signed certificate, or
  anything touching the signing key or the public `GET /v1/verify/{token}` trust anchor.
- **Zone-data tampering** — spoofing or replaying veterinary/FMD-zone deltas to defeat offline
  enforcement.
- **Idempotency / replay** weaknesses on write endpoints.
- **Personal-data exposure** of keepers / holdings.
- Standard web/app classes: injection, SSRF, broken access control, secret leakage.

## Safe harbour

We will not pursue or support legal action against researchers who, in good faith:
- stay within this scope, use only sandbox/local data, and avoid privacy violations, data
  destruction, and service degradation; and
- give us reasonable time to remediate before any public disclosure.

If you are unsure whether an action is authorised, ask first via the contact above.

---

*Governance: [GOVERNANCE.md](./GOVERNANCE.md) · Trademark/impersonation: [TRADEMARK.md](./TRADEMARK.md) ·
Licensing: [LICENSING.md](./LICENSING.md)*

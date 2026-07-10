# Changelog

All notable changes to the **LITS API contract** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The contract is versioned in the URL
path (`/v1`); see [CONTRIBUTING.md](./CONTRIBUTING.md) for the change policy.

## [2.0.0] — 2026-06-25

Adds the elevated-scope read plane (for export integrators such as METS) and the disease/lab
surveillance write plane (for field integrators such as FuroTrack). Authorisation is key-bound:
elevated endpoints are gated by scopes carried on the operator's API key, granted by the registry
operator — a client cannot self-elevate.

- **Elevated reads** (operator-granted key scope): `GET /v1/animals/{id}/movements`
  (`movements:read`), `GET /v1/animals/{id}/health` (`health:read`), `GET /v1/holdings/{id}`
  (`holdings:read`, returns GPS + EUDR `deforestation_free`/`legality_verified` flags).
- **Disease surveillance**: `POST /v1/disease-cases`, `GET /v1/disease-cases/{id}`,
  `PATCH /v1/disease-cases/{id}` (`disease_cases:write`).
- **Laboratory results**: `POST /v1/lab-results` — positives auto-link to an open disease case.
- **Integrator poll**: `GET /v1/movements/list?status=&since=` for movement auto-sync.
- New schemas: `AnimalMovementHistory`, `AnimalHealthStatus`, `HoldingDetail`,
  `DiseaseCaseReport/Ack/Detail/Update`, `LabResultReport/Ack`.

Preserves the dzinza-implementation-specific surface (`/keeper/scans`, `/seals/verify`,
`/trust-list`) not present in the upstream open contract.

## [Unreleased]

First public draft of the open LITS contract. Current surface:

- **Client API** (`openapi.yaml`): `POST /v1/animals`, `GET /v1/animals/{national_id}`,
  `POST /v1/movements`, `POST /v1/vaccinations`, `POST /v1/certificates` (request),
  `GET /v1/certificates/{id}`, `POST /v1/certificates/{id}/revoke`, `GET /v1/zones` (delta sync),
  `GET /v1/campaigns` (active vaccination campaigns), `GET /v1/verify/{token}` (public, no auth),
  `GET /healthz`. Per-operator bearer auth,
  `Idempotency-Key` on writes, acknowledgement IDs on every response.
- **Control-plane API** (`openapi-admin.yaml`): zone authoring, integrator accreditation and
  API-key management, certificate issue/revoke, movement transitions, and audit.
- Sample payloads (`examples/`), a contract validator (`scripts/validate.py`), and the
  conformance approach (`conformance/`).

The contract is `*-draft` and may change without a version bump until `1.0.0` is ratified with
the competent authority (see [CONTRIBUTING.md](./CONTRIBUTING.md)).

---

*Pre-release development history is kept with the implementation in the private platform
repository; this public changelog begins with the first published draft of the contract.*

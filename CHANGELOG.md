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

### Fixed

Contract hygiene. No path, operation, schema or field visible to a client changes — every fix
below removes something the YAML parser was already discarding, or names something the parser
was already keeping.

- **`openapi.yaml` defined `/authorized-keepers` and `/keepers/resolve` twice** (byte-identically).
  YAML keeps only the last mapping key, so the earlier pair was silently discarded — and
  `@redocly/cli lint` aborted the whole run with `duplicated mapping key` before it validated
  *either* spec, which is why the lint step reported nothing else. The second block is removed,
  keeping the first so the three elevated reads (`/animals/{id}/movements`,
  `/animals/{id}/health`, `/holdings/{id}`) stay contiguous. Path count is unchanged at 43,
  because the duplicate never contributed one.
- **Two tags were used but never declared**: `campaigns` in `openapi.yaml` and `trust-admin`
  in `openapi-admin.yaml`. An undeclared tag still groups operations, but carries no
  description, so generated documentation drops those operations into an untitled section.
  Both are now declared in their spec's top-level `tags:` list.
- **`standards/registry.yaml`: the `eudr.plot-geometry` control carried `seamPin` and `notes`
  twice.** The duplicate `seamPin` was identical and therefore harmless, but the *first* `notes`
  was discarded by the loader — and that was the one recording the 2026-08-01 correction of this
  control from `implemented` down to `partial`. The register was asserting a downgraded status
  whose stated justification had silently vanished from the loaded document. Both notes are
  merged under the single surviving key; the `partial` status is unchanged.

None of these were caught by either gate: `scripts/validate.py` does not detect duplicate YAML
mapping keys or undeclared tags, and `@redocly/cli`'s recommended ruleset does not enable
`operation-tag-defined` and does not lint `standards/registry.yaml` at all. Teaching the gate to
reject a duplicate mapping key and an undeclared tag is the follow-up that keeps these fixed.

---

*Pre-release development history is kept with the implementation in the private platform
repository; this public changelog begins with the first published draft of the contract.*

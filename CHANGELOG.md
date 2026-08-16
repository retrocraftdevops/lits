# Changelog

All notable changes to the **LITS API contract** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The contract is versioned in the URL
path (`/v1`); see [CONTRIBUTING.md](./CONTRIBUTING.md) for the change policy.

## [2.1.0] — 2026-08-16

### Added

Vaccination enrichment — six optional fields on the `Vaccination` request schema. **Genuinely
additive: no existing client can break.** Nothing is removed, renamed, or made required, and the
`required` set is untouched. Because `Vaccination` is `additionalProperties: false`, this is
strictly a *widening* — payloads that the registry would previously have rejected are now
accepted, and every payload valid before this change is still valid. There is no tightening in
this release.

- **`lot_expiry`** (`date`). `lot_number` already existed and already satisfies the batch
  requirement — it is **not** duplicated under a new name. Expiry is the missing half: the lot
  number identifies the batch for a recall, only the expiry says whether the dose was still
  viable when it went in.
- **`cold_chain_ok`** (`boolean|null`) — the administering officer's attestation that the cold
  chain held. `false` is a cold-chain **exception**: it is the per-vaccination event that the
  control plane's existing `CampaignProgress.cold_chain_exceptions` counter counts, and the field
  description says so explicitly so the seam is not left to inference. Null or absent means *not
  asserted*, which is deliberately **not** an assertion that the chain held.
- **`cold_chain_evidence_ref`** (`string|null`) — a hash or URI pointing into the integrator's
  own records. **Raw fridge telemetry stays out of the registry**: temperature time series,
  sensor readings and alarm logs remain with the integrator. The contract carries the attestation
  and a pointer to its proof, never the series.
- **`dual_id_confirmed`** (`boolean|null`) — the animal was presented with both its permanent
  mark (brand or tattoo) and its tag, and the two agreed. This is **not** "two tags".
- **`holding_id`**, **`zone_code`** — where and in which veterinary zone the dose was
  administered. Recorded rather than derived, because deriving either from the animal's *current*
  position gives the wrong answer for any animal that has since moved, and campaign coverage is
  computed per holding and per zone.

`examples/record-vaccination.json` and the integration guide's field mapping are updated in the
same change (CONTRIBUTING.md quality gate, item 3). No control-plane change was needed:
`CampaignProgress.cold_chain_exceptions` already exists.

> **TO-VERIFY.** The driver is **South Africa's RVS-FMD scheme, reported gazetted 4 May 2026**,
> conditioning participation on a digital system recording vaccination date, vaccine batch number
> and vaccine storage temperature. That instrument and its requirements are **unverified** and
> must be confirmed with the South African authority before any profile cites them.
>
> **TO-VERIFY.** The dual-identification rule is attributed to the **Animal Identification Act 6
> of 2002**, under which the permanent brand/tattoo is understood to be the legal identifier and
> the tag to supplement it — hence "permanent mark *and* tag", not "two tags". This citation is
> **unverified**. It is deliberately **not** written into the contract: the schema describes the
> fact recorded and states that the legal weight is defined by the territory profile, because
> hard-coding one jurisdiction's identification law into a multi-country contract is the
> neutrality failure RFC 0003 §3 argues against. The citation belongs in `profiles/za`, which is
> approved but not yet written.

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

None of these was caught by either gate at the time: `scripts/validate.py` did not detect
duplicate YAML mapping keys or undeclared tags, and `@redocly/cli`'s recommended ruleset does not
enable `operation-tag-defined` and does not lint `standards/registry.yaml` at all. The gate has
since been taught both — see *Changed* below.

### Changed

- **`scripts/validate.py` now rejects duplicated YAML mapping keys and undeclared operation
  tags.** The gate was blind to both classes, which is how the defects above shipped. Proven
  blind rather than assumed: a planted duplicate path left the validator reporting `OK` *while
  silently swallowing real contract surface* — unique `$ref`s fell 43 → 42 as the planted stub
  overwrote the genuine definition. A gate that cannot see a defect which deletes contract from
  the published document is not a gate.
  - **Duplicate mapping keys** in `openapi.yaml`, `openapi-admin.yaml` and
    `standards/registry.yaml`. Runs first, before anything is believed about the parse, because
    every other check reads the already-deduplicated document. It is the only check anywhere
    covering `standards/registry.yaml`, which `@redocly/cli` does not lint.
  - **Undeclared tags** — every tag an operation references must appear in its spec's top-level
    `tags:` list. Redocly's recommended ruleset does not enable `operation-tag-defined`.
  - Both were proven to fail on a planted defect and to pass again on its removal before being
    relied on. No contract file changes; this is gate-only.
- **`scripts/validate.py` now validates every `examples/*.json` against the schema it
  illustrates.** CONTRIBUTING.md's quality gate already *required* that examples "never drift
  from the contract"; nothing enforced it. The parse check proves only that a file is JSON — an
  example carrying an undeclared property, or a wrong-typed value, shipped green. Examples are
  the first thing an integrator copies, so drift here is more expensive than almost anywhere
  else in the repo.
  - Checks declared **type** (including nullable type arrays), **enum** membership, **required**
    properties and **`additionalProperties: false`**, recursing through internal `$ref`s and
    array items — so a violation nested inside `Movement.animals[]` or `ZoneDelta.zones[]` is
    caught, not just a top-level one.
  - An example with **no entry** in the file→schema map is a **failure, not a skip**, so adding
    an example cannot silently opt it out of the check.
  - Proven in both directions before being relied on, and beyond the top level: an
    `additionalProperties` violation, a wrong type, a missing required property nested behind a
    `$ref`, a bad enum value, and an unmapped example each produced `FAIL`/exit 1, and each
    restored to green. All five existing examples conform, so the check landed green.
- **This repository now owns a standards-vocabulary parity step**
  (`scripts/check-standards-parity.py`, wired into `.github/workflows/validate.yml` beside
  `scripts/validate.py`). `standards/README.md` has always claimed that each of the four repos
  sharing `standards/vocabulary.v1.json` "hashes it and fails CI on drift"; for this repo that
  was **not true** — detection lived only in FuroField's pipeline, a single point of failure for
  a four-repo obligation. No contract file changes; this is gate-only.
  - **It works with this repo checked out alone**, because a standards repo cannot assume its
    siblings are on the runner. Standalone it verifies `vocabulary.v1.json` against a canonical
    digest recorded in the script, validates the structure `scripts/validate.py` indexes into
    (a missing `$defs.Status.enum` was a `KeyError` traceback rather than a diagnosis), and
    checks `registry.yaml` declares this repo and the pinned version.
  - **An absent sibling is never reported as an agreeing sibling.** Present checkouts are
    compared byte for byte and each `seamPin` is checked to be named on at least one other side;
    absent ones print `NOT COMPARED` and the summary reads `PASS (SELF-CHECK ONLY) … shows
    NOTHING about cross-repo agreement`. `--require-siblings` makes absence a failure for local
    use when adding a pin.
  - **It does not duplicate `~/projects/FuroField/scripts/check-standards-parity.sh`**, which
    remains authoritative for the per-seam *value* assertions across all four repos. A fourth
    copy of the four-repo topology is the drift the program exists to detect.
  - Proven capable of failing before being relied on, against copies in a detached worktree —
    nothing in this repository was mutated. A drifted own vocabulary, a deleted
    `$defs.Status.enum`, a drifted sibling copy, a seam pin no sibling carries, and
    `--require-siblings` with none present each produced `FAIL`/exit 1 naming the file or the
    pin; each restored to exit 0.
  - **Stated limit:** a digest recorded beside the file it pins can be updated in the same edit.
    It catches silent drift (a reformat, an editor rewrite, a hand-merged conflict); a deliberate
    change is caught instead by the version-bump rule, which this gate ties to the register and
    the four-way script ties to the siblings.

---

*Pre-release development history is kept with the implementation in the private platform
repository; this public changelog begins with the first published draft of the contract.*

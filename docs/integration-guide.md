# LITS Client Integration Guide

How an accredited platform integrates with the LITS registry as a **client** — auth, the
write/read operations, the reliability contract, zone sync, certificates, and the
dry-run → live lifecycle. **FuroTrack is the worked reference** throughout (it is the first
client, not the owner); every other vendor integrates the same way with its own API key.

> Status: DRAFT design. Pairs with the client contract [../openapi.yaml](../openapi.yaml) and
> the two-plane model in registry-operations.md §0. No production
> endpoint exists yet — until a sandbox is live, clients run in **dry-run** (§7).

---

## 0. You are a client (the two-plane model from your seat)

LITS runs on a **control plane** (the sovereign registry + Admin Portal, on `*.gov.zw`) and
a **client plane** (your capture app). The full model is in
registry-operations.md §0; the only thing a client must internalise:

- **The registry is the source of truth.** You **submit** events and **read** reference data.
  You never own the national identity, movement or health record.
- **No client gets privileged access.** FuroTrack, competitors, abattoir systems — all use the
  same `openapi.yaml`, same conventions, their own per-operator key.
- **You never call the control-plane API** ([../openapi-admin.yaml](../openapi-admin.yaml)) —
  that is zone authoring, accreditation, key issuance and audit, for DVS / operator staff only.

A clean way to think about it: integrating with LITS is **one more registry adapter**, exactly
like talking to NamLITS (Namibia), SLITS (Eswatini) or BAITS (Botswana). No new architecture.

---

## 1. The operations & the adapter mapping

Four operations cover the integration. The right column is the **FuroTrack reference adapter**
(`LITSAdapter`, ZLITS (Zimbabwe)0 in its registry list); your platform supplies the equivalent.

| LITS endpoint | Purpose | FuroTrack adapter method |
| --- | --- | --- |
| `POST /v1/animals` | Register / identify an animal → `national_id` | `register_animal` |
| `POST /v1/movements` | Lodge a movement permit / consignment → `permit_reference` | `record_movement` |
| `POST /v1/vaccinations` | Record a vaccination / mandatory disease event → `id` | `record_vaccination` |
| `GET /v1/zones?since_version=N` | Pull the veterinary / FMD zone delta | `fmd_zone_sync` consumer |
| `POST /v1/certificates` | **Request** a registry certificate (request-only, §6) | `request_certificate` |

### Field mapping (reference: FuroTrack `LITSAdapter`)

The adapter is a thin field translation from FuroTrack's internal model to the contract — no
business logic. Representative mappings:

| Operation | FuroTrack field → LITS field |
| --- | --- |
| `register_animal` | `tag → visual_tag`, `eid_tag → eid`, `farm_registration_number → holding_id`, `owner_name → keeper_name`, plus `species/breed/sex/date_of_birth/district/fmd_zone_code` passthrough |
| `record_movement` | `permit_number`, `subject_count → head_count`, per-animal `national_id/visual_tag/species/fmd_zone_code`, `origin_site_name → origin`, `approved_by → vet_endorsement`, `destination(_zone_code/_type)`, `purpose`, transporter/vehicle/dates |
| `record_vaccination` | animal `national_id` (or `eid_tag`), `disease`, `vaccine_name`, `lot_number`, `dose`, `administered_at`, `next_due_at`, `vet_name → administered_by`, `campaign_id` |
| `request_certificate` | `kind` (default `movement_permit`), `subject_type` (default `movement`), `subject_id`, `destination`, `valid_until`, `vet_endorsement` |

See request bodies in [../examples/](../examples/): [`register-animal.json`](../examples/register-animal.json),
[`record-movement.json`](../examples/record-movement.json),
[`record-vaccination.json`](../examples/record-vaccination.json),
[`issue-certificate.json`](../examples/issue-certificate.json).

---

## 2. Conventions every client must honour

These are load-bearing — [../CONTRIBUTING.md](../CONTRIBUTING.md) forbids removing them, so a
client may rely on them permanently.

- **Per-operator bearer auth.** Each platform is issued its own key and sends
  `Authorization: Bearer <operatorApiKey>`. The registry attributes every submission to a
  known operator. (Public `GET /v1/verify/{token}` and `GET /healthz` take no auth.)
- **`Idempotency-Key` on every write.** A client-generated key (≤200 chars) makes a write safe
  to retry: the registry returns the **original** result for a repeated key. Generate one key
  per logical event and reuse it across retries.
- **An acknowledgement ID on every write.** `national_id` (animals), `permit_reference`
  (movements), `id` (vaccinations/certificates) — persist it against your local record.
- **Path-versioned (`/v1`).** Additive changes stay in `/v1`; breaking changes ship under a new
  `/vN`. Build against `/v1` and ignore unknown fields you don't consume.

---

## 3. Reliability — retries, circuit breaker, receipts

A national registry will have outages and zone-rule rejections; a client must degrade
gracefully and never lose an event. The FuroTrack reference flush worker shows the pattern:

- **Write an audit receipt first.** Before calling the registry, record a
  `government_sync_receipts` row (`status = pending`); update it to `synced` / `dry_run` /
  `not_configured` / `error` on the outcome. **No event is silently dropped** — every attempt
  leaves a row carrying the registry `ack_id` / `verify_url` and the response.
- **Retry with exponential backoff + full jitter** to avoid a thundering herd against the
  registry.
- **Per-registry circuit breaker.** After `CIRCUIT_OPEN_THRESHOLD` consecutive failures, mark
  the registry `open` and skip it for `CIRCUIT_RESET_SECONDS`, then probe again. This keeps one
  registry's outage from stalling your whole sync pipeline.
- **Replay errored receipts** on the next flush — the `Idempotency-Key` (§2) makes replay safe.

---

## 4. Zone reference sync (delta)

Veterinary / FMD zones are **authored by DVS in the Admin Portal** and **only consumed** by
clients — a client never creates a national zone (registry-operations.md §1).

- Call `GET /v1/zones?since_version=N` with the last `server_version` you stored; the registry
  returns only zones whose `zone_version > N`, plus the current `server_version`.
- Persist `server_version` and pass it back next time — a **monotonic, conflict-free delta** that
  works for offline field devices.
- The response shape matches FuroTrack's existing `fmd_zone_sync` consumer, so it ingests the
  feed unchanged. See [`zone-delta.response.json`](../examples/zone-delta.response.json).

> Migration note (FuroTrack): today FuroTrack can author zones locally. Under LITS-governed
> Zimbabwe that authority moves to the registry and FuroTrack becomes **read-only** on national
> zones — otherwise two competing zone truths emerge.

---

## 5. Movement rules — expect rejections

`POST /v1/movements` is **enforced**, not just recorded. The registry checks veterinary-zone
rules and may answer:

- `201` with `status: lodged` — the request is recorded for authority review (watch
  `crosses_zone_boundary`); this is **not** an approval or an issued permit.
- Cross-zone requests remain `lodged` and are reviewed under the authority's configured
  veterinary approval workflow.
- `409` with an `Error` body (`code: zone_blocked`) — the movement crosses a blocked boundary
  and is **refused**. Surface this to the user as a hard stop, not a retryable error.

Handle `409` distinctly from transport errors: a blocked movement is a correct registry
decision, so do **not** feed it to the retry/circuit-breaker path (§3).

---

## 6. Certificates — request only; the registry issues & signs

This is the rule clients most often get wrong. The certificate of record is **minted by the
authority, never by a client** (registry-operations.md §4).

1. A client `POST /v1/certificates` only **requests** one → status `requested`, **unsigned**.
2. The competent authority (Official Vet / DVS) **issues and signs** it on the control plane,
   and is the only party that can **revoke** it.
3. A client then `GET /v1/certificates/{id}` to fetch the signed payload, the official
   `reference`, the `verify_url` (QR target) and the canonical `pdf_url`.
4. A client may **fetch, embed, print and preview** the registry-signed certificate — but never
   mints its own "national" certificate. That would re-introduce a competing authority and break
   recognisability at borders / abattoirs.

The public `GET /v1/verify/{token}` (no auth) returns a sanitised status anyone can scan — the
trust anchor that works independently of any vendor.

---

## 7. Lifecycle — dry-run → live

A client integrates **before** a live endpoint exists and flips over with config only, no code
change. The FuroTrack reference uses these env vars (other vendors use their own prefix):

| Variable | Role |
| --- | --- |
| `LITS_API_URL` | Registry base URL (sandbox, then production). |
| `LITS_API_KEY` | The per-operator bearer key issued on accreditation. |
| `LITS_REGISTRATION_PATH` / `LITS_MOVEMENT_PATH` / `LITS_VACCINATION_PATH` / `LITS_CERTIFICATE_PATH` | Verified endpoint paths — the adapter **does not guess routes**. |
| `GOVT_SYNC_DRY_RUN` or `LITS_DRY_RUN` | Force dry-run regardless of config. |

States:

1. **Not configured** — no URL/key/paths set → the client keeps local traceability records and
   marks the authority connection unavailable, but must not present, approve, complete, or print
   a regulated movement as a national permit. No calls are made.
2. **Dry-run** — `GOVT_SYNC_DRY_RUN=true` → receipts recorded as `dry_run`, **no calls made**;
   used to validate payload mapping end-to-end.
3. **Live** — URL + key + verified paths set, dry-run off → real `POST`s; receipts carry the
   registry `ack_id` and any `verify_url`.

Promote one registry at a time; the audit receipts let you verify mapping in dry-run before any
real submission.

---

## 8. Accreditation & conformance

Open spec does **not** mean anyone may pose as official ([spec-governance.md §3](./spec-governance.md)).

- Run the **conformance suite** (the conformance suite) against your
  integration — it ties behaviour to the contract so the two cannot drift.
- Get **accredited** by the operator, who issues your per-operator key (control plane).
- Only an accredited, conformance-tested integrator with a live key may call itself
  **"ZLITS-conformant"** or display the badge — see [../TRADEMARK.md](../TRADEMARK.md).

---

## 9. Error reference

| Status | When | Client action |
| --- | --- | --- |
| `400` | Malformed request | Fix payload; do not retry unchanged. |
| `401` | Missing / invalid key | Check `Authorization`; re-accredit if revoked. |
| `409` (`zone_blocked`) | Movement crosses a blocked zone | Hard stop — surface to user; **not** retryable. |
| `409` (conflict) | Conflicting state on register | Re-fetch the record; reconcile. |
| `422` | Validation failed | Fix the flagged fields. |
| `404` | Unknown `national_id` / certificate | Confirm the subject exists / was registered first. |
| transport / `5xx` | Registry unavailable | Retry with backoff + jitter; trip the circuit breaker (§3). |

---

## References

- Client API contract — [../openapi.yaml](../openapi.yaml) · examples — [../examples/](../examples/)
- Two-plane model, zones, certificates, RBAC — registry-operations.md
- Conformance, trademark & accreditation — [spec-governance.md](./spec-governance.md), [../TRADEMARK.md](../TRADEMARK.md)
- Load-bearing conventions & change policy — [../CONTRIBUTING.md](../CONTRIBUTING.md)
- Why FuroTrack is the reference, not the owner — [../README.md](../README.md)

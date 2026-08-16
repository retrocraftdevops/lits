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

These operations cover the integration. The right column is the **FuroTrack reference adapter**
(`LITSAdapter`, ZLITS (Zimbabwe)0 in its registry list); your platform supplies the equivalent.

| LITS endpoint | Purpose | FuroTrack adapter method |
| --- | --- | --- |
| `POST /v1/animals` | Register / identify an animal → `national_id` | `register_animal` |
| `POST /v1/movements` | Lodge a movement permit / consignment → `permit_reference` | `record_movement` |
| `GET /v1/movements/list?status=&since=` | Poll for permits the authority has acted on (§5) | movement auto-sync |
| `POST /v1/vaccinations` | Record a vaccination / mandatory disease event → `id` | `record_vaccination` |
| `GET /v1/zones?since_version=N` | Pull the veterinary / FMD zone delta | `fmd_zone_sync` consumer |
| `GET /v1/quarantine-orders?since_version=N` | Pull the disease-response-order delta (§4b) | *new at `2.2.0` — same loop as `fmd_zone_sync`* |
| `POST /v1/certificates` | **Request** a registry certificate (request-only, §6) | `request_certificate` |

### Field mapping (reference: FuroTrack `LITSAdapter`)

The adapter is a thin field translation from FuroTrack's internal model to the contract — no
business logic. Representative mappings:

| Operation | FuroTrack field → LITS field |
| --- | --- |
| `register_animal` | `tag → visual_tag`, `eid_tag → eid`, `farm_registration_number → holding_id`, `owner_name → keeper_name`, plus `species/breed/sex/date_of_birth/district/fmd_zone_code` passthrough |
| `record_movement` | `permit_number`, `subject_count → head_count`, per-animal `national_id/visual_tag/species/fmd_zone_code`, `origin_site_name → origin`, `approved_by → vet_endorsement`, `destination(_zone_code/_type)`, `purpose`, transporter/vehicle/dates |
| `record_vaccination` | animal `national_id` (or `eid_tag`), `disease`, `vaccine_name`, `lot_number`, `dose`, `administered_at`, `next_due_at`, `vet_name → administered_by`, `campaign_id`, plus optional `lot_expiry`, `cold_chain_ok`, `cold_chain_evidence_ref`, `dual_id_confirmed`, `holding_id`, `zone_code` passthrough |
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

**Gate on `movement_restriction`, never on `zone_type`.** `movement_restriction`
(`none | restricted | blocked`) is the load-bearing field and its values do not change.
`zone_type` is **descriptive** — for labelling and colour — and the registry adds values to it:
`standstill` arrived at `2.2.0` (see §4b). A client that switches exhaustively on `zone_type` with
no default branch will break on the next one; a client that blocks on
`movement_restriction: blocked` never will. Treat an unrecognised `zone_type` as a display
fallback, not an error.

### 4b. Disease response orders — quarantine & standstill (delta sync)

New at `2.2.0`. An **order** is the act of authority that closes a holding or stands the country
still. Before it existed in the contract, a farm app whose keeper was under quarantine would
lodge a movement, show a permit reference, and let the stock leave — the registry knew, and had
no way to tell you.

- `GET /v1/quarantine-orders?since_version=N` is **`/zones`'s loop, field for field**. Same
  cursor, same persistence rule, same offline-first intent. If you already have `fmd_zone_sync`,
  you have this. See [`quarantine-order-delta.response.json`](../examples/quarantine-order-delta.response.json).
- **A lifted or revoked order stays in the feed** carrying that `status`. Do not treat
  disappearance as retraction — it means you have not synced, and a client that assumed otherwise
  would enforce a lifted order forever.
- **Read `conditions[].code` and fail CLOSED on a value you do not recognise** — treat the order
  as at least as restrictive as `no_movement_on_off`. This is the opposite of the usual "ignore
  unknown enum values" advice and it is deliberate: ignoring a restriction you do not understand
  permits a movement the authority forbade. A delayed truck is cheaper than the disease leaving
  the cordon.
- **Do not compute the dates.** `milestones[{code, date}]` are supplied by the registry under its
  own territory's profile. Render and act on them; do not re-derive a review date from your own
  copy of the rules, because your copy goes stale and the registry's does not.
- **You may already be enforcing standstills without doing anything.** An active `standstill`
  order is *also* projected into `GET /v1/zones` as `zone_type: standstill` with
  `movement_restriction: blocked`. If you gate on `movement_restriction`, a national standstill
  binds your client on its next zone sync with **no code change** — which is the point, since
  outbreak response is measured in hours. See
  [`standstill-zone-delta.response.json`](../examples/standstill-zone-delta.response.json).
- **Join, do not double-count.** `QuarantineOrder.projected_zone_code` names the zone an order
  projects into. A client reading both feeds should join on it, or it will report one restriction
  as two.
- **Trace flags** (`trace_flags` on `GET /v1/animals/{national_id}` and
  `GET /v1/animals/{id}/health`) are **registry-applied only** — there is no client write path,
  and asking for one is asking to exercise authority you do not have. `expires_at: null` means
  **lifelong**, not "unset": a `sero_positive_lifelong` flag outlives any later negative test, so
  a market-access decision made from `disease_free` and `last_test_result` alone can be wrong in
  the permissive direction.

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

### Reading back the outcome

`201 lodged` is where your write ends and the authority's workflow begins. To learn what happened
next, **poll `GET /v1/movements/list?status=approved&since=<last sync>`** and push your field data
for the permits that come back. That is the auto-sync loop the endpoint exists for.

Two things to build against, and they are different on purpose:

| | Shape | `status` can be |
| --- | --- | --- |
| **Acknowledgement** of your lodgement (`POST /v1/movements`, `POST /keeper/movements`) | `MovementAck` | `lodged`, `blocked` — **only these two.** You lodge; the authority approves. Your own submission never comes back authorised. |
| **Read view** of a permit (`GET /v1/movements/list`) | `MovementPermitSummary` | the full lifecycle `MovementLifecycleStatus`: `lodged`, `under_review`, `approved`, `rejected`, `blocked`, `departed`, `arrived`, `completed`, `cancelled`, `expired` |

**Do not switch exhaustively on the read-view status.** Treat an unrecognised value as "not
approved" and carry on — the lifecycle is the authority's, and per §2 a client ignores what it
does not consume. Sample response:
[`movement-list.response.json`](../examples/movement-list.response.json).

> Fixed at contract `2.1.1`. Before it, the list's response items were `MovementAck`, so a
> conformant registry **could not return an approved permit from this endpoint at all** — the
> filter accepted `status=approved` and the schema forbade the answer. If you built against
> `2.0.0` or `2.1.0` and concluded the poll did not work, it did not; nothing on your side was
> wrong. No client change is required to adopt the fix: every field you already parse is
> unchanged, in the same place, with the same type.
>
> **Cursor caveat, stated rather than left to be discovered.** The items carry `recorded_at` (when
> the permit was lodged), not an "updated at" — so `since` cannot be advanced from the response
> body. Use your own request timestamp, and expect to re-see recently-changed permits. The
> monotonic-cursor fix for this is the event feed on the roadmap, not another timestamp here.

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

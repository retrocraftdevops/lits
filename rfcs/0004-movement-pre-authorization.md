<!--
SPDX-FileCopyrightText: 2026 The LITS steward
SPDX-License-Identifier: Apache-2.0
-->
# RFC 0004 — Movement pre-authorization (reading the permit a client lodged)

- **Status:** Draft (pending steering-committee ratification per GOVERNANCE.md §4 "RFC for
  sovereign-impacting changes" — this touches **movement authority** and **certificate
  semantics**).
- **Affects:** `openapi.yaml` (client) 2.1.0 → 2.2.0, `openapi-admin.yaml` 1.5.0-draft →
  1.6.0-draft. (If this lands before RFC 0003, read those as 2.0.0 → 2.1.0 and 1.4.0-draft →
  1.5.0-draft.)
- **Backwards compatibility:** Additive only, within `/v1`, plus **one enum widening that fixes a
  latent contract defect** — see §3, which is the only change here that alters an existing
  schema.
- **Fixes a defect in the shipped contract.** `GET /v1/movements/list` has accepted
  `status=approved` since **`bd0ee9e` (2026-07-10)**, but **`3b8e917` (2026-07-15)** narrowed the
  *shared* `MovementAck.status` enum to `{lodged, blocked}`. Because `MovementAck` is the response
  item of that list, **a conformant server cannot return an approved permit from the one endpoint
  the integration guide instructs integrators to poll for approvals.** This is live in `2.0.0`
  today, not a gap this RFC merely happens to close — see §1 and the regression case at §8.6.
- **Builds on:** commit `3b8e917` ("clarify movement authority contract"), whose distinction this
  RFC completes rather than revisits. **Relates to:** RFC 0001 (qualified seals — how a permit
  verifies at a roadblock with no signal), RFC 0003 (the order a permit may be issued under).

> **Honesty note.** Every statutory fact below is **TO-VERIFY**, per the `profiles/mz`
> discipline. The design deliberately avoids needing any of them to be settled.

---

## 1. The problem

Commit `3b8e917` established the right rule and said it plainly in the schema:

> `permit_reference` — *Registry movement-request reference; **it is not evidence of approval or
> issuance.*** … `status: [lodged, blocked]` — *a client lodges a request; only the authority
> control plane can later approve it.*

That is correct, and it is the foundation this RFC builds on. **Clients lodge. The authority
issues.** Nothing here weakens it.

But the rule was only half-plumbed. Having lodged a request and received a `permit_reference`, a
client **cannot ask what happened to it.** There is no per-permit read. The only way to learn the
outcome is `GET /v1/movements/list?status=&since=`, which polls a whole time window across every
permit the key can see, in order to answer a question about one.

And that poll does not actually work, for a reason worth stating precisely because it is a real,
verifiable defect in the published contract rather than a matter of taste:

- `/v1/movements/list` accepts `status` ∈ `{lodged, approved, rejected, departed, completed,
  blocked}` — landed 2026-07-10 in `bd0ee9e`.
- Its `200` response is an array of **`MovementAck`**, whose `status` enum `3b8e917` narrowed on
  2026-07-15 to `{lodged, blocked}`.

`MovementAck` is shared between the `POST` acknowledgement and the list response. Narrowing it was
right for the acknowledgement — a lodgement is never born approved — and the list endpoint was
collateral. **The consequence is that a conformant server cannot express an approved permit in
the very endpoint the integration guide tells integrators to poll in order to "detect permits
that have transitioned to `approved`."** The documented integration loop is unsatisfiable against
the documented schema.

So the gap this RFC closes is narrow and concrete: *a client can lodge, and cannot read back.*

The second, field-level version of the same gap: inside an area under an order, movement is
frequently permitted **only under a permit issued for that movement**. A client has no way to say
"this consignment moves under permit X", no way to say "under order Y", and no way to attach the
cleaning-and-disinfection certificate the condition required. The information exists on paper at
the roadblock and nowhere in the contract.

## 2. Non-goal: there is no third permit object

The strong temptation is to introduce a `Permit` resource alongside `Movement` (the client's
lodgement) and the admin plane's permit lifecycle. **This RFC does not**, and the discipline is
the main thing it contributes.

There is already exactly one regulated object here — the movement permit — with a lifecycle the
control plane already drives (`POST /admin/movements/{ref}/{action}`, actions `lodge | review |
approve | reject | depart | arrive | complete | cancel`). A third object would mean a third
identifier, a third state machine, and an inevitable question at a roadblock about which of two
documents wins.

Instead this RFC adds:

1. a **read view** of the object that already exists (§3),
2. a pointer to the **signed evidence** object that already exists — a `Certificate` of kind
   `movement_permit` (§4), and
3. **three optional request fields** so a lodgement can cite the authority it moves under (§5).

Nothing new is invented that the contract did not already have a home for.

## 3. `GET /v1/movements/{permit_reference}` — the permit view

```
GET /v1/movements/{permit_reference}   → MovementPermit
```

```yaml
MovementPermit:
  type: object
  required: [permit_reference, status, animals]
  properties:
    permit_reference: { type: string }
    id:               { type: string }
    status:
      type: string
      enum: [lodged, under_review, approved, rejected, blocked, departed, arrived, completed, cancelled, expired]
      description: |
        Full lifecycle status as driven by the control plane. `lodged` still means only that the
        request was recorded — approval is `approved` and nothing else.
    crosses_zone_boundary: { type: boolean }
    recorded_at:  { type: string, format: date-time }
    decided_at:   { type: [string, 'null'], format: date-time }
    decision_note: { type: [string, 'null'], description: Reason, where the authority gives one. }

    animals:
      type: array
      minItems: 1
      items:
        type: object
        required: [national_id]
        properties:
          national_id: { type: string }
          visual_tag:  { type: string }
          species:     { type: string }
      description: |
        The individual animals the permit authorises — not a head count. A permit that names
        a number cannot be checked against a truck; a permit that names animals can.

    conditions:
      type: array
      items: { $ref: '#/components/schemas/OrderCondition' }   # RFC 0003 §4.1 vocabulary
      description: Conditions attached to this permit, using the pinned condition codes.

    valid_from:  { type: [string, 'null'], format: date-time }
    valid_until: { type: [string, 'null'], format: date-time }

    issued_under_order_id: { type: [string, 'null'], description: RFC 0003 order, where applicable. }
    permit_certificate_id: { type: [string, 'null'], description: See §4. Null until approved. }

    origin:      { type: string }
    destination: { type: string }
    origin_zone_code:      { type: [string, 'null'] }
    destination_zone_code: { type: [string, 'null'] }
```

**Why individual animals — the Red-Cross-permit shape.** A movement permit that authorises "40
head" authorises any 40 head, which is to say it authorises laundering: the animals that arrive
need not be the animals that were cleared. A permit that enumerates `national_id`s can be checked
against the truck at a roadblock, one ear tag at a time, by an officer with a phone and no
training. This is the property that makes the permit an actual control rather than a receipt, and
it is why the animal list is `required` with `minItems: 1` rather than optional.

**Access.** A `404` — not a `403` — for a permit belonging to another operator. A `403` confirms
the reference exists, which leaks the shape of other operators' trade to anyone willing to
enumerate.

**The enum fix.** `MovementAck.status` is widened to the same lifecycle enum so that
`/v1/movements/list?status=approved` can return what it says it can (§1). This is the one change
here that touches an existing schema. It is **additive for readers** — no value is removed or
renamed, and a client that only ever handled `lodged | blocked` keeps working — but it makes
previously-impossible responses possible, so it needs the minor bump and an integrator note. The
alternative, giving the list its own response schema, is cleaner in the abstract and worse in
practice: two nearly-identical schemas that will drift.

## 4. Evidence of approval is a Certificate, not a status field

A `status: approved` in a JSON body is not evidence. It is unsigned, unverifiable offline,
trivially forged in a screenshot, and meaningless to a border officer.

The contract already has the object that *is* evidence. `CertificateRequest.kind` already includes
**`movement_permit`**; `Certificate` already carries `reference`, `signature`, `signing_key_id`,
`verify_token`, `verify_url`, `pdf_url`, `valid_until`, revocation fields, and — under RFC 0001 —
`seal` and `seal_level`.

So:

- On approval the registry issues a `movement_permit` **Certificate** over the permit.
- `MovementPermit.permit_certificate_id` points at it; it is **null until approved**, which makes
  "is this approved?" answerable by the presence of signed evidence rather than by trusting a
  string.
- It is fetched at `GET /v1/certificates/{id}`, verified publicly and unauthenticated at
  `GET /v1/verify/{token}`, revoked through the existing revocation path, and — at RFC 0001
  seal level **LT** — **verified fully offline at a roadblock with no connectivity**, which is
  where movement permits are actually checked.

This is the whole argument for not inventing a third object: every property a permit needs as
evidence already exists, signed and verifiable, on an object the contract already ships. Revoking
a permit becomes certificate revocation, which the contract already models and already
propagates.

## 5. Additive request fields and the two-phase flow

Three optional fields on the existing `Movement` request schema (which is
`additionalProperties: false`, so they must be declared):

```yaml
authorizing_permit_reference:
  type: string
  description: |
    An already-issued permit under which this movement is made. Required inside an area whose
    order carries `movement_by_permit_only`; ignored elsewhere.
cd_certificate_ref:
  type: string
  description: |
    Reference to the cleaning & disinfection certification satisfying a `cd_required` condition.
    A reference only — the C&D checklist itself is farm-app domain (§7).
under_order_id:
  type: string
  description: The RFC 0003 order this movement is made under, where the client knows it.
```

**The two-phase flow inside an affected area.** Outside an affected area, nothing changes: lodge,
and the authority reviews under its normal workflow. Inside one:

1. **Phase 1 — pre-authorization.** The client lodges the intended movement. The registry sees
   the origin or destination is under an order with `movement_by_permit_only` and no
   `authorizing_permit_reference` was supplied, and refuses with `409` and the new code
   `permit_required`. The client's user journey is now "apply for a permit", not "retry".
2. **Phase 2 — movement under the permit.** Once the authority has issued a permit, the client
   lodges again citing `authorizing_permit_reference` (and, where relevant,
   `cd_certificate_ref`). The registry validates the citation against the live permit — status,
   window, and that the animals on the truck are the animals on the permit — and accepts.

A client may then present or print the movement **only** once
`GET /v1/movements/{ref}.permit_certificate_id` resolves to an issued certificate. This is the
same discipline `3b8e917` wrote into the integration guide for the not-configured state: a client
"must not present, approve, complete, or print a regulated movement as a national permit" on its
own authority.

### The new error code

```yaml
code: permit_required        # HTTP 409
```

It must be distinct from `zone_blocked`, because they mean opposite things to the user:

| Code | Meaning | What the client should show |
|---|---|---|
| `zone_blocked` | This movement is **not allowed**, by anyone, now. | A hard stop. Not retryable. |
| `permit_required` | This movement **is allowed** — but not without a permit you do not have. | A route into applying for one. |

Collapsing them into one code tells a keeper their legitimate, permittable movement is forbidden,
which is both wrong and the kind of wrongness that drives people to move stock without telling
anyone.

## 6. Versioning impact

All additive within `/v1` (CONTRIBUTING.md "Change policy"); no `/vN` required.

| Spec | From | To | What lands |
|---|---|---|---|
| `openapi.yaml` (client) | 2.1.0 | **2.2.0** | `GET /v1/movements/{permit_reference}`; `MovementPermit` schema; `Movement` gains `authorizing_permit_reference`, `cd_certificate_ref`, `under_order_id`; `MovementAck.status` enum widened (§3); error code `permit_required` |
| `openapi-admin.yaml` | 1.5.0-draft | **1.6.0-draft** | permit issuance emits a `movement_permit` Certificate on `approve`; permit conditions authorable on the existing `/admin/movements/{ref}/{action}` surface |

The `MovementAck.status` widening is the one item that is not purely additive in effect, and it is
a **fix** — it makes the contract self-consistent for the first time since 2026-07-15. It should
still be called out to integrators, because a client that exhaustively switched on `lodged |
blocked` will now meet values it has never seen.

Cross-repo seam-pin obligation for this RFC: `permit-condition-codes` (shared with RFC 0003) must
be pinned in FuroTrack's and Dzinza's standards registers in the same change window.
`standards/vocabulary.v1.json` needs **no** edit.

## 7. What stays OUT of the registry

The registry records the **authority to move** and the **fact of the movement**. Everything about
*executing* the movement belongs to the farm app or the transporter's system:

- **Route planning and optimisation**, waypoints, ETA calculation.
- **Truck telemetry** — GPS breadcrumb streams, fuel, driver hours. The permit carries the vehicle
  registration; the registry is not a fleet-tracking system.
- **Loading-ramp and welfare checklists**, crate density, water stops.
- **Cleaning & disinfection checklists** — the steps, products, photos and sign-off. The contract
  carries `cd_required` as a condition and `cd_certificate_ref` as a **reference**; the artefact
  lives in the farm app (this is the same line RFC 0003 §9 draws).
- **Transport booking, haulier rates, driver rosters.**

## 8. Conformance cases to add

1. `GET /v1/movements/{ref}` for a permit the calling key lodged returns a `MovementPermit` whose
   `permit_reference` matches.
2. Unknown reference → `404`. **Another operator's** reference → `404`, never `403` (§3).
3. A **lodged** permit's view has `permit_certificate_id: null` — approval is not implied by
   existence.
4. Once approved, `permit_certificate_id` resolves via `GET /v1/certificates/{id}`, and that
   certificate's `verify_token` verifies at the public, unauthenticated `GET /v1/verify/{token}`.
5. Revoking that certificate is reflected in the permit view — a revoked permit does not read as
   good.
6. **The regression case for §1:** `GET /v1/movements/list?status=approved` returns items whose
   `status` is `approved`. Against today's contract this is unsatisfiable; it must fail before the
   enum widening and pass after, which is what makes it a real test rather than decoration.
7. `POST /v1/movements` from within an area whose order carries `movement_by_permit_only`, with no
   `authorizing_permit_reference`, returns `409` with `code: permit_required` — and specifically
   **not** `zone_blocked` (§5).
8. The same request **with** a valid `authorizing_permit_reference` is accepted.
9. An `authorizing_permit_reference` that is expired, rejected, or names different animals than
   the consignment is refused.
10. Idempotency is preserved end to end: re-lodging with the same `Idempotency-Key` returns the
    original `permit_reference` and does not create a second permit.
11. `animals` on a `MovementPermit` is never empty (`minItems: 1`), including for a
    single-animal movement.

## 9. Open questions for ratification

1. **Should `permit_reference` be opaque?** It is currently readable and, in the example
   (`MVP-2026-00477`), sequential — which leaks national movement volume to anyone holding two
   references. Opaque references cost nothing and close that.
2. **Is the animal list on the permit, or derived from the lodgement?** Stored on the permit, it
   is what was *authorised* and cannot drift. Derived, it always matches the movement but can be
   changed after approval. This RFC proposes stored; the committee should confirm, because it
   decides what a roadblock check actually means.
3. **Permit transferability and amendment.** May a permit be amended after issue (a truck breaks
   down; a different vehicle goes), or must it be revoked and reissued? Reissue is cleaner and
   slower, and speed is why people move stock unpermitted.
4. **Retention.** How long is a permit view readable after `completed`? Traceability wants years;
   data minimisation under [Chapter 12:07] wants a stated period.
5. **Is `cd_certificate_ref` a `Certificate.id` or a free-text external reference?** A
   `Certificate` is verifiable; a free reference is merely asserted. Verifiability argues for the
   former, and the practical availability of C&D certification in the field argues for the latter.
6. **Offline verification depth.** RFC 0001 level **LT** lets a roadblock verify a permit with no
   connectivity — but not that it was *revoked* five minutes ago. What revocation latency is
   acceptable at a border post, and does that require a short `valid_until` on movement permits
   specifically?
7. **Which authority issues** inside an area under another authority's order — the issuing
   officer of the order, or the district of origin? A control question whose answer the audit
   fields must be able to express.

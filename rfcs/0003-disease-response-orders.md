<!--
SPDX-FileCopyrightText: 2026 The LITS steward
SPDX-License-Identifier: Apache-2.0
-->
# RFC 0003 — Disease response orders (quarantine, standstill, trace flags)

- **Status:** **Accepted 2026-08-16** by the steward (Rodrick Makore). This is a
  sovereign-impacting RFC — it touches **zone authority**, the **two-plane split**, and
  **personal data**, because a flag on an animal is attributable to its keeper — so
  [GOVERNANCE.md](../GOVERNANCE.md) §4 assigns it to the joint steering committee. **That
  committee does not exist yet**: §2 constitutes it *on designation*, and until then the steward
  holds the decision rights. Acceptance is therefore recorded as a **pre-designation steward
  decision**, and the committee, once constituted, may revisit it. Accepting the RFC ratifies the
  design; the contract surface below is **not yet implemented** — see
  [../docs/roadmap.md](../docs/roadmap.md) for the sequence and
  [../CHANGELOG.md](../CHANGELOG.md) for what has actually landed.
- **Affects:** `openapi.yaml` (client) 2.0.0 → 2.1.0, `openapi-admin.yaml` 1.4.0-draft →
  1.5.0-draft.
- **Backwards compatibility:** Additive only, within `/v1`. No field is removed, renamed or made
  required. One new enum value is added to an existing field (`Zone.zone_type`) — see
  §4 for why that is the safest available shape and what it costs.
- **Depends on:** nothing. **Depended on by:** RFC 0004 (a movement issued *under* an order),
  and the biosecurity-attestation work (which section-scoped quarantine needs — see §5).

> **Honesty note.** Every statutory fact in this document is **TO-VERIFY** with the competent
> authority, in the same discipline `profiles/mz` uses. Nothing here asserts what any
> jurisdiction's law currently says; the whole point of the design is that the contract does not
> need to know. Where a specific instrument is named it is named as a thing to check, not as a
> thing established.

---

## 1. The problem

The contract can already record that an animal is **sick** (`POST /v1/disease-cases`,
`POST /v1/lab-results`) and that an **area** is restricted (`GET /v1/zones`). It has no way to
carry the thing that actually sits between those two facts and stops a truck: the **order** — the
act of authority that quarantines a holding, or stands the country still.

Today that decision exists in two places, neither of which a client can read:

1. a paper notice served on the keeper, and
2. if the officer thinks to do it, a zone.

So a farm app whose keeper is under quarantine will cheerfully lodge a movement, show the keeper
a permit reference, and let the stock leave. The registry knows the holding is closed. The
contract never told anyone. That is the failure mode this RFC exists to remove, and it is the
same class of defect the standard has been careful about elsewhere: **the authority's decision
must be readable by the people it binds.**

There is a second, sharper version of the problem. A **standstill** — the national "nothing
moves" declaration made in the first hours of an FMD outbreak — is worth almost nothing if
enforcing it requires every integrator to ship a client update first. Outbreak response is
measured in hours; a coordinated release across every accredited vendor is measured in weeks.
Any design that requires client code to change before a standstill bites has failed at the one
moment it was built for.

## 2. Orders are authored on the admin plane and read as a delta

**Authoring.** An order is an act of the State. A client must never create one. This is the
two-plane split (GOVERNANCE.md §4, `CONTRIBUTING.md` "Two specs") applied without exception:

```
POST   /admin/quarantine-orders                      → QuarantineOrder   (draft)
POST   /admin/quarantine-orders/{order_id}/{action}  → QuarantineOrder
GET    /admin/quarantine-orders                      → [QuarantineOrder] (incl. drafts)
GET    /admin/quarantine-orders/{order_id}           → QuarantineOrder
```

`action` is one of `activate | suspend | resume | extend | lift | revoke`, validated against the
order's current state. This deliberately mirrors `POST /admin/movements/{ref}/{action}` — the
control plane already has exactly one idiom for "advance a regulated object through its
lifecycle", and a second idiom would be a new thing for an Admin Portal to learn for no gain.
Scope: `orders:write` for authoring and transitions, `orders:read` for the admin reads.

**Reading.** Clients read a **versioned delta**, mirroring `/zones` field for field:

```
GET /v1/quarantine-orders?since_version=&country_code=&limit=   → QuarantineOrderDelta
```

Returns orders whose `order_version` is greater than `since_version`, plus the current
`server_version`, which the client persists and passes back. This is not a new invention; it is
the shape `/zones` already uses and that every deployed consumer already has code for
(`fmd_zone_sync`). It is chosen for the same reason `/zones` chose it: the consuming device is a
phone in a district with intermittent connectivity, it must sync a small delta when it can and
then **enforce offline**, and a monotonic integer is the only cursor that survives that
honestly.

A **lifted order remains in the delta** with `status: lifted` rather than disappearing from it.
A feed that answers "what changed" by omission cannot tell a client the difference between
"lifted" and "you have not synced recently", and the client would keep enforcing a lifted order
forever. Retraction must be a positive statement.

## 3. The contract carries no jurisdiction's arithmetic

This is the load-bearing design decision, and the one most likely to be argued about.

It is tempting to put the periods in the contract — a quarantine lasts *n* days, the slaughter
window opens on day *m*. **The contract must not.** Those numbers differ between Zimbabwe,
Mozambique, Malawi and South Africa; they differ by disease; they change by gazette without
warning; and hard-coding any one country's numbers into an open standard would quietly make the
standard that country's, which is precisely the vendor-neutrality property GOVERNANCE.md §1 and
CONTRIBUTING.md exist to protect. A national instance would then have to fork the standard to
obey its own law — the exact outcome the whole project is arranged to prevent.

So the contract carries **dates and their meaning, never the rule that produced them**:

```yaml
milestones:
  type: array
  items:
    type: object
    required: [code, date]
    properties:
      code:
        type: string
        enum: [day_zero, slaughter_window_opens, slaughter_window_closes, review_due, lift_eligible]
      date: { type: string, format: date }
      note: { type: string }
```

The registry computes these dates under its own territory's profile; the client renders and acts
on them without knowing the arithmetic. A client shows "review due 12 March" because the
registry said so — not because it re-derived it and got a different answer from a stale copy of
the rules.

**Each profile states which milestones its law requires**, and how they are derived. That is the
job `profiles/<cc>/legal-basis-and-mandate.md` already does for mandate and numbering, extended
to response timelines. A profile that requires a milestone the vocabulary lacks is the trigger
to extend the vocabulary — deliberately, once, for everyone — rather than to add a bespoke field
for one country.

The milestone codes are a **pinned vocabulary** in the same sense as the standards register's
seam pins: FuroTrack and Dzinza must carry the identical list, and drift is a conformance
failure, not a difference of opinion.

## 4. Conditions are codes, and a standstill is projected into the zone feed

### 4.1 Conditions

What an order *requires* must be machine-readable, or a client can only display it and hope:

```yaml
conditions:
  type: array
  items:
    type: object
    required: [code]
    properties:
      code:
        type: string
        enum:
          - no_movement_on_off        # nothing enters, nothing leaves
          - movement_by_permit_only   # movement allowed only under an issued permit (RFC 0004)
          - cd_required               # cleaning & disinfection required before release
          - sampling_required         # surveillance sampling required before lift
          - section_isolation_granted # a declared section is isolated from the rest (see §5)
      note: { type: string, description: Human context; never the machine meaning. }
```

**Unknown condition codes must fail closed.** CONTRIBUTING.md's change policy says a new enum
value is additive because "clients may ignore" it. For a *restriction* vocabulary that rule is
inverted and dangerous: a client that ignores a condition it does not recognise permits a
movement the authority forbade. A client encountering an unknown `code` MUST therefore treat the
order as at least as restrictive as `no_movement_on_off`.

That has a consequence the steering committee should accept explicitly rather than discover
later: **adding a condition code is not a free additive change.** It changes behaviour at
already-deployed clients, from "allowed" to "blocked", on their next sync. It needs a minor
version bump and integrator notice, and it is safe only in that direction. Failing closed is the
right default for an animal-health restriction — the cost of a wrongly-blocked movement is a
delayed truck; the cost of a wrongly-permitted one is the disease leaving the cordon — but it
should be a decision on the record, not an accident. This is flagged again in §9.

### 4.2 Standstill projects into `/zones`

A standstill order is, in its effect, a movement restriction over an area for a period. The zone
feed **already** carries exactly that, and every deployed client already enforces it:
`Zone.movement_restriction` is `none | restricted | blocked`, and clients gate movements on it
today.

So: an active standstill order is **projected** into the existing `/v1/zones` feed as a zone with
a new additive `zone_type: standstill` and `movement_restriction: blocked`, carrying the
territory the order covers, with `effective_from` / `effective_until` from the order.

The payoff is the answer to §1's second problem: **an already-deployed client enforces a national
standstill with zero client changes**, on its next zone sync, because it is reading a field it
has always read. No release train, no vendor coordination, no window in which half the country's
apps are enforcing and half are not.

Three properties of the projection matter and should be pinned:

- **The order is the record; the zone is derived.** The zone exists because the order does. It is
  a view, not a second source of truth, and it is never edited through `/admin/zones`.
- **Lifting the order retracts the zone** — sets `effective_until` and bumps `zone_version`, so
  the retraction propagates by the same mechanism as the declaration. An enforcement that cannot
  be switched off as fast as it was switched on is not usable in an outbreak.
- **`projected_zone_code` on the order names the zone**, so a client that reads both feeds can
  join them and avoid double-counting one restriction as two.

**The honest cost.** `zone_type` is an enum, and a client that switches on it exhaustively — with
no default branch — could break on an unrecognised value. That is a real risk and it should be
stated rather than glossed. It is judged acceptable because the load-bearing field for
enforcement is `movement_restriction`, which is unchanged and whose values are unchanged;
`zone_type` is descriptive, used for labelling and colour. A client that blocks on
`movement_restriction: blocked` — which is what the integration guide tells clients to do — is
unaffected. The conformance suite should nonetheless add a case asserting that a client tolerates
an unknown `zone_type` (§8).

## 5. Section-scoped quarantine requires a declared section

An order may be scoped to a **section** of a holding rather than the whole of it — the
difference between closing one shed and closing a farm, which for a large feedlot is the
difference between a manageable event and an insolvency.

But you cannot quarantine the north shed of a holding that has never told the registry it has
sheds. Section scope is therefore **valid only where the holding has an accepted biosecurity
attestation declaring its sections**; otherwise the authoring call returns `422` with
`code: sections_not_declared`. The registry refuses to issue an order it cannot describe rather
than issuing a vague one — the same instinct as refusing to bill an unmeasurable book.

This is what sequences the biosecurity attestation immediately after this RFC in the roadmap:
until it exists, `scope: section` is specified but not issuable, and that limit should be
visible in the contract rather than hidden in an implementation.

> **TO-VERIFY.** Whether a competent authority will accept section-scoped quarantine at all, and
> under what evidentiary standard, is a question for each territory's veterinary authority. The
> WOAH Terrestrial Code's biosecurity chapter (Ch. 4.X) — the natural reference for
> compartment/section standards — was **proposed for adoption at the May 2026 General Session;
> the final adopted text is unverified at the time of writing** and must be checked before any
> profile cites it as settled.

## 6. Trace flags are registry-applied, never client-applied

Some facts follow an animal for the rest of its life. An animal that has been serologically
positive for a disease may never be eligible for certain markets again, whatever a later test
says.

```yaml
TraceFlag:
  type: object
  required: [code, applied_at]
  properties:
    code:
      type: string
      enum: [sero_positive_lifelong, quarantine_history]
    applied_at: { type: string, format: date-time }
    expires_at:
      type: [string, 'null']
      format: date-time
      description: Null means lifelong — the flag never expires and is not re-evaluated.
    order_id:    { type: [string, 'null'], description: The order under which the flag was applied. }
    disease:     { type: [string, 'null'] }
    applied_by:  { type: string, description: The issuing authority. Never an integrator key. }
```

Read additively on `GET /v1/animals/{national_id}` (`trace_flags: [TraceFlag]`) and on
`GET /v1/animals/{id}/health` (elevated `health:read`). **Written only on the admin plane**:
`POST /admin/animals/{national_id}/trace-flags` and `.../trace-flags/{code}/clear`.

There is no client write path, and that is the point rather than an oversight. A lifelong mark on
a keeper's animal is a determination with real economic consequence for a named person; it is an
act of authority that must carry an officer, a legal basis and an audit entry, and it must be
appealable. A farm app that could stamp it would be exercising authority it does not have, and
the audit trail would record a vendor key rather than a decision-maker. `null` expiry meaning
*lifelong* is stated explicitly in the schema because the alternative reading — "not yet set" —
would be catastrophic in exactly the wrong direction.

This is the part of the RFC that most clearly touches **personal data** under the Cyber & Data
Protection Act [Chapter 12:07] (POTRAZ; GOVERNANCE.md §6), which is one of the reasons the whole
document is RFC-class.

## 7. The verbal order comes first

In the field, an order is made by a veterinary officer **telling the keeper**, at the gate, that
nothing leaves. The written instrument is served afterwards — sometimes days afterwards, and in
an outbreak, reliably afterwards.

A contract that models only the written instrument is therefore blind during precisely the window
that decides whether the outbreak is contained: the first forty-eight hours. So the order carries
both timestamps, both nullable:

```yaml
declared_verbally_at:    { type: [string, 'null'], format: date-time }
confirmed_in_writing_at: { type: [string, 'null'], format: date-time }
```

An order is **enforceable from `declared_verbally_at`** where the territory's law recognises a
verbal order, with `confirmed_in_writing_at` following. An order with neither timestamp cannot be
`active`.

> **TO-VERIFY — Gazette 54972.** Whether a verbally-declared order is enforceable before written
> confirmation, and how long the confirmation may lag, is a statutory question. It has been
> raised against **Gazette 54972**, and that citation is **unverified**: it must be read and
> confirmed (or replaced) before any profile relies on it, and the answer may differ per
> territory. If some territory requires writing first, that territory's profile says so and its
> registry refuses to activate on a verbal declaration alone — the contract carries both fields
> either way and does not decide.

## 8. Schema sketch — `QuarantineOrder`

```yaml
QuarantineOrder:
  type: object
  required: [order_id, order_type, status, scope, subject_id, order_version, country_code, effective_from]
  properties:
    order_id:      { type: string, examples: [ZW-QO-2026-000412] }
    order_type:    { type: string, enum: [quarantine, standstill] }
    status:        { type: string, enum: [draft, active, suspended, lifted, revoked, expired] }
    scope:         { type: string, enum: [holding, section, animal, area] }
    subject_id:
      type: string
      description: holding_id | section_id | national_id | zone_code, per `scope`.
    section_id:    { type: [string, 'null'], description: Required when scope is section (see §5). }
    disease:       { type: string, description: WOAH vocabulary, as DiseaseCaseReport.disease. }
    disease_case_id: { type: [string, 'null'], description: The case that prompted the order, if any. }
    order_version: { type: integer, format: int64, description: Monotonic; the delta cursor. }
    country_code:  { type: string }
    declared_verbally_at:    { type: [string, 'null'], format: date-time }   # §7
    confirmed_in_writing_at: { type: [string, 'null'], format: date-time }   # §7
    effective_from:  { type: string, format: date-time }
    effective_until: { type: [string, 'null'], format: date-time }
    milestones:  { $ref: '#/components/schemas/OrderMilestone' }             # §3, array
    conditions:  { $ref: '#/components/schemas/OrderCondition' }             # §4.1, array
    issuing_authority:  { type: string }
    issuing_officer_ref: { type: string, description: Officer identifier; not a personal name. }
    legal_basis: { type: string, description: Profile-supplied citation for the power exercised. }
    gazette_reference: { type: [string, 'null'] }
    projected_zone_code: { type: [string, 'null'], description: Zone this order projects into (§4.2). }
    lifted_at:   { type: [string, 'null'], format: date-time }
    lift_reason: { type: [string, 'null'] }

QuarantineOrderDelta:
  type: object
  required: [server_version, orders]
  properties:
    server_version:  { type: integer, format: int64 }
    orders_returned: { type: integer }
    orders:          { type: array, items: { $ref: '#/components/schemas/QuarantineOrder' } }
```

`issuing_officer_ref` is an identifier rather than a name, deliberately: the audit trail needs to
resolve to a person, but the *client-plane* feed — readable by every accredited integrator —
does not need to publish which named official closed which named farm.

## 9. What stays OUT of the registry

The registry is the record of **authority acts and regulated facts**. It is not a farm-management
database, and the line matters commercially as well as architecturally: every field that a
competing vendor does not need in order to comply is a field that makes the standard heavier,
more opinionated, and less neutral — and vendor-neutrality is non-regressable
(CONTRIBUTING.md).

Staying out, and belonging to the farm app:

- **Cleaning & disinfection checklists** — the steps, the products, the operator, the photos. The
  registry carries the *condition* `cd_required` and the *fact* that it was certified complete.
- **Isolation-pen management** — which pen, which animals, feed and water routines, stocking.
- **Biosecurity plan documents** — the plan itself, its revisions, staff sign-off, training
  records. The registry carries the *attestation* that an accepted plan exists (and, for §5, the
  sections it declares) — not the document.
- **Fridge and cold-chain telemetry** — vaccine fridge temperature logs, sensor streams, alarms.
  This is high-volume operational data whose home is the farm app; the registry's interest is
  narrowly the vaccination record (see the roadmap's vaccination enrichment step, which adds a
  `cold_chain_ok` assertion and an evidence *reference*, never the telemetry).
- **Staff rosters, on-call rotas, notification preferences.**

The test to apply to any proposed field: *would a different vendor, in a different country, need
this in order to comply with an order?* If not, it belongs in the farm app.

## 10. Versioning impact

All changes are **additive within `/v1`** — no new `/vN` is required (CONTRIBUTING.md
"Change policy").

| Spec | From | To | What lands |
|---|---|---|---|
| `openapi.yaml` (client) | 2.0.0 | **2.1.0** | `GET /v1/quarantine-orders`; `QuarantineOrder`, `QuarantineOrderDelta`, `OrderMilestone`, `OrderCondition`, `TraceFlag`; `Zone.zone_type` gains `standstill`; `Animal`/`AnimalHealthStatus` gain optional `trace_flags` |
| `openapi-admin.yaml` | 1.4.0-draft | **1.5.0-draft** | `/admin/quarantine-orders` (+ `/{id}`, `/{id}/{action}`); `/admin/animals/{national_id}/trace-flags` (+ `/{code}/clear`); scopes `orders:read`, `orders:write` |

Version numbers assume this RFC lands first in the roadmap's order; they are relative to that
sequence, not absolute reservations.

Two things in this "additive" set are additive in form but not in behaviour, and are called out
so ratification is informed:

1. **A new `conditions[].code`** changes deployed clients from permitting to blocking (§4.1).
2. **`Zone.zone_type: standstill`** is safe for clients that gate on `movement_restriction`, and
   unsafe for a client that switches exhaustively on `zone_type` (§4.2).

Also required in the same change window, per the cross-repo seam-pin obligation: the new pins
`order-status`, `permit-condition-codes` and `trace-flag-codes` must be entered in FuroTrack's
and Dzinza's standards registers. `standards/vocabulary.v1.json` itself needs **no** edit — its
existing enums suffice — and if it ever does, that edit lands byte-identically in all four repos
at once or in none.

## 11. Conformance cases to add

Contract-level (`scripts/validate.py`) and live (`conformance/`):

1. `GET /v1/quarantine-orders?since_version=N` returns only orders with `order_version > N`, and
   a `server_version` not less than the highest returned.
2. Replaying the same `since_version` twice returns the same set or a superset — never a gap.
3. A **lifted** order still appears in the delta with `status: lifted` (§2).
4. An active `standstill` order appears in `GET /v1/zones` as a zone with `zone_type: standstill`
   **and** `movement_restriction: blocked`, whose `zone_code` equals the order's
   `projected_zone_code`.
5. Lifting that order bumps the projected zone's `zone_version` and sets `effective_until` (§4.2).
6. A client tolerates an **unknown `zone_type`** without failing, provided
   `movement_restriction` is honoured (the §4.2 cost, made testable).
7. A client treats an **unknown `conditions[].code` as blocking** (§4.1). This asserts client
   behaviour, so it belongs in the client half of the conformance suite.
8. `POST /v1/movements` for an animal at a holding under an active order carrying
   `no_movement_on_off` is refused `409`.
9. Authoring `scope: section` against a holding with no accepted biosecurity attestation returns
   `422 sections_not_declared` (§5).
10. There is **no client path** by which a trace flag can be written; an integrator key attempting
    one gets `404`/`405`, and the animal's `trace_flags` are unchanged (§6).
11. A `TraceFlag` with `expires_at: null` is still returned, and still enforced, after any
    plausible expiry horizon (the "null means lifelong" assertion, made non-vacuous).
12. An order with neither `declared_verbally_at` nor `confirmed_in_writing_at` cannot reach
    `active` (§7).

## 12. Open questions for ratification

1. **Milestone vocabulary completeness.** Are `day_zero`, `slaughter_window_opens`,
   `slaughter_window_closes`, `review_due`, `lift_eligible` sufficient across the territories in
   scope, or does a profile already need a sixth? Getting this wrong is cheap to fix now and
   expensive after integrators ship.
2. **Does `scope: area` duplicate a zone?** An area-scoped order and a projected standstill zone
   may be two spellings of one thing. Consider dropping `area` and requiring area-wide orders to
   be `standstill`.
3. **Should the standstill projection be opt-in per territory?** It is proposed as always-on
   because that is what makes it work without client changes; a territory that wants orders and
   zones kept strictly separate would need a switch, and a switch weakens the guarantee.
4. **Fail-closed vs the additive-enum policy** (§4.1) — the committee should ratify the exception
   explicitly, or reject it and accept that unknown conditions are ignored.
5. **Trace-flag retention and data protection.** A lifelong flag is, by construction, indefinite
   retention of a fact about a named keeper's property. How does that sit with data-minimisation
   under [Chapter 12:07]? Is there an appeal or erasure path, and who decides it?
6. **Who may lift?** Must the lifting officer be the issuing officer, the same district, or any
   officer with `orders:write`? This is a control question, not a schema question, but the
   contract's audit fields must be able to express the answer.
7. **Verbal orders** — Gazette 54972 is **TO-VERIFY** (§7), and the answer may be per-territory.
8. **WOAH Terrestrial Code Ch. 4.X** (biosecurity) was **proposed for adoption at the May 2026
   General Session; the adopted text is unverified.** Any profile or conformance case that cites
   it must mark it accordingly until the adopted text is in hand.

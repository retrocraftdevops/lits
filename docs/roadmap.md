# LITS Contract Roadmap

What is planned for the LITS contract, in the order it is planned, and why that order.

> **Status: DRAFT planning document.** This is the forward-looking companion to
> [CHANGELOG.md](../CHANGELOG.md), which records only what has already landed. Nothing here is
> committed contract surface: a step is a proposal until it ships and appears in the changelog,
> and every RFC-class step is a proposal until the steering committee ratifies it
> ([GOVERNANCE.md](../GOVERNANCE.md) §2, §4).
>
> **Every statutory fact referenced below is TO-VERIFY**, in the discipline `profiles/mz` uses.
> The **WOAH Terrestrial Code biosecurity chapter (Ch. 4.X)** was **proposed for adoption at the
> May 2026 General Session; the adopted text is unverified** and must be checked before any step
> or profile cites it as settled.

---

## The sequence

| # | Step | Class | Spec impact | State |
|---|---|---|---|---|
| 0 | [Contract hygiene](#0-contract-hygiene) | fix | none (parser-level) | **landed** (`b57d7fa`); follow-up open |
| 1 | [Vaccination enrichment](#1-vaccination-enrichment) | additive | client → 2.1.0 | next |
| 2 | [RFC 0003 — disease response orders](#2-rfc-0003--disease-response-orders) | RFC | client 2.1.0 → 2.2.0, admin 1.4.0-draft → 1.5.0-draft | draft |
| 3 | [RFC 0004 — movement pre-authorization](#3-rfc-0004--movement-pre-authorization) | RFC | client 2.2.0 → 2.3.0, admin 1.5.0-draft → 1.6.0-draft | draft |
| 4 | [Biosecurity attestation](#4-biosecurity-attestation) | additive | client + admin | not drafted |
| 5 | [Sampling](#5-sampling) | additive | client + admin | not drafted |
| 6 | [Event feed](#6-event-feed) | additive | client | drafted in RFC 0005 §2 |
| 7 | [RFC 0005 — subscriptions](#7-rfc-0005--webhook-subscriptions) | RFC | client + admin | draft |
| 8 | [`profiles/za`](#8-profilesza-south-africa) | profile | none | **approved**, sequenced last |

Version numbers are **relative to this sequence**, not absolute reservations. Land the steps out
of order and the numbers shift; the ordering constraints in each section do not.

Everything in steps 1–7 is **additive within `/v1`**. No step here requires a `/v2`
([CONTRIBUTING.md](../CONTRIBUTING.md), "Change policy"). Two items are additive in form but not
in effect and are flagged where they occur (RFC 0003 §4.1, §4.2; RFC 0004 §3).

---

## 0. Contract hygiene

**Landed** in `b57d7fa`. Four duplicate or undeclared YAML keys the parser was silently
discarding: `/authorized-keepers` and `/keepers/resolve` defined twice in `openapi.yaml`, the
undeclared tags `campaigns` and `trust-admin`, and duplicated `seamPin` / `notes` on the
`eudr.plot-geometry` control. Detail in the [changelog](../CHANGELOG.md).

It is step 0 because two of the four were **hiding other problems**, and you cannot sequence work
against a signal you cannot read.

### Follow-up still open

Three things that step 0 exposed rather than fixed. None blocks step 1, and all three should land
before the contract is presented as ratifiable:

1. **Neither gate detects the class of defect step 0 fixed.** `scripts/validate.py` does not
   check for duplicate YAML mapping keys or undeclared tags; `@redocly/cli`'s recommended
   ruleset does not enable `operation-tag-defined` and does not lint
   `standards/registry.yaml` at all. Both were proven blind by breaking them on purpose. A fix
   that no gate can hold does not stay fixed — teaching `validate.py` to reject a duplicate
   mapping key and an undeclared tag is a few lines and keeps it fixed.
2. **104 pre-existing lint errors are now visible.** The duplicate path key made `@redocly/cli`
   abort with `duplicated mapping key` before validating *either* spec, so the CI lint step had
   stopped reporting anything at all. With it removed, the run completes and surfaces 101 uses of
   the OpenAPI 3.0 `nullable` keyword in `openapi-admin.yaml` (invalid in 3.1, where the form is
   `type: [string, 'null']` — which `openapi.yaml` already uses correctly) and 3 flow-scalar
   descriptions in `openapi.yaml` where an unquoted `,` splits the mapping. These were **not**
   introduced by step 0 and are deliberately left out of it: replacing `nullable` is a
   schema-semantics change across ~101 sites, not hygiene.
3. **`scripts/check-standards-parity.sh` does not exist.** `standards/README.md` §Verify names it
   as the command that "hashes the vocabulary + compares pinned seams across repos", and it is
   absent from this repo, with no parity step in
   [`.github/workflows/validate.yml`](../.github/workflows/validate.yml). The cross-repo seam
   obligation is therefore enforced **in prose only** here — which is precisely the failure
   `standards/README.md` says the register exists to end ("pinned by hand with drift *declared* a
   conformance failure but never *detected*"). This matters most at step 2, which adds three new
   pins.

---

## 1. Vaccination enrichment

**The smallest useful step in the list, and the most urgent** — flagged `RVS-FMD-urgent`. It adds
no object, no endpoint and no plane; it adds optional fields to a schema that already exists, so
it can land while the RFCs above it are still being argued.

`Vaccination` today carries `national_id`, `disease`, `vaccine_name`, `lot_number`, `dose`,
`administered_at`, `next_due_at`, `administered_by`, `campaign_id`. It already has
**`lot_number`** — which is the useful half of a vaccine recall and the useless half of a cold-chain
question. Proposed additions, all optional:

| Field | Type | Why |
|---|---|---|
| `lot_expiry` | `date` | A lot number identifies the batch; only the expiry says whether the dose was viable when it went in. Recall and coverage-audit both need it, and it is on the vial. |
| `cold_chain_ok` | `boolean` | The field officer's assertion that the cold chain held. An FMD vaccine that broke cold chain was an injection, not an immunisation, and coverage computed without this over-reports protection — the number a response is planned against. |
| `cold_chain_evidence_ref` | `string` | A **reference** to the evidence, never the evidence. Fridge telemetry stays in the farm app (RFC 0003 §9). |
| `dual_id_confirmed` | `boolean` | That both the visual tag and the electronic ID were read at the point of vaccination. Without it a vaccination binds to whichever identifier was convenient, and the record cannot be reconciled later. |
| `holding_id` | `string` | Where it happened. Coverage is computed per holding and per zone; today it can only be derived by joining back through the animal's current holding, which is wrong for any animal that has since moved. |
| `zone_code` | `string` | The zone at the time of vaccination. Same reason: zones change, and ring-vaccination coverage is a question about the zone as it was. |

`holding_id` and `zone_code` are the two that repay the effort immediately: they turn campaign
coverage from a derived, drift-prone join into a recorded fact. `Vaccination` is
`additionalProperties: false`, so each must be declared.

**Ordering:** first, because it is independent of everything below it and urgent on its own terms.
Nothing later depends on it.

**Gate:** `scripts/validate.py` + `@redocly/cli lint`, a `### Added` changelog entry, and an
updated `examples/record-vaccination.json` so the example never drifts from the contract
(CONTRIBUTING.md, quality gate item 3).

---

## 2. RFC 0003 — disease response orders

[rfcs/0003-disease-response-orders.md](../rfcs/0003-disease-response-orders.md). QuarantineOrder +
StandstillOrder + animal trace flags. Orders authored on the admin plane, read by clients as a
versioned delta mirroring `/zones`; no jurisdiction's arithmetic in the contract (pinned
`milestones` and `conditions` vocabularies, each profile stating what its law requires);
standstill projected into the existing zone feed so deployed clients enforce it with **no client
changes**; trace flags registry-applied only.

**Ordering:** before RFC 0004, because a movement issued *under an order* needs orders to exist
(`issued_under_order_id`), and RFC 0004's permit conditions reuse this RFC's
`permit-condition-codes` vocabulary. After step 1, because step 1 is smaller and urgent, and
nothing in it blocks this.

**Leaves a stated gap:** `scope: section` is specified here but not issuable until step 4 — the
contract says so and refuses (`422 sections_not_declared`) rather than issuing a vague order.

---

## 3. RFC 0004 — movement pre-authorization

[rfcs/0004-movement-pre-authorization.md](../rfcs/0004-movement-pre-authorization.md). Completes
the machinery `3b8e917` established rather than revisiting it — clients still only *lodge*. Adds
`GET /v1/movements/{permit_reference}`, the additive request fields
`authorizing_permit_reference` / `cd_certificate_ref` / `under_order_id`, the two-phase flow
inside affected areas, and the error code `permit_required`. Invents **no** third permit object:
evidence of approval is a `movement_permit` Certificate the contract already signs, verifies and
revokes.

**Ordering:** after RFC 0003 (above). It also **fixes a live defect** — `/movements/list` has
accepted `status=approved` since `bd0ee9e` (2026-07-10) while `3b8e917` (2026-07-15) narrowed the
shared `MovementAck.status` to `[lodged, blocked]`, so a conformant server cannot return an
approved permit from the endpoint integrators are told to poll for approvals. If that fix is
wanted sooner than this RFC ratifies, the enum widening can be split out and landed on its own;
it is the only part of RFC 0004 that touches an existing schema.

---

## 4. Biosecurity attestation

Not yet drafted. A holding declares its biosecurity arrangements — including its **sections** —
and the authority accepts or rejects the declaration.

**Ordering:** after RFC 0003, which needs it. RFC 0003 §5 makes section-scoped quarantine valid
*only* where an accepted attestation declares sections, because you cannot quarantine the north
shed of a holding that has never said it has sheds. This step closes the gap RFC 0003 leaves
deliberately open, and it should be drafted with RFC 0003's ratified shape in hand rather than
guessed alongside it.

**Scope discipline:** the registry carries the *attestation* — that an accepted plan exists, the
scheme it was assessed against, its sections, its validity window. The **plan document, the
checklists, the staff training records and the audit photographs stay in the farm app**
(RFC 0003 §9). Adds the seam pin `biosecurity-scheme`.

**TO-VERIFY:** the natural reference for section/compartment standards is the WOAH Terrestrial
Code biosecurity chapter (Ch. 4.X), **proposed for adoption in May 2026, adopted text unverified**.
Do not cite it as settled in this step or in any profile until the text is in hand.

---

## 5. Sampling

Not yet drafted. Surveillance sampling as a first-class record: what was sampled, when, under
whose order, and how the result flows back.

**Ordering:** after step 4. `sampling_required` is one of RFC 0003's condition codes, so the
*obligation* is expressible from step 2; this step makes the *discharge* of that obligation
recordable, which is what a `lift_eligible` milestone actually depends on. It sits after
biosecurity attestation because a sampling plan is described against a holding's declared
structure. It composes with the existing `POST /v1/lab-results`, which already auto-links
positives to open disease cases — sampling is the missing front half of that path, not a
replacement for it.

---

## 6. Event feed

The additive half of RFC 0005 — `GET /v1/events?since_cursor=&types=`, one monotonic loop with a
pinned event-type vocabulary, carrying **pointers and not payloads**
([RFC 0005 §2](../rfcs/0005-event-feed-and-subscriptions.md)).

**Ordering:** after the capabilities that generate the interesting events (steps 2–5), so the
event-type vocabulary is pinned once against real surface rather than extended three times.
Before step 7, without exception — see below.

The existing `/zones` and `/quarantine-orders` deltas are **not** deprecated by this. They are the
offline-first path for a field device on intermittent connectivity, and removing them would be a
breaking change requiring `/v2`.

---

## 7. RFC 0005 — webhook subscriptions

[rfcs/0005-event-feed-and-subscriptions.md](../rfcs/0005-event-feed-and-subscriptions.md) §4.
Integrator-key-scoped subscriptions, HMAC-signed reusing RFC 0002's convention, at-least-once
delivery, retry with auto-disable, operator force-disable on the admin plane. Plus the keeper
alerting surface (`GET /v1/keeper/alerts`).

**Ordering: strictly after step 6, and this one is not negotiable.** The poll feed is the recovery
path for a subscription that lapsed, failed or was auto-disabled. A webhook system shipped without
a catch-up loop is unrecoverable, and its first outage becomes a permanent gap in the consumer's
record with no way to close it short of a full resync.

**SMS/USSD delivery stays out of the contract** — an operator concern, per-territory, a cost
decision, and personal data over a channel the contract cannot secure (RFC 0005 §5).

---

## 8. `profiles/za` (South Africa)

**Approved.** Deliberately sequenced **after RFC 0003 and RFC 0004 have citable shapes** — not
because it is low value, but because a profile's job is to map a jurisdiction's legal basis onto
**real contract surface**, and half of what a South African profile needs to cite does not exist
yet.

A profile written now could describe the mandate and the identifier scheme, and would have to
hand-wave exactly the parts that matter most: which contract object carries a quarantine, which
carries a standstill, which milestones the law requires, what a movement permit is evidence of.
Written after steps 2–3, each of those maps to a named schema, field and endpoint — which is what
makes a profile checkable instead of a description of intent.

**Not written this wave.** When it is, it follows the `profiles/mz` structure — `README.md`,
`legal-basis-and-mandate.md`, a use-case pack — and the same **TO-VERIFY** discipline on every
institutional and statutory fact until confirmed with the South African veterinary authority.

---

## The cross-repo seam-pin obligation

`standards/vocabulary.v1.json` is **byte-identical in four repos** — this one, FuroField,
FuroTrack and Dzinza (`standards/README.md`). A `seamPin` names an interchange vocabulary shared
across them, and drift is a conformance failure rather than a difference of opinion.

The steps above introduce **five new pins**:

| Pin | Introduced by | Pins |
|---|---|---|
| `order-status` | step 2 | the `QuarantineOrder.status` lifecycle |
| `trace-flag-codes` | step 2 | `sero_positive_lifelong`, `quarantine_history` |
| `permit-condition-codes` | steps 2–3 | the `conditions[].code` vocabulary shared by orders and permits |
| `biosecurity-scheme` | step 4 | the scheme a biosecurity attestation was assessed against |
| `event-types` | steps 6–7 | the pinned event-type vocabulary |

**Each must be entered in FuroTrack's and Dzinza's registers in the same change window** as the
LITS step that introduces it. A pin that exists on one side only is not a pin; it is a claim.

**`standards/vocabulary.v1.json` itself needs no edit for any of them.** Its existing enums
(`Status`, `EvidenceTier`, `Family`, `AppliesTo`) are sufficient — a new `seamPin` is a *value*
recorded on a control, not a schema change. This is worth stating plainly because the instinct on
adding a vocabulary is to edit the vocabulary file, and here that instinct is wrong and expensive.

**If the vocabulary ever does need an edit**, it lands **byte-identically in all four repos at
once, or in none** — a backwards-compatible addition bumps the minor version in all four in the
same change; anything that invalidates an existing register is a major version with the same
treatment. Editing it in one repo alone fails that repo's parity test and every other repo's
cross-repo check, which is the design working, not a problem to route around.

⚠️ **Caveat, per step 0's open follow-up:** in *this* repo that parity check has no runnable
script — `scripts/check-standards-parity.sh` is named in `standards/README.md` but is absent, and
CI has no parity step. Until it exists, the obligation above is enforced by discipline, and each
of the five pins should be added to the sibling registers by hand and verified by hand in the same
change window.

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
| 0 | [Contract hygiene](#0-contract-hygiene) + [gate hardening](#0b-gate-hardening--landed) | fix | none (parser-level) | **landed** (`b57d7fa` + gate ×3); 2 follow-ups open |
| 1 | [Vaccination enrichment](#1-vaccination-enrichment) | additive | client 2.0.0 → **2.1.0** | **landed** |
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

### 0b. Gate hardening — landed

`scripts/validate.py` could not detect either class of defect step 0 fixed. Proven blind, not
assumed: a planted third `/keepers/resolve` and a planted undeclared tag both left it reporting
green, and the planted duplicate **silently swallowed real contract surface** on the way through
(unique `$ref`s fell 43 → 42 as the bogus stub overwrote the real definition) while the gate still
printed OK. A gate that cannot see a defect which *deletes contract from the published document*
is not a gate.

Three checks added across two rounds, each proven red-then-green before being trusted:

1. **No duplicated mapping key** in `openapi.yaml`, `openapi-admin.yaml` or
   `standards/registry.yaml`. It runs *first*, because every other check in the gate reads the
   already-deduplicated document and therefore cannot know what YAML threw away. This is the only
   check anywhere that covers `standards/registry.yaml` — `@redocly/cli` does not lint it at all,
   which is why the `eudr.plot-geometry` downgrade justification could vanish unnoticed.
2. **Every operation tag is declared** in its spec's top-level `tags:` list, both specs.
   Redocly's recommended ruleset does not enable `operation-tag-defined`, so this is the only
   place it is checked.
3. **Every `examples/*.json` conforms to the schema it illustrates** — declared type (including
   nullable type arrays), enum membership, required properties and `additionalProperties: false`,
   recursing through internal `$ref`s and array items. This enforces an obligation the repo had
   already committed to in writing (CONTRIBUTING.md's quality gate: examples "never drift from the
   contract") and that nothing checked: the parse step proves only that a file is JSON, so an
   example carrying an undeclared property or a wrong-typed value shipped green. An example with
   **no entry** in the file→schema map fails rather than skipping, so a new example cannot opt
   itself out. All five existing examples conform, so it landed green.

   *Known limit, stated rather than discovered later:* the check enforces
   `additionalProperties: false` only where a schema declares it. All eight top-level request
   schemas do; the nested `MovementSubject` (used by `Movement.animals[]`) does not, so an
   undeclared property inside a movement's animal entry is legal per the contract and is
   correctly not flagged. Whether that omission is deliberate is a question for the steward.

### Follow-up still open

Three things were exposed here; **two remain open**. None blocks the next step, and all should be
resolved before the contract is presented as ratifiable. (A fourth — examples never checked against
their schemas — was closed by the second round of [gate hardening](#0b-gate-hardening--landed).)
Item 3 was closed on 2026-08-16 by a decision from Rodrick as steward: `rfcs/` is Apache-2.0.

**Item 2 was recorded as CLOSED on 2026-08-16 and that was premature — it is re-scoped and
re-opened below.** The decision was made and the script was written, reviewed and proven capable
of failing, all of which stands. What does not stand is the word *enforced*: **nothing runs it.**
Entries are kept rather than deleted, because the reasoning is what stops the questions being
reopened.

1. **104 pre-existing lint errors are now visible.** The duplicate path key made `@redocly/cli`
   abort with `duplicated mapping key` before validating *either* spec, so the CI lint step had
   stopped reporting anything at all. With it removed, the run completes and surfaces 101 uses of
   the OpenAPI 3.0 `nullable` keyword in `openapi-admin.yaml` (invalid in 3.1, where the form is
   `type: [string, 'null']` — which `openapi.yaml` already uses correctly) and 3 flow-scalar
   descriptions in `openapi.yaml` where an unquoted `,` splits the mapping. These were **not**
   introduced by step 0 and are deliberately left out of it: replacing `nullable` is a
   schema-semantics change across ~101 sites, not hygiene.
2. **The parity script EXISTS — in FuroField. This entry was half wrong and the wrong half
   mattered.** Corrected 2026-08-16.

   What was right: there is no such file in **this** repository (`scripts/` contains only
   `validate.py`), `standards/README.md` §Verify cited it as a repo-relative path as though there
   were, and [`.github/workflows/validate.yml`](../.github/workflows/validate.yml) has no parity
   step. The README is now fixed to cite the absolute path, as FuroTrack's copy already did.

   What was wrong: **"the cross-repo seam-pin obligation is enforced by nothing that runs" is not
   true.** `~/projects/FuroField/scripts/check-standards-parity.sh` is real, is wired into
   FuroField's `ci.yml`, and **reads this repository directly** — its own header names the four
   registers including `LITS  standards/registry.yaml`, and it is written to be run from any of the
   four. Run from a clean tree on 2026-08-16 it reported **PASS**: one vocabulary hash
   (`737b5e9f…44e572a4`) across FuroField, furotrack, lits and dzinza, both pinned seams present on
   both sides, `1.0.0` declared everywhere.

   **And the PASS was checked before it was believed.** A green check proves nothing until it is
   known to be capable of going red, so a *copy* of this repo's `standards/vocabulary.v1.json` was
   mutated and the script re-run against it: it named `lits/standards/vocabulary.v1.json`, printed
   expected and found hashes, and exited 1. Nothing in this repository was modified to do it.

   **The residual gap was narrower than this entry claimed.** Detection had
   lived only in a sibling repo's CI, so a drift introduced here was caught only when *FuroField's*
   pipeline ran — a single point of failure for a four-repo obligation, and one whose availability
   history is not spotless. It mattered more from step 2 onward, which introduces five new pins
   (see [the seam-pin obligation](#the-cross-repo-seam-pin-obligation)).

   > **RE-OPENED 2026-08-16 (same day). This entry said CLOSED; the check is landed but NOT
   > ENFORCED, and the difference is the whole point of the entry.** Verified, not inferred:
   >
   > - **Actions is disabled on this repository.** `GET /repos/retrocraftdevops/lits/actions/permissions`
   >   returns `{"enabled": false}`, and the run history is empty — **zero workflow runs, ever**.
   >   A workflow file in the tree is not a gate; nothing has executed it.
   > - **The step is unpushed anyway.** The `validate.yml` revision carrying
   >   `check-standards-parity.py` is on a local commit; `origin/main`'s copy of that file has no
   >   parity step at all. Even with Actions on, the remote has nothing to run.
   > - **The fallback is also down.** The consolation was "FuroField's CI still catches it". It
   >   does not right now: FuroField's last 30 Actions runs are **all `startup_failure` after 0s**,
   >   with no successful run in that window. That is the known org-wide billing outage affecting
   >   these repos, not a fault in FuroField's pipeline — but the effect on this obligation is the
   >   same, and an outage that explains a gap does not close it.
   >
   > **So the honest state: drift in this repo's vocabulary is currently caught by nothing
   > automatic — only by a human running `scripts/check-standards-parity.py`.** That is a weaker
   > position than the pre-decision one this entry set out to improve on, because the earlier
   > entry at least described the enforcement accurately.
   >
   > **What actually closes it** (both, not either): (1) enable GitHub Actions on
   > `retrocraftdevops/lits` — which for this org means the CI outage above being resolved; and
   > (2) push the commits carrying `scripts/check-standards-parity.py` and the `validate.yml`
   > step, so `origin/main` holds a workflow that includes it. **Close it only against a run
   > URL** — a green run of `validate-contract` on `main` with the parity step visible in the log,
   > and, because a check that has never failed is not known to work, a deliberately drifted
   > vocabulary rejected by *that pipeline* rather than by a local shell.

   **Decided by Rodrick, 2026-08-16: yes — this repository owns a parity step of its own.**
   Implemented as `scripts/check-standards-parity.py`, and written into
   [`.github/workflows/validate.yml`](../.github/workflows/validate.yml) alongside
   `scripts/validate.py` — **wiring that is correct and dormant**, per the re-opening above. The
   script itself is finished work; only its automatic invocation is missing.

   Of the three options in the question, the answer was none of them exactly. A **wrapper** needs
   both checkouts on a runner that has one; **vendoring** the FuroField script makes a fourth copy
   of the four-repo topology, which is the drift the program exists to detect; and **centralising**
   was the gap itself. What landed instead splits the work by what each side can actually know:

   - **Here:** the checks this repo can make alone — its `vocabulary.v1.json` against a canonical
     digest recorded in the script, the vocabulary structure `scripts/validate.py` indexes into,
     and `registry.yaml`'s declared repo and version. Sibling checkouts are compared **when they
     happen to be present**, and every one that is not is printed as `NOT COMPARED` and named in
     the summary line, which reads `PASS (SELF-CHECK ONLY)`. An absent sibling never reads as an
     agreeing sibling. `--require-siblings` makes absence a failure for local use.
   - **There:** `~/projects/FuroField/scripts/check-standards-parity.sh` stays authoritative for
     the per-seam **value** assertions across all four (the EUDR threshold and precision, the E&S
     category enum). Not duplicated here.

   Proven capable of failing before being trusted, in a detached worktree against copies — nothing
   in this repository was mutated: a drifted own vocabulary, a deleted `$defs.Status.enum`, a
   drifted sibling copy, a seam pin no sibling carries, and `--require-siblings` with none present
   each exited 1 naming the file or the pin; each restored to exit 0.

   **Stated limit, so it is not discovered later.** A digest recorded in the same repository as the
   file it pins can be updated in the same edit, and no in-repo tripwire can prevent that. It
   catches the *silent* drift — a reformat, an editor rewrite, a hand-merged conflict. A
   *deliberate* change is caught by the version-bump rule instead: bumping `vocabularyVersion` is
   tied to the register by this gate and to the siblings by the four-way script, so it cannot land
   in one repo alone and pass anywhere.
3. **`rfcs/` was missing from `LICENSING.md`'s per-path map — CLOSED, see below.** The ambiguity
   as it stood: the map's prose row
   (`README.md`, `docs/`, `profiles/`, …) would sweep RFCs in as **CC BY 4.0** by content class;
   but `rfcs/0001` carries an `SPDX-License-Identifier: Apache-2.0` header, RFCs 0003–0005 follow
   that precedent, and `rfcs/0002` carries **no header at all** — three states across five files.
   `docs/spec-governance.md` §2 cuts toward Apache-2.0 ("CC-BY … is *not* designed for things that
   are implemented as code"), and these RFCs do carry field-level schema sketches meant to be
   implemented. `LICENSING.md`'s own fallback ("the most specific matching rule above it applies")
   does not resolve it, because no rule matches `rfcs/`. The steward should state the rule and
   make the five files consistent with it — a licensing question, not an editorial one.

   Re-verified 2026-08-16, unchanged at the time: `rfcs/0001`, `0003`, `0004` and `0005` each
   carried an `SPDX-FileCopyrightText`/`SPDX-License-Identifier: Apache-2.0` header; `rfcs/0002`
   carried none; `LICENSING.md` contained no rule matching `rfcs/`.

   **CLOSED 2026-08-16. Rodrick, as steward, decided `rfcs/` is Apache-2.0.** The rule and its
   reasoning are now recorded in [`../LICENSING.md`](../LICENSING.md) §"Why RFCs are Apache-2.0
   (and not CC BY)" — in the licensing map rather than only here, so the next person meets it where
   they look up a path.

   **The decisive reason is the patent grant.** This repo ships a patent non-assertion covenant
   ([`../PATENTS`](../PATENTS)) so implementers can build without fear of an ambush, and **CC BY
   4.0 grants no patent rights** — its § 2(b)(2) reads *"Patent and trademark rights are not
   licensed under this Public License."* These RFCs carry normative schema that implementers build
   against, so under CC BY the implementable part would travel without the very protection the
   repo exists to provide. `docs/spec-governance.md` §2 already pointed the same way, and four of
   the five files had converged on Apache-2.0 by hand.

   Two things followed mechanically: `rfcs/0002` got the header the other four carry, and
   `scripts/validate.py`'s SPDX check — which globbed only `openapi*.yaml`, `scripts/*.py`,
   `conformance/*.py` and `standards/registry.yaml`, five files, **none of them under `rfcs/`** —
   now globs `rfcs/*.md` too. That blindness is why `rfcs/0002` could ship headerless with the gate
   green. Proven in both directions: with the glob added and `0002` still bare the gate exited 1
   naming it; with the header added it read 10 files and exited 0; and a planted headerless
   `rfcs/0006` was caught and cleared the same way.

---

## 1. Vaccination enrichment

**Landed** — client `2.0.0` → `2.1.0`. The smallest step in the list and the most urgent, taken as
a direct additive PR rather than an RFC: it adds no object, no endpoint and no plane, only optional
fields to a schema that already existed.

`Vaccination` already carried **`lot_number`**, which satisfies the batch requirement; it was
**not** duplicated under a new name. Six optional fields were added:

| Field | Type | Why |
|---|---|---|
| `lot_expiry` | `date` | A lot number identifies the batch for a recall; only the expiry says whether the dose was viable when it went in. It is on the vial. |
| `cold_chain_ok` | `boolean\|null` | The administering officer's attestation that the cold chain held. A vaccine that broke cold chain was an injection, not an immunisation, so coverage computed without it over-reports protection — and coverage is the number an outbreak response is planned against. |
| `cold_chain_evidence_ref` | `string\|null` | A hash/URI **reference** to the evidence, never the evidence. Fridge telemetry stays with the integrator (RFC 0003 §9). |
| `dual_id_confirmed` | `boolean\|null` | The animal was presented with both its **permanent mark (brand/tattoo)** and its **tag**, and the two agreed. Not "two tags", and not tag-plus-EID. |
| `holding_id` | `string` | Where the dose was given. Recorded, not derived — deriving it from the animal's *current* holding is wrong for any animal that has since moved. |
| `zone_code` | `string` | The zone at the time of administration. Same reason: zones change, and ring-vaccination coverage is a question about the zone as it was. |

**Polarity note.** The control plane already counts `CampaignProgress.cold_chain_exceptions`, so
the client field and the admin counter are opposite polarities of one fact. The admin spec has no
competing *field* name — its counter is a campaign-level aggregate, not a per-vaccination field —
so `cold_chain_ok` was kept for its attestation semantics and safer absent-state (absent means
*not asserted*, never "the chain held"), with the link to the counter written explicitly into the
field description rather than left to inference.

**Neutrality.** The statutory basis for dual identification is **not** written into the shared
contract. The schema records the fact and states that its legal weight is profile-defined, because
hard-coding one jurisdiction's identification law into a multi-country contract is the neutrality
failure RFC 0003 §3 argues against. The citation belongs in `profiles/za` (step 8).

**TO-VERIFY:** the driver — South Africa's **RVS-FMD scheme, reported gazetted 4 May 2026**,
conditioning participation on a digital system recording vaccination date, vaccine batch number and
storage temperature — and the **Animal Identification Act 6 of 2002** attribution behind
`dual_id_confirmed`. Both unverified; confirm with the South African authority before any profile
cites them.

**Shipped with:** updated `examples/record-vaccination.json`, the integration guide's field
mapping, a `### Added` changelog entry, and two conformance cases — that a `2.0.0`-shaped body is
still accepted at `2.1.0` (the guard that "additive" really was additive), and that
`cold_chain_ok: false` is the event incrementing `cold_chain_exceptions` (a cross-plane seam,
asserted end to end).

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

**How to verify a pin — 2026-08-16, both halves now runnable, and both of them YOUR job to run.**
Each of the five pins must still be added to the sibling registers in the same change window, but
checking it is a command rather than an inspection. **Neither command is run by any pipeline
today** ([follow-up 2](#follow-up-still-open)): Actions is disabled here, and FuroField's runs are
all failing at startup. Run **both** by hand; they answer different questions:

```bash
python3 scripts/check-standards-parity.py --require-siblings   # this repo's gate — BY HAND; CI does not run it
~/projects/FuroField/scripts/check-standards-parity.sh         # the four-way seam-VALUE comparison
```

The first is this repository's own gate ([follow-up 2](#follow-up-still-open)), added after Rodrick
decided this repo should own one. Once CI does run it, it will run with no siblings and say so —
`PASS (SELF-CHECK ONLY)`, every sibling listed as `NOT COMPARED`. Locally, `--require-siblings` makes a missing
checkout a failure, which is what you want at the moment you are adding a pin: it will not let an
uncheckable sibling pass as an agreeing one. It fails if a pin this register declares is named by
none of the siblings present — a pin on one side only is a claim, not a pin.

The second stays authoritative for the per-seam **values** (the EUDR threshold and precision, the
E&S category enum), which the first deliberately does not duplicate.

Read the exit code of each: 0 = agreement as far as that run could see; 1 names the drift.

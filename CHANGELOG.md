# Changelog

All notable changes to the **LITS API contract** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The contract is versioned in the URL
path (`/v1`); see [CONTRIBUTING.md](./CONTRIBUTING.md) for the change policy.

## [Unreleased]

### Fixed

**The specs asserted three seam pins that no register on any side declares.** Six descriptions
across both planes read *"Pinned vocabulary — seam pin `order-status`"* (likewise
`permit-condition-codes` and `trace-flag-codes`). `standards/registry.yaml` declares neither —
only `eudr-geometry` and `es-attestation-category` — and it abstains **on purpose**, because
`scripts/check-standards-parity.py` check 5 refuses a pin no sibling names: *"a pin that exists on
one side only is not a pin; it is a claim"* ([docs/roadmap.md](./docs/roadmap.md)). `2.2.0`'s own
"Not shipped, and owed" note says exactly this. So the register and the changelog were the honest
halves, and **the published contract was the one overclaiming** — an integrator reading it saw a
cross-repo agreement that does not exist.

Re-verified before changing anything, with the parity gate's own matcher rather than a hand grep:
all four sibling checkouts are present, and **none** declares any of the three in a standards
artifact. The only occurrences anywhere are a `name="order-status"` radio button in FuroTrack's
dashboard (the near-miss recorded at `2.2.0`) and a FuroTech planning document listing the pins as
*owed*. Declaring them here alone would have been the same defect facing the other way, so the
prose is downgraded instead: each site now reads **proposed**, states that no register declares it
yet, and names what would make it a pin — this register and the FuroTrack and Dzinza registers
declaring it in one change window. No schema, enum, field or status code changed.

**No version bump is taken here, and that is a steward decision, not an omission.**
[CONTRIBUTING.md](./CONTRIBUTING.md)'s change policy is written in terms of schema semantics
(fields, enum values, required-ness, status codes); none of those moved, so the policy does not
call for one. The open question is the *artifact-integrity* one it does not cover — whether
correcting published `2.2.0` prose in place should still carry a `2.2.1`, so that two documents
never share a version string. Flagged for the steward rather than answered.

### Added

**A gate that reads spec prose — nothing ever had.** `scripts/validate.py` check 8 requires every
seam pin the specs **assert** to be declared in `standards/registry.yaml`. That closes the first
link of a two-link chain and deliberately duplicates neither half:

    spec prose  ->  standards/registry.yaml     (validate.py, standalone)
    registry    ->  the sibling registers       (check-standards-parity.py, check 5)

A spec may assert a pin only if this register declares it; this register may declare it only if a
sibling does. Marking a pin `**proposed**` is a legitimate downgrade rather than an escape hatch —
it changes what the integrator reads, which was the entire defect — and the reverse is checked
too, so a pin that later becomes real cannot leave the prose calling it proposed.

> **A hole in the first draft of that gate, worth recording.** It required literal spaces
> (`seam pin \`x\``) and so matched **nothing** at `openapi.yaml:1714` and
> `openapi-admin.yaml:1729`, where the wrapped YAML block scalar splits the phrase across a line.
> Two of the six sites it existed to police were invisible to it and it reported a confident green
> over them. It was caught only because the check prints its count and `4` disagreed with a hand
> count of `6`. The pattern now spans whitespace, and a second net reconciles every bare `seam pin`
> mention against the named ones, so a phrase this gate cannot parse fails loudly instead of
> passing silently.

## [2.2.0] — 2026-08-16

### Added

**Disease response orders — quarantine, standstill, and animal trace flags.** The client half of
[RFC 0003](./rfcs/0003-disease-response-orders.md), accepted by the steward on 2026-08-16 as a
**pre-designation decision** ([GOVERNANCE.md](./GOVERNANCE.md) §2 constitutes the joint steering
committee *on designation*, so it does not exist yet and may revisit this). Minor release: new
endpoint, new schemas, one new enum value on an existing field, two new optional response fields.

**What was missing.** The contract could already record that an animal is **sick**
(`POST /v1/disease-cases`, `POST /v1/lab-results`) and that an area is **restricted**
(`GET /v1/zones`). It carried no way to express the thing sitting between those two facts that
actually stops a truck: **the order**. That decision lived in a paper notice served on the keeper
and — if the officer thought to do it — a zone, and a client could read neither. So a farm app
whose keeper was under quarantine would lodge a movement, show the keeper a permit reference, and
let the stock leave. The registry knew the holding was closed; the contract never told anyone.

**What landed in `openapi.yaml`:**

- **New** `GET /v1/quarantine-orders?since_version=&country_code=&limit=` → `QuarantineOrderDelta`.
  It is **`/zones`'s shape field for field**, on purpose rather than for want of imagination: the
  consuming device is a phone on intermittent connectivity that must sync a small delta and then
  enforce **offline**, and every deployed consumer already has code for this cursor. No elevated
  scope — an order the client cannot read is an order the client cannot enforce.
- **New** `QuarantineOrder`, `QuarantineOrderDelta`, `OrderMilestone`, `OrderCondition`,
  `TraceFlag`, and the five vocabularies they carry as named components so each is stated once:
  `OrderType`, `OrderStatus`, `OrderScope`, `OrderMilestoneCode`, `OrderConditionCode`,
  `TraceFlagCode`.
- **Changed** `Zone.zone_type` — gains `standstill`. See "not free" below.
- **Added** optional `trace_flags` to `AnimalRecord` (`GET /v1/animals/{national_id}`) and to
  `AnimalHealthStatus` (`GET /v1/animals/{id}/health`, `health:read`).

**Three design decisions worth stating, because each had a cheaper wrong answer:**

1. **No jurisdiction's arithmetic is in the contract.** It is tempting to say a quarantine lasts
   *n* days. The periods differ by territory and by disease and change by gazette, so hard-coding
   any one country's numbers would quietly make the standard that country's — and a national
   instance would have to fork it to obey its own law, which is the exact outcome
   vendor-neutrality exists to prevent. The contract therefore carries **dates and their meaning**
   (`milestones[{code, date}]`, pinned code vocabulary) and never the rule that produced them.
   **Each profile states which milestones its law requires and how they are derived.**
2. **A standstill is projected into the zone feed.** An active standstill order also appears in
   `GET /v1/zones` as `zone_type: standstill` with `movement_restriction: blocked`. The payoff is
   the whole reason the shape was chosen: **an already-deployed client enforces a national
   standstill with zero client changes**, on its next zone sync, because it is reading a field it
   has always read. Outbreak response is measured in hours; a coordinated release across every
   accredited vendor is measured in weeks. The order is the record and the zone is the view —
   it is never authored through `/admin/zones` (which is why `ZoneWrite` did **not** gain the
   value), lifting the order retracts the zone by the same mechanism that declared it, and
   `projected_zone_code` lets a client reading both feeds join them instead of counting one
   restriction as two.
3. **Trace flags are registry-applied only.** There is no client write path and that is the point,
   not an oversight: a lifelong mark on a keeper's animal is a determination with real economic
   consequence for a named person, so it must carry an officer, a legal basis and an audit entry,
   and be appealable. A farm app that could stamp it would exercise authority it does not have and
   the audit trail would record a vendor key instead of a decision-maker. `expires_at: null` is
   documented in the schema as meaning **lifelong**, because the alternative reading — "not yet
   set" — fails in exactly the wrong direction.

**Additive in form. Two items are not additive in EFFECT, and are called out rather than glossed:**

- **`Zone.zone_type: standstill`.** `zone_type` is `required` on `Zone`, so a new value is a
  widening for the server and therefore a **tightening for every reader**. A client that switches
  exhaustively on `zone_type` with no default branch can break on it. It is judged acceptable
  because the load-bearing field for enforcement is `movement_restriction`, which is unchanged and
  whose values are unchanged, and gating on `movement_restriction: blocked` is what the
  integration guide already tells clients to do. The field description now says so in the
  contract, and a conformance case asserts a client tolerates an unknown `zone_type`.
- **`OrderConditionCode` is a fail-closed vocabulary.** A client meeting a code it does not
  recognise MUST treat the order as at least as restrictive as `no_movement_on_off`. This inverts
  [CONTRIBUTING.md](./CONTRIBUTING.md)'s additive-enum rule ("new enum value that clients may
  ignore"), and the inversion is deliberate: for a *restriction* vocabulary, ignoring what you do
  not understand permits a movement the authority forbade. The consequence is that **adding a
  condition code later is not a free additive change** — it moves deployed clients from permitting
  to blocking on their next sync, needs a minor bump and integrator notice, and is safe only in
  that direction.

**`draft` is deliberately absent from the client `OrderStatus`.** RFC 0003 §8 sketches one status
enum for both planes, but §2 annotates the *admin* read as "incl. drafts" — which is only
meaningful as a contrast with the client feed. A client never sees an order the authority has not
yet made, exactly as `MovementLifecycleStatus` omits the control plane's `draft`. The pinned
`order-status` vocabulary remains the full six values; the client feed publishes five of them.

**Covered by checks proven able to fail.** Three new examples —
`examples/quarantine-order-delta.response.json` (→ `QuarantineOrderDelta`),
`examples/standstill-zone-delta.response.json` (→ `ZoneDelta`) and
`examples/animal-health-trace-flags.response.json` (→ `AnimalHealthStatus`) — are validated by
`scripts/validate.py`'s example-conformance check. **Before** they were mapped, the gate exited 1
naming all three as validated by nothing, so the map is not optional. **After**, eight regressions
were planted in a scratch copy — nothing in the repo was mutated — and every one was caught,
naming the exact path:

| Planted regression | Caught at |
|---|---|
| `Zone.zone_type` loses `standstill` | `standstill-zone-delta…zones[0].zone_type` |
| `TraceFlagCode` loses `sero_positive_lifelong` | `animal-health-trace-flags…trace_flags[0].code` |
| `TraceFlag.expires_at` stops being nullable | `animal-health-trace-flags…trace_flags[0].expires_at` |
| `OrderMilestoneCode` loses `day_zero` | `quarantine-order-delta…orders[0].milestones[0].code` |
| `OrderStatus` loses `lifted` | `quarantine-order-delta…orders[2].status` |
| `OrderConditionCode` loses `no_movement_on_off` | `quarantine-order-delta…orders[0].conditions[0].code` |
| `OrderType` loses `standstill` | `quarantine-order-delta…orders[1].order_type` |
| example drops the required cursor `order_version` | `quarantine-order-delta…orders[0]` |

The `lifted` case is the one that makes "a retracted order stays in the delta" testable rather
than asserted, and the nullable-`expires_at` case does the same for "null means lifelong".

> **Stated limits, so they are not discovered later.**
>
> - **The example check binds an example to a NAMED schema, not to a reference.** A ninth
>   regression was planted — re-pointing `QuarantineOrderDelta.orders.items` at a bare
>   `type: object`, orphaning `QuarantineOrder` — and it **passed, exit 0**. This is the same
>   limit recorded at `2.1.1` and it now covers more surface, because this release adds eleven
>   schemas that are reachable only through `$ref`s. Closing it needs the "every declared schema
>   is referenced" check in [roadmap follow-up 4](./docs/roadmap.md#follow-up-still-open), which
>   still cannot land while `CertificateRevocation` is a genuine orphan.
> - **`AnimalRecord` is an `allOf`, and the example checker does not understand `allOf`.** An
>   example mapped to it would be validated by a pass that inspects nothing — a green measuring
>   zero. That is why the trace-flag example is bound to `AnimalHealthStatus`, a plain object,
>   where the recursion genuinely reaches `trace_flags[].code`. **`AnimalRecord.trace_flags` is
>   therefore contract surface with no example-level gate behind it**; it is covered only by the
>   live conformance case.
> - **The three new seam pins are NOT yet entered in the sibling registers, so they are not
>   declared here either.** See "Not shipped" below.

**What landed in `openapi-admin.yaml`** (`1.4.0-draft` → `1.5.0-draft`) — the plane on which an
order actually exists as an act:

- **New** `POST /admin/quarantine-orders` (draft), `GET /admin/quarantine-orders` (**incl.
  drafts**), `GET /admin/quarantine-orders/{order_id}`, and
  `POST /admin/quarantine-orders/{order_id}/{action}` where `action` is
  `activate | suspend | resume | extend | lift | revoke`. The transition idiom deliberately
  mirrors `POST /admin/movements/{ref}/{action}`: the control plane already has exactly one way to
  advance a regulated object through its lifecycle, and a second would be a new thing for an Admin
  Portal to learn for no gain. Scopes `orders:write` (author, transition) and `orders:read`.
- **New** `POST /admin/animals/{national_id}/trace-flags` and
  `POST /admin/animals/{national_id}/trace-flags/{code}/clear` (`herd:write`). Keyed on
  `national_id` — the sovereign identifier — because the flag follows the animal's national
  identity, not a local record id.
- **New** `QuarantineOrderWrite`, `OrderTransition`, `QuarantineOrder`, `TraceFlagWrite`,
  `TraceFlag`, and this plane's own copies of the six vocabularies. **No cross-file `$ref`s**, per
  CONTRIBUTING's "Two specs" rule — the specs stay independent.
- **Changed** `Zone.zone_type` on the admin **read** view — gains `standstill`. **`ZoneWrite` did
  not**, and that asymmetry is the design: the projected zone is a *view* of the order, authored by
  activating the order and retracted by lifting it, never edited through `/admin/zones`. A
  `ZoneWrite` that accepted `standstill` would let an operator create the second source of truth
  the projection exists to avoid.

Two behaviours are stated in the contract rather than left to the implementation:
**`activate` refuses `409` on an order carrying neither `declared_verbally_at` nor
`confirmed_in_writing_at`** (an order that was never made, in either form, binds nobody — while
the contract still carries both timestamps and decides nothing about which a territory's law
requires); and **`POST /admin/quarantine-orders` refuses `422 sections_not_declared`** for
`scope: section` against a holding whose sections the registry does not hold. Since no biosecurity
attestation surface exists yet, `scope: section` is **specified and currently not issuable at
all** — a limit the contract admits instead of hiding.

**`@redocly/cli lint` is unchanged by this release: 104 errors and 5 warnings before and after,
identical rule-for-rule.** Measured, not assumed — `a6a553c`'s two specs and the post-change two
specs were both linted with `@redocly/cli@2.46.1` and the per-rule counts diffed with no
difference. No finding lands on any new path or schema. Notably `no-unused-components` stays at
**1** (the pre-existing `CertificateRevocation` orphan), which is independent evidence that all
eleven new client schemas and thirteen new admin schemas are actually referenced.

**Not shipped in this release, and owed:**

- The seam pins `order-status`, `trace-flag-codes` and `permit-condition-codes` are **not** added
  to `standards/registry.yaml`. Adding a pin here that no sibling names is precisely what
  `scripts/check-standards-parity.py` check 5 refuses — *"a pin that exists on one side only is
  not a pin; it is a claim"* — and the sibling halves (FuroTrack, Dzinza) are outside this
  change's scope. The pin lands in the same change window as the sibling register entries, not
  before. `standards/vocabulary.v1.json` needs **no** edit for any of them: a `seamPin` is a value
  recorded on a control, not a schema change.

## [2.1.1] — 2026-08-16

### Fixed

**`GET /v1/movements/list` could not return an approved permit — a defect live in `2.0.0` since
2026-07-15.** Not a new capability: the endpoint has advertised this behaviour since `bd0ee9e`
(2026-07-10) and been unable to deliver it since `3b8e917` (2026-07-15). Patch release, because
nothing new is offered — a documented behaviour is made expressible.

**The defect.** `/movements/list` accepts `status=approved`, and its own description tells
integrators to poll it "to detect permits that have transitioned to `approved` in the registry
since their last sync". Its `200` returned an array of **`MovementAck`**, whose `status` enum
`3b8e917` had narrowed to `[lodged, blocked]`. **A conformant server could not express an approved
permit in the one endpoint whose stated purpose is returning them.** The filter accepted the
question and the schema forbade the answer.

**Two remedies were weighed. The one that shipped is (b).**

- **(a) Widen the shared `MovementAck.status`** to the full lifecycle. This is what
  [RFC 0004](./rfcs/0004-movement-pre-authorization.md) §3 proposed. **Rejected**, for three
  reasons:
  - **`approved` is not meaningful on an acknowledgement of a lodgement.** `MovementAck` answers
    "we received your submission". A lodgement is never born approved — that is precisely what
    `3b8e917` ("clarify movement authority contract") landed to establish. Admitting `approved`
    into the acknowledgement schema hands back, at the contract level, the reading that commit
    was written to end: that a client's own submission can come back authorised.
  - **`MovementAck` is shared by two WRITE paths, not one.** `POST /v1/movements` and
    `POST /keeper/movements` both return it. Widening the shared schema to fix a *read* endpoint
    would have loosened two write acknowledgements that were correct as they stood — the blast
    radius lands on the busiest path in the contract, to fix a defect that is not on it.
  - **It is a widening for the server and therefore a TIGHTENING for the client.** On a response
    schema, "more values may be returned" is a new obligation on every reader. RFC 0004 §6 said as
    much: "a client that exhaustively switched on `lodged | blocked` will now meet values it has
    never seen." That is the definition of a change a deployed client can break on.
- **(b) Give the read path its own schema, leave `MovementAck` alone.** Shipped. **No conformant
  client can break on it:** every field a client already parses is present, in the same place,
  with the same type and meaning; nothing is removed, renamed or made required; and the only new
  values appear exactly where the contract already told clients to expect them.
  - RFC 0004 §3's objection to (b) was that two nearly-identical enums will drift. **So the enum
    was not duplicated.** `MovementLifecycleStatus` is a single named component, `$ref`ed by the
    list item schema *and* by the `/movements/list?status=` filter — one vocabulary, one place,
    fewer restatements than (a) would have left behind.
  - **It is a step toward RFC 0004, not something 0004 must undo.** The ten values are RFC 0004
    §3's own lifecycle enum, verbatim. When `MovementPermit` (the detail view) lands it `$ref`s
    the same component; `MovementPermitSummary` stays the summary the list already returned. The
    RFC now carries an erratum recording that its §3 preference is superseded, because an accepted
    RFC that still recommends the rejected option is how a fix gets undone.

**What changed in `openapi.yaml`:**

- **New** `MovementLifecycleStatus` — `[lodged, under_review, approved, rejected, blocked,
  departed, arrived, completed, cancelled, expired]`. The control plane's `draft` state is
  deliberately absent: a client never sees a permit before it is lodged.
- **New** `MovementPermitSummary` — the list item. Same five fields `MovementAck` carries
  (`permit_reference`, `id`, `status`, `crosses_zone_boundary`, `recorded_at`), with the lifecycle
  enum on `status`.
- **New** `MovementList` — the `{count, movements}` body, named rather than inline so a published
  example can be checked against it (see below).
- **Changed** `/movements/list`: `200` now `$ref`s `MovementList`; the `status` filter now `$ref`s
  `MovementLifecycleStatus` instead of restating six of its ten values. The filter change is a
  **widening of accepted input** — the registry answers questions it previously rejected — which
  no client can break on.
- **Unchanged, on purpose:** `MovementAck`. Its `status` description now records *why* it stays at
  two values and points at `MovementLifecycleStatus`, so the next reader meets the reasoning
  instead of the temptation.

**Covered by a check that was proven able to fail.** `examples/movement-list.response.json` is new
and carries `approved` and `under_review`; `scripts/validate.py`'s example-conformance check
validates it against `MovementList`, recursing through the array and the `$ref`. Both regressions
were planted in a scratch copy — nothing in the repo was mutated — and both were caught: reverting
`MovementLifecycleStatus` to `[lodged, blocked]`, and re-pointing `MovementList.movements.items` at
`MovementAck`, each exited 1 naming `movement-list.response.json.movements[0].status`. Removing the
example's `EXAMPLE_SCHEMAS` entry also failed, so it cannot be silently opted out.

> **Stated limit, so it is not discovered later.** The example check binds an example to a **named
> schema**, not to an **endpoint**. Reverting `/movements/list`'s `200` to an inline schema while
> leaving `MovementList` defined but orphaned was planted too, and **passed** — exit 0. Closing
> that needs an "every declared schema is referenced" check, which cannot land while `openapi.yaml`
> carries a genuine orphan (`CertificateRevocation`, an operation described in three places and
> defined in none); see [roadmap follow-up 4](./docs/roadmap.md#follow-up-still-open), opened by
> this work.
>
> `@redocly/cli lint` run before and after this change reports the **identical** 3 errors and 4
> warnings on `openapi.yaml` — all pre-existing, none in the new schemas. This release adds no
> lint findings and fixes none.
>
> **Also not fixed here:** the list items carry `recorded_at`, not an updated-at, so `since` cannot
> be advanced from the response body. A poller must use its own request timestamp and expect to
> re-see recently-changed permits. That is a cursor design question the roadmap's event feed
> answers properly; adding a second timestamp here would compete with it.

Shipped with a conformance case and its guard (`conformance/README.md` §2, RFC 0004 §8.6): that
`?status=approved` returns items whose status is `approved`, **paired with** the assertion that a
`POST /v1/movements` acknowledgement is still only ever `lodged` or `blocked`. The pair matters —
the cheapest way to pass the first case alone is remedy (a), and the second case is what refuses
it. `docs/integration-guide.md` §5 gains the poll loop it never described, with the two shapes set
out side by side and an instruction not to switch exhaustively on the read-view status.

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
  - **Corrected 2026-08-16 — check 5 could be satisfied by a RADIO BUTTON.** Found while
    verifying, before asserting it, that `[2.2.0]`'s three owed seam pins really would be
    refused if declared one-sidedly. Planting `order-status` in a scratch copy of the register
    and running the gate printed `order-status: named by furotrack` and **exited 0**. The match
    was `name="order-status"` — a radio-button group in
    `apps/web-dashboard/src/app/(dashboard)/orders/page.tsx`. A form control had satisfied a
    four-repo standards obligation.
    - **The cause was a necessary breadth, not carelessness.** Only Dzinza keeps its register as
      a `registry.yaml`; FuroField's lives in `apps/app/lib/standards/*.ts` and the engine's in
      `furotech_api/standards/*.py`, so the check cannot simply read one filename and had to
      search broadly — and a bare substring search over a whole application will eventually hit
      an unrelated string.
    - **The earlier "proven able to fail" claim above was true and still insufficient.** It used
      a pin name nothing happened to contain, so it proved the check *can* go red without proving
      it goes red for a pin someone would really add. A tripwire has to be tested with the input
      it will actually see.
    - **Fixed:** a match now counts only in a **standards artifact** — a path component
      containing `standards`, or a register file — and the output names the **file** that
      declared the pin (`dzinza:platform/lits/standards.py`) rather than only the repo, so the
      evidence is in the log instead of in the reader's trust. Proven both ways: the two real
      pins still pass, and the planted `order-status` now exits 1 naming it.
    - **What it nearly cost.** Had `[2.2.0]` added its three pins without checking, the gate
      would have reported them agreed, and "pinned on both sides" would have been false with
      every check green — the exact failure the pin obligation exists to prevent, arriving
      through the mechanism meant to prevent it.
- **`rfcs/` is licensed Apache-2.0, stated in `LICENSING.md` for the first time.** A steward's
  licensing decision, not an editorial one. The per-path map had **no rule matching `rfcs/`** and
  its own fallback ("the most specific matching rule above it applies") could not resolve it, so
  the five files sat in three states: `rfcs/0001`, `0003`, `0004` and `0005` carrying an
  Apache-2.0 SPDX header written by hand, and `rfcs/0002` carrying none.
  - **The decisive reason is the patent grant**, and it is recorded in `LICENSING.md` §"Why RFCs
    are Apache-2.0 (and not CC BY)" so it is not relitigated. This repo ships a patent
    non-assertion covenant (`PATENTS`) precisely so implementers can build without fear of an
    ambush; **CC BY 4.0 grants no patent rights** — § 2(b)(2): *"Patent and trademark rights are
    not licensed under this Public License."* These RFCs carry normative schema that implementers
    build against, so under CC BY the implementable part would travel without the protection the
    repo exists to provide. `docs/spec-governance.md` §2 already said CC-BY "is *not* designed for
    things that are implemented as code."
  - Narrative documentation is unchanged and stays CC BY 4.0. The line is **implementability**,
    not file format: `docs/roadmap.md` describes what may be built, an RFC specifies it.
  - **`rfcs/0002` now carries the header the other four carry.**
  - **`scripts/validate.py`'s SPDX check now covers `rfcs/*.md`.** It globbed only
    `openapi*.yaml`, `scripts/*.py`, `conformance/*.py` and `standards/registry.yaml` — five
    files, **none under `rfcs/`** — which is exactly why `rfcs/0002` shipped headerless with the
    gate reporting OK. Proven in both directions on the real defect: with the glob added and
    `0002` still bare the gate exited 1 naming `rfcs/0002-dpi-interop-adapters.md`; with the
    header added it read 10 files and exited 0. A planted headerless `rfcs/0006` was caught and
    cleared the same way, so a *future* RFC cannot repeat it.
- **RFCs 0003, 0004 and 0005 moved Draft → Accepted (2026-08-16).** Recorded here because
  [docs/spec-governance.md](./docs/spec-governance.md) §6 makes the public changelog part of the
  change process, and integrators sequence their own work off these. **No contract byte changed:**
  acceptance ratifies a design, it does not ship one. `openapi.yaml` and `openapi-admin.yaml` are
  untouched by this entry, and no schema, path or field named in any of the three RFCs exists yet.
  - **Accepted by the steward, not by a steering committee — and the distinction is recorded
    rather than smoothed over.** [GOVERNANCE.md](./GOVERNANCE.md) §4 assigns sovereign-impacting
    RFCs — which all three are (zone authority and personal data; movement authority and
    certificate semantics; personal data leaving the registry over a webhook) — to the **joint
    steering committee**. §2 constitutes that committee **on designation**, so it does not exist
    yet, and §2 gives the pre-designation steward the decision rights meanwhile. Each RFC's status
    line now says exactly that, and says the committee may revisit the decision once constituted.
    "Ratified by the steering committee" would have been the cheap wording and would have been
    false.
  - **No new status vocabulary was invented.** `docs/spec-governance.md` and `GOVERNANCE.md`
    define *who* decides and *what* must accompany a change, not an RFC status vocabulary;
    `rfcs/0002` has read **Accepted** since it was written, so that is the word used.
  - **What is unblocked, and what is not.** [docs/roadmap.md](./docs/roadmap.md) records the three
    steps as `accepted` and states, in the same place, that every ordering constraint survives
    acceptance: RFC 0003 before RFC 0004 (a movement issued *under an order* needs orders to
    exist, and 0004's permit conditions reuse 0003's `permit-condition-codes` vocabulary); the
    event feed strictly before webhook subscriptions (the poll loop is the recovery path for a
    lapsed or auto-disabled subscription); and `profiles/za` still last, because a profile maps
    law onto **contract surface that exists**, and a ratified RFC is a shape, not a schema.

---

*Pre-release development history is kept with the implementation in the private platform
repository; this public changelog begins with the first published draft of the contract.*

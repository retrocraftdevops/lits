<!--
SPDX-FileCopyrightText: 2026 The LITS steward
SPDX-License-Identifier: Apache-2.0
-->
# RFC 0005 — Event feed and webhook subscriptions

- **Status:** **Accepted 2026-08-16** by the steward (Rodrick Makore). Sovereign-impacting under
  [GOVERNANCE.md](../GOVERNANCE.md) §4 — the subscription half touches **personal data**, because
  it sends facts about named keepers' animals to an endpoint the registry does not control — and
  §4 assigns such RFCs to the joint steering committee. **That committee does not exist yet**: §2
  constitutes it *on designation*, so until then the steward holds the decision rights and this is
  recorded as a **pre-designation steward decision** which the committee may revisit. Acceptance
  ratifies the design, not an implementation: nothing here has landed, and the **ordering
  constraint in §6 / roadmap step 7 (feed strictly before subscriptions) is not relaxed by
  acceptance** — see [../docs/roadmap.md](../docs/roadmap.md).
- **Affects:** `openapi.yaml` (client) 2.2.0 → 2.3.0 for the feed; the subscription surface adds
  to `openapi.yaml` and `openapi-admin.yaml` 1.6.0-draft → 1.7.0-draft. (Numbers assume the
  roadmap order; they are relative to it, not absolute reservations.)
- **Backwards compatibility:** Additive only, within `/v1`. Nothing is removed; the existing
  delta feeds keep working unchanged and are **not** deprecated (§6).
- **Reuses:** RFC 0002's HMAC signing convention. **Consumes:** RFC 0003's orders and RFC 0004's
  permits as event subjects.

> **Honesty note.** Every statutory fact below is **TO-VERIFY**, per the `profiles/mz` discipline.

---

## 1. The problem: the contract is poll-only, and the polls are multiplying

Every "how do I find out what changed?" answer in the contract today is a different poll with a
different cursor:

| Feed | Cursor |
|---|---|
| `GET /v1/zones` | `since_version` (monotonic integer) |
| `GET /v1/movements/list` | `since` (timestamp) |
| `GET /v1/quarantine-orders` (RFC 0003) | `since_version` (monotonic integer) |

That is three loops, two cursor styles, and one more of each with every capability the standard
adds. The cost lands in three places:

- **On the integrator.** A client that wants to know "did anything change that affects me?" must
  poll N endpoints on N schedules and reconcile them. Each new endpoint is new client work, which
  means the slowest vendor sets the pace at which the registry can add anything.
- **On the registry.** Every accredited integrator polling every feed on a short interval is a
  load profile that scales with vendors × feeds, almost all of it returning nothing.
- **On the timeline that matters.** The registry cannot tell a client about anything the client
  did not think to poll for. A standstill declared at 06:00 reaches a client on its next zone
  sync — which, at a polite polling interval, is not 06:01. RFC 0003 §4.2 works hard to make
  standstill enforceable *without a client release*; it cannot make it *fast* while the only
  transport is a poll.

## 2. Step one — one monotonic loop (`GET /v1/events`)

The additive, low-risk step. One feed, one cursor, everything on it.

```
GET /v1/events?since_cursor=&types=&limit=   → EventPage
```

```yaml
EventPage:
  type: object
  required: [next_cursor, events]
  properties:
    next_cursor: { type: string, description: Opaque. Persist it; pass it back. }
    has_more:    { type: boolean, description: True when the page was truncated by `limit`. }
    events:      { type: array, items: { $ref: '#/components/schemas/Event' } }

Event:
  type: object
  required: [event_id, type, occurred_at, cursor, subject_type, subject_id]
  properties:
    event_id:
      type: string
      description: Stable and unique. The dedupe key — delivery is at-least-once (§4).
    cursor:      { type: string, description: This event's position; opaque, monotonic. }
    type:        { type: string, description: Pinned vocabulary — see §3. }
    occurred_at: { type: string, format: date-time }
    subject_type:
      type: string
      enum: [animal, holding, movement, certificate, zone, quarantine_order, disease_case, campaign, lab_result]
    subject_id:  { type: string }
    resource_url:
      type: string
      description: |
        Where to read the subject's CURRENT state. The event carries no domain payload — see §2.1.
    country_code: { type: string }
```

### 2.1 Events are notifications, not payloads

The single most important design decision here, and the one that will be argued with: **an event
says "movement `MVP-2026-00477` changed — go read it." It does not carry the movement.**

Three reasons, in ascending order of importance:

1. **A payload is a second source of truth.** An event log that carries data can disagree with the
   resource it describes — after a retry, after a correction, after a revocation. A pointer cannot
   be stale in a way that matters, because following it always yields the current truth. For a
   registry whose entire claim is "the registry is the source of truth"
   (CONTRIBUTING.md), shipping a second, divergent copy of the record over a firehose is an odd
   thing to do.
2. **Duplicates are free.** Delivery is at-least-once (§4), so consumers will see events twice.
   Re-reading a resource is naturally idempotent; re-applying a payload is not.
3. **Scope enforcement.** This is the decisive one. Authorisation in this contract is key-bound
   and per-endpoint: `movements:read`, `health:read`, `holdings:read` gate *elevated* reads
   precisely so a restricted third-party key cannot see everything. A feed carrying payloads
   would have to re-implement every one of those gates, per field, per event type — and the first
   mistake silently exports the national herd to a key that was never granted it. A feed carrying
   **pointers** enforces scope where it is already enforced: the consumer follows
   `resource_url`, and the existing endpoint refuses it. The event feed itself must still be
   **filtered to the subjects the key may read** — a key that cannot read a holding must not learn
   that it changed — but that is one filter on one field, not a payload-shaped attack surface.

## 3. The event-type vocabulary is pinned

Free-form event type strings would make every consumer's switch statement a guess:

```
zone.declared                 zone.updated                 zone.expired
quarantine_order.issued       quarantine_order.amended     quarantine_order.lifted
movement.lodged               movement.approved            movement.rejected
movement.departed             movement.completed
certificate.issued            certificate.revoked
animal.registered             animal.trace_flag_applied
campaign.started              campaign.completed
disease_case.reported         disease_case.reclassified
lab_result.recorded
```

**Unknown `type` values here are safely ignorable** — and it is worth contrasting this explicitly
with RFC 0003 §4.1, where unknown *condition* codes must fail closed. The difference is what
ignorance costs: ignoring an unrecognised notification means you did not react to something;
ignoring an unrecognised restriction means you permitted something forbidden. Same enum-widening
mechanism, opposite safe default, and both should be stated in the contract rather than inferred.

Like RFC 0003's vocabularies, `event-types` is a **pinned seam**: FuroTrack and Dzinza carry the
identical list in their standards registers, and drift is a conformance failure.
`standards/vocabulary.v1.json` needs **no** edit for it.

## 4. Step two — webhook subscriptions (the RFC-class half)

The feed removes the multiplicity; it does not remove the polling. Push does, and push is where
the sovereign and data-protection questions live — which is why it is the half that genuinely
needs ratification rather than just review.

```
POST   /v1/subscriptions           → Subscription    (integrator-key scoped)
GET    /v1/subscriptions           → [Subscription]  (only the calling key's)
DELETE /v1/subscriptions/{id}
GET    /admin/subscriptions        → [Subscription]  (all; operator visibility)
POST   /admin/subscriptions/{id}/disable
```

```yaml
Subscription:
  type: object
  required: [id, url, types, status]
  properties:
    id:     { type: string }
    url:    { type: string, format: uri, description: HTTPS only. }
    types:  { type: array, items: { type: string }, description: Pinned event types (§3). }
    status: { type: string, enum: [active, failing, disabled] }
    secret_set:      { type: boolean, description: Whether a signing secret is set. Never the secret. }
    created_at:      { type: string, format: date-time }
    last_success_at: { type: [string, 'null'], format: date-time }
    consecutive_failures: { type: integer }
```

An integrator manages **its own** subscriptions (client plane, scoped to the calling key); the
operator retains visibility and a force-disable (admin plane). That split follows the two-plane
model without making integrators file a ticket to change a URL.

**Signing reuses RFC 0002's convention rather than inventing one.** RFC 0002 already established
`X-Signature: hmac-sha256(body, secret)` for the payments connector; a webhook is the same
problem in the other direction, and a second signing scheme in one system is a second thing to get
wrong. Delivery headers:

```
X-Signature:       hmac-sha256(raw_body, subscription_secret)
X-LITS-Event-Id:   <event_id>        # dedupe
X-LITS-Timestamp:  <RFC 3339>        # include in the signed material; reject old ones — replay
```

**Delivery semantics, stated in the contract so they are not per-implementation folklore:**

- **At-least-once.** Consumers **must** dedupe on `event_id`. Exactly-once is not offered because
  it cannot be honestly delivered over HTTP to endpoints the registry does not control.
- **The body is an `Event`** — the same pointer-shaped object as the feed (§2.1). Doubly so here:
  the body crosses to a third-party URL, so anything in it has left the registry's control
  permanently.
- **Retry** with exponential backoff over a bounded window; `2xx` is success, everything else is
  a failure.
- **Auto-disable** after N consecutive failures across M hours, with the operator notified. An
  endpoint that has been dead for a day should not be retried forever.
- **The poll feed is the recovery path.** A disabled or lapsed subscriber catches up with
  `GET /v1/events?since_cursor=`. This is precisely why the feed must land **first**: a webhook
  system with no catch-up loop is unrecoverable, and its first outage becomes a permanent gap.

## 5. The keeper alerting surface

Integrators are not the only audience. The person who most needs to know that a holding is under
quarantine is the **keeper**, and the contract already has a keeper plane — `/keeper/*` under
`keeperSession` auth.

```
GET /v1/keeper/alerts?since_cursor=   → EventPage   (keeperSession)
```

The same event spine, filtered to the keeper's own holdings and animals. No new machinery: the
scope filter already required for §2.1 is the same filter, with a keeper session instead of an
integrator key.

### SMS and USSD stay OUT of the contract

The registry publishes the **event**. Whether a given keeper is told by SMS, USSD, a push
notification or a district officer with a phone is an **operator concern**, not a contract
concern. This is a deliberate boundary, and the reasons are worth recording because it will be
asked for:

- **It is per-territory.** Short codes, aggregator contracts and regulatory allocation differ by
  country (INCM in Mozambique, POTRAZ in Zimbabwe — both **TO-VERIFY**). A channel in the contract
  would be wrong in most territories on the day it shipped.
- **It is a cost and procurement decision.** Per-message cost, who pays, and volume caps are
  operator economics. An open standard that obliges every national instance to run an SMS budget
  is not a neutral standard.
- **It carries personal data over a channel the contract cannot secure.** An SMS to a named
  keeper's handset is a disclosure with no transport the registry controls and no signature the
  recipient can check. That belongs under the operator's processor obligations
  (GOVERNANCE.md §6), governed by the operating agreement, not by an API document.
- **It would date badly.** Delivery channels turn over on a far shorter cycle than a national
  traceability contract should.

So the contract's obligation ends at making the event available, promptly, to a party entitled to
it. Delivery is the operator's.

## 6. The existing delta feeds are not deprecated

`GET /v1/zones?since_version=` and `GET /v1/quarantine-orders?since_version=` **stay**, unchanged
and supported, and this RFC proposes no path to removing them.

Removing them would be a breaking change requiring `/v2` (CONTRIBUTING.md), and it would break
every deployed field device at the moment of least tolerance for it. More importantly, the zone
delta is the offline-first path: a phone in a district with intermittent connectivity syncs a
small, bounded, integer-cursored delta and enforces offline. A general event feed does not replace
that; it complements it. A client may use either or both.

## 7. Versioning impact

All additive within `/v1`; no `/vN`.

| Spec | From | To | What lands |
|---|---|---|---|
| `openapi.yaml` (client) | 2.2.0 | **2.3.0** | `GET /v1/events`; `Event`, `EventPage` schemas; the pinned event-type vocabulary; `GET /v1/keeper/alerts` |
| `openapi.yaml` (client) | 2.3.0 | **2.4.0** | `POST`/`GET`/`DELETE /v1/subscriptions`; `Subscription` schema |
| `openapi-admin.yaml` | 1.6.0-draft | **1.7.0-draft** | `GET /admin/subscriptions`, `POST /admin/subscriptions/{id}/disable` |

Cross-repo seam-pin obligation: `event-types` must be pinned in FuroTrack's and Dzinza's standards
registers in the same change window. `standards/vocabulary.v1.json` needs **no** edit — and if it
ever does, it lands byte-identically in all four repos at once or in none.

## 8. What stays OUT of the registry

- **Notification preferences and quiet hours** — per-user delivery choices belong to the app the
  user actually holds.
- **In-app inboxes, read/unread state, digest scheduling** — presentation, not record.
- **Staff on-call rotas and escalation trees** — operational.
- **SMS/USSD delivery itself** (§5), and any message templating or translation for it.
- **Analytics on the feed** — open rates, engagement. Not the registry's business.

## 9. Conformance cases to add

1. **Cursor monotonicity.** Events returned for `since_cursor=C` all have cursors greater than
   `C`, and `next_cursor` is not less than the greatest returned.
2. **Replay safety.** Replaying `since_cursor=C` returns the same set or a superset — **never a
   gap**. This is the property the whole recovery story rests on, so it must be tested, not
   assumed.
3. **Scope filtering.** An event whose subject the calling key may not read is **absent** from
   that key's feed — asserted with a restricted key, not merely with a full-access one, or the
   test measures nothing.
4. **`types=` filters** to exactly the requested types.
5. **Unknown types are ignorable** — a client presented with an unrecognised `type` continues
   processing the page (the contrast with RFC 0003 §4.1, made testable).
6. **`resource_url` resolves** to the subject and returns its current state; the event carries no
   domain payload (§2.1) — asserted by schema, so a payload-carrying implementation fails.
7. **Pagination.** `has_more: true` plus `next_cursor` walks the whole log with no gap and no
   infinite loop.
8. **Webhook signature vector.** A fixed body + secret produces a known `X-Signature`, verifiable
   by a third party — the same shape RFC 0002's HMAC needs.
9. **Replay rejection.** A delivery whose `X-LITS-Timestamp` is outside the tolerance is
   rejectable by the consumer, and the timestamp is inside the signed material.
10. **At-least-once is honest.** A consumer that returns `5xx` once receives the event again with
    the **same `event_id`**.
11. **Auto-disable.** After the configured consecutive failures the subscription reaches
    `disabled`, and the missed events are still retrievable from `GET /v1/events` (the recovery
    path, §4).
12. **`secret_set` never discloses the secret** in any response.
13. **Keeper alerts are keeper-scoped** — a keeper session sees only its own holdings' events.

## 10. Open questions for ratification

1. **Cursor format.** Opaque string (proposed — it lets the implementation change without a
   contract change) or a monotonic integer matching `/zones`' `since_version` (familiar, and
   forces the implementation's hand)?
2. **Retention window of the event log.** How far back may a client catch up? Too short and a
   long outage becomes a permanent gap that only a full resync closes; too long and the registry
   retains an indefinite, keeper-attributable activity log — a data-minimisation question under
   [Chapter 12:07]. This bounds §4's recovery guarantee and should be a stated number.
3. **Ordering guarantee.** Global ordering is simple to consume and hard to scale; per-subject
   ordering is the reverse. Per-subject is probably sufficient, but consumers must be told which
   they get.
4. **Who may hold a subscription?** Any accredited integrator, or only those with specific
   scopes? A webhook is a standing export of change data about named keepers to a third-party URL.
5. **Secret rotation.** How is a subscription secret rotated without dropping deliveries — dual
   secrets during an overlap window?
6. **Egress and sovereignty.** May a subscription URL resolve outside the territory? Pushing
   national herd change data to a foreign endpoint is a sovereignty question, not a technical one,
   and the answer may differ per territory (**TO-VERIFY** with each authority).
7. **Back-pressure.** What does the registry do when one subscriber is persistently slow — drop,
   queue, or disable? Queueing for one subscriber must not delay another.
8. **Does the keeper alert surface need its own consent gate**, separate from the integrator
   authorisation model already in `/keeper/authorizations`?

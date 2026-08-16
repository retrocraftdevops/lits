# Conformance

An integration is **conformant** when it implements the published contract and behaves as the
contract requires. Conformance is checked at two levels.

## 1. Contract validation (defined in CI; **run it by hand today**)

```bash
python3 scripts/validate.py
```

Checks every `openapi*.yaml` is valid OpenAPI 3.1, that all `$ref`s resolve, that the
`examples/` parse, and that open source files carry an SPDX licence header. This is the gate on
every change.

> **It is not currently running automatically.** GitHub Actions is disabled on this repository
> (`enabled: false`, zero workflow runs ever, verified 2026-08-16), so
> [`.github/workflows/validate.yml`](../.github/workflows/validate.yml) defines this gate but
> nothing executes it. Run it locally before you open a change. See
> [roadmap follow-up 2](../docs/roadmap.md#follow-up-still-open).

## 2. Live conformance

A black-box suite that exercises a running registry over the contract:

- per-operator bearer auth, and an acknowledgement ID on every write;
- `Idempotency-Key` honoured (a repeated key returns the original result);
- the public `GET /v1/verify/{token}` endpoint with no auth;
- every field the contract marks `required` is emitted;
- **an optional field stays optional.** A `POST /v1/vaccinations` body carrying only the fields
  required at `2.0.0` is still accepted at `2.1.0` — the guard that an "additive" release really
  was additive. Paired with its opposite: a body carrying every optional field
  (`lot_expiry`, `cold_chain_ok`, `cold_chain_evidence_ref`, `dual_id_confirmed`, `holding_id`,
  `zone_code`) is accepted and round-trips unchanged, so the fields are genuinely stored and not
  merely tolerated;
- **`cold_chain_ok: false` is the event that increments `CampaignProgress.cold_chain_exceptions`.**
  This is a cross-plane seam — a client-plane report driving a control-plane counter — so it is
  asserted end to end rather than on either side alone.
- **`GET /v1/movements/list?status=approved` returns items whose `status` is `approved`.** Against
  the `2.0.0`/`2.1.0` contract this was **unsatisfiable** — the endpoint accepted the filter while
  its response items were `MovementAck`, whose enum was `[lodged, blocked]` — so a conformant
  server could not answer the one poll integrators are told to run. Fixed at `2.1.1`; this is the
  regression case (RFC 0004 §8.6). It is a real test rather than decoration precisely because it
  could not have passed before the fix.
- **…and its guard: a `POST /v1/movements` acknowledgement is still only ever `lodged` or
  `blocked`** — likewise `POST /keeper/movements`. **The two cases must be run together.** The
  cheapest way to make the case above pass is to widen the shared `MovementAck`, which would hand
  back the very reading `3b8e917` was written to end: a client's own lodgement coming back
  authorised. This case is what refuses that shortcut, so a suite carrying only the first case is
  satisfiable by the wrong fix.

### Disease response orders (added at `2.2.0` — RFC 0003 §11)

Twelve cases. **Three of them are enforced today** by `scripts/validate.py` at the contract level
(marked **[gate]**, and each was proven able to fail by planting the regression in a scratch copy
— see [CHANGELOG](../CHANGELOG.md) `[2.2.0]`). **The other nine assert the behaviour of a running
registry or of a client, and nothing runs them yet**, because the live harness below does not
exist. They are written down so that the harness has a specification to satisfy rather than being
invented later from memory — but a case nothing executes is a plan, not a check, and it is listed
here as one.

1. `GET /v1/quarantine-orders?since_version=N` returns only orders with `order_version > N`, and a
   `server_version` not less than the highest returned. *(live)*
2. Replaying the same `since_version` twice returns the same set or a superset — **never a gap**.
   *(live)*
3. **A lifted order still appears in the delta** with `status: lifted`. *(live)* — **[gate]** at
   contract level: `examples/quarantine-order-delta.response.json` carries a `lifted` order, so
   removing `lifted` from `OrderStatus` fails `scripts/validate.py`. That proves the value is
   *expressible*; only the live case proves the registry *emits* it.
4. An active `standstill` order appears in `GET /v1/zones` as a zone with `zone_type: standstill`
   **and** `movement_restriction: blocked`, whose `zone_code` equals the order's
   `projected_zone_code`. *(live)* — **[gate]** for the schema half:
   `examples/standstill-zone-delta.response.json` is bound to `ZoneDelta`, so dropping `standstill`
   from `Zone.zone_type` fails the gate.
5. Lifting that order bumps the projected zone's `zone_version` and sets `effective_until`. *(live)*
6. **A client tolerates an unknown `zone_type`** without failing, provided `movement_restriction`
   is honoured. *(live, client-side)* This is the §4.2 cost made testable: `zone_type` gained a
   value at `2.2.0` and will gain more, so a client that switches on it exhaustively is the thing
   this case is looking for.
7. **A client treats an unknown `conditions[].code` as blocking.** *(live, client-side)* Asserts
   client behaviour, so it belongs in the client half of the suite. **Run it together with case 6**
   — they are the two halves of "unknown values are safe", and they resolve in *opposite*
   directions on purpose: an unknown `zone_type` must be tolerated, an unknown condition code must
   block. A suite carrying only one of them teaches the wrong general rule.
8. `POST /v1/movements` for an animal at a holding under an active order carrying
   `no_movement_on_off` is refused `409`. *(live)*
9. Authoring `scope: section` against a holding with no accepted biosecurity attestation returns
   `422 sections_not_declared`. *(live, control plane)* Until the attestation surface exists this
   is the **only** outcome, so the case is currently "always refuses" and will need tightening when
   step 4 lands — noted so it is not mistaken later for a passing case that measures a real choice.
10. **There is no client path by which a trace flag can be written** — an integrator key attempting
    one gets `404`/`405`, and the animal's `trace_flags` are unchanged. *(live)* The contract half
    is structural: `openapi.yaml` defines no write operation on `trace_flags` at all.
11. **A `TraceFlag` with `expires_at: null` is still returned, and still enforced, after any
    plausible expiry horizon** — the "null means lifelong" assertion made non-vacuous. *(live)* —
    **[gate]** at contract level: the trace-flag example carries `expires_at: null`, so making
    `TraceFlag.expires_at` non-nullable fails `scripts/validate.py`.
12. An order with neither `declared_verbally_at` nor `confirmed_in_writing_at` cannot reach
    `active` (`409` on `POST /admin/quarantine-orders/{id}/activate`). *(live, control plane)*

> **What no case here covers.** `AnimalRecord.trace_flags` has **no contract-level gate**:
> `AnimalRecord` is an `allOf`, and `scripts/validate.py`'s example checker does not understand
> `allOf`, so an example bound to it would be validated by a pass that inspects nothing. The
> trace-flag example is bound to `AnimalHealthStatus` instead, where the check genuinely recurses
> into `trace_flags[].code`. Case 10 is the only thing that covers the `AnimalRecord` side, and it
> is a live case, which is to say: nothing runs it today.

This harness is being extracted from the reference implementation into a standalone,
vendor-neutral runner. Until it lands, integrators self-test against the published contract and
a sandbox endpoint.

Only an **accredited, conformance-tested** integrator may present itself as official or display
the conformance mark — see [../TRADEMARK.md](../TRADEMARK.md).

<!--
SPDX-FileCopyrightText: 2026 The LITS steward
SPDX-License-Identifier: Apache-2.0
-->
# RFC 0002 — DPI interoperability adapters (the generic-REST contract)

- **Status:** Accepted (reference implementation)
- **Layer:** Platform mediator (`lits/interop.py`), tenant-scoped configuration
- **Related:** GovStack Information-Mediator / X-Road; RFC 0001 (qualified e-seals)

## Summary

A national registry must plug into national digital public infrastructure (DPI). LITS exposes one
**connector** per external service behind a single interface, each with a safe **mock** default so the
registry runs end-to-end before any real service is wired:

| Connector | Purpose |
|---|---|
| `national_id` | Verify a keeper's identity against the national ID system |
| `payments` | Collect fees/fines (invoice) and disburse insurance payouts (payout) |
| `business_registry` | Verify an establishment's legal entity |

Configuration is **per tenant** (each country wires its own endpoints, stored in that country's silo
database under `settings["interop"]`, secrets masked on read). When a connector has a live `endpoint`,
the mediator makes a **real JSON round-trip** to it; otherwise the deterministic mock runs. The single
network seam is `interop._http_post` (so it is trivially stubbed in tests and never hits the network
there).

## The live contract

The mediator `POST`s `application/json` to the configured `endpoint`.

**Auth headers** (when a credential is configured):

```
Authorization: Bearer <api_key>
X-Api-Key: <api_key>
X-Signature: <hmac-sha256(body, secret)>   # payments only, when a signing secret is set
```

**Request / response by connector:**

| Connector | Request body | Expected response |
|---|---|---|
| `national_id` | `{ "national_id_no": "...", "name": "..." }` | `{ "verified": true, "matched_name": "..." }` |
| `business_registry` | `{ "registration_no": "...", "name": "..." }` | `{ "verified": true, "matched_name": "..." }` |
| `payments` | `{ "operation": "invoice"\|"payout", "amount": 800, "currency": "USD", "reference": "...", "payer"\|"payee": "..." }` | `{ "id": "ext-123", "status": "issued"\|"disbursed" }` |

A single `payments` endpoint serves both operations, distinguished by the `operation` field.
`verified` is read leniently (`verified` or `valid`); the payment id is read from `invoice_id` /
`payout_id` / `id`.

## Failure semantics

A live call that errors (timeout, non-2xx, unparseable body) **degrades to an explicit failure** — it
never silently falls back to the mock:

- verify → `{ "verified": false, "source": "live", "error": "<service> call failed: …" }`
- payments → `{ "status": "error", "provider": "live", "error": "…", "<id>": null }`

This guarantees a caller (e.g. a lending payout, see `lending._adjudicate_and_pay`) can tell the
difference between "the rail accepted it" and "the rail rejected/was unreachable". Real disbursements
remain operator-gated; the adapter is never auto-fired against a live rail.

## Configuration & operations

- UI: **Administration → Interoperability** (`/interop`), gated `settings:write` (DVS-admin level).
- API: `GET /admin/interop` (masked view), `PATCH /admin/interop/{connector}` (set endpoint +
  credential; masked secret + `__KEEP__` sentinel preserved on re-save), `POST
  /admin/interop/{connector}/test` (live reachability probe, stamps `verified_at` on success).

## Non-goals (reference build)

- Per-country bespoke schemas — a country whose gateway differs maps to this envelope with a thin shim.
- Retries/circuit-breaking/queueing — a single timed round-trip; production hardening is out of scope.
- mTLS / OAuth client-credentials — the reference adapter uses Bearer + API key + optional HMAC; a
  production mediator can extend `_auth_headers`.

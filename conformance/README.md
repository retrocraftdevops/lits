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

This harness is being extracted from the reference implementation into a standalone,
vendor-neutral runner. Until it lands, integrators self-test against the published contract and
a sandbox endpoint.

Only an **accredited, conformance-tested** integrator may present itself as official or display
the conformance mark — see [../TRADEMARK.md](../TRADEMARK.md).

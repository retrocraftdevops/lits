# Conformance

An integration is **conformant** when it implements the published contract and behaves as the
contract requires. Conformance is checked at two levels.

## 1. Contract validation (runs in CI)

```bash
python3 scripts/validate.py
```

Checks every `openapi*.yaml` is valid OpenAPI 3.1, that all `$ref`s resolve, that the
`examples/` parse, and that open source files carry an SPDX licence header. This is the gate on
every change.

## 2. Live conformance

A black-box suite that exercises a running registry over the contract:

- per-operator bearer auth, and an acknowledgement ID on every write;
- `Idempotency-Key` honoured (a repeated key returns the original result);
- the public `GET /v1/verify/{token}` endpoint with no auth;
- every field the contract marks `required` is emitted.

This harness is being extracted from the reference implementation into a standalone,
vendor-neutral runner. Until it lands, integrators self-test against the published contract and
a sandbox endpoint.

Only an **accredited, conformance-tested** integrator may present itself as official or display
the conformance mark — see [../TRADEMARK.md](../TRADEMARK.md).

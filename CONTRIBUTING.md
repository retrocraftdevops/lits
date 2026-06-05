# Contributing to ZLITS

ZLITS is the **national registry contract** — the single agreement between the registry
and every client (FuroTrack and others). Changes here ripple to every integrator, so the
bar is deliberately high.

## Principles (do not regress)

- **Vendor-neutral.** No client (FuroTrack included) gets privileged fields, endpoints or
  semantics. If a change only helps one vendor, it does not belong in the contract.
- **The registry is the source of truth.** Clients submit and read; they never own the
  national identity, movement or health record.
- **Operator/State-owned.** Hosts are `*.gov.zw` (or the operator's domain) — never a
  vendor domain. Data governance follows the Cyber & Data Protection Act [Chapter 12:07]
  (POTRAZ): State as controller, operator as processor.

## Change policy (semantic, path-versioned)

The API is versioned in the path (`/v1`).

- **Additive / backward-compatible** (new optional field, new endpoint, new enum value
  that clients may ignore): allowed within the current version. Add a `### Added` entry to
  [CHANGELOG.md](./CHANGELOG.md).
- **Breaking** (removing/renaming a field, tightening a constraint, changing a status
  code or required-ness): requires a **new version** (`/v2`) — never mutate `/v1` in place.
- Every write endpoint keeps: per-operator bearer auth, an `Idempotency-Key`, and an
  acknowledgement ID in the response. These are load-bearing for client retry/circuit-breaker
  behaviour and must not be removed.

## Two specs

- **`openapi.yaml`** — the client API (integrators; `operatorApiKey`).
- **`openapi-admin.yaml`** — the control-plane API (Admin Portal; `adminSession`).

Keep them separate: integrator-facing operations belong in `openapi.yaml`, control-plane
operations (zone authoring, key issuance, audit) in `openapi-admin.yaml`. They are
independent (no cross-file `$ref`s).

## Quality gate (must pass before merge)

```bash
python3 scripts/validate.py        # openapi*.yaml + examples parse, $refs resolve, SPDX headers present
npx --yes @redocly/cli lint openapi.yaml openapi-admin.yaml
```

CI runs the same checks (`.github/workflows/validate.yml`). A PR that changes either spec
must:

1. Keep `scripts/validate.py` green (all `$ref`s resolve; OpenAPI 3.1; examples valid).
2. Update [CHANGELOG.md](./CHANGELOG.md).
3. Update any affected `examples/*.json` so they never drift from the contract.
4. For breaking changes, ship under a new `/vN` and say so in the PR description.

## Sign your work (Developer Certificate of Origin)

Every contribution is made under the [Developer Certificate of Origin](./DCO) (DCO 1.1).
Signing off certifies that you wrote the change — or otherwise have the right to submit it under
the project's licence ([Apache-2.0](./LICENSE) for the contract, [CC BY 4.0](./LICENSE-docs) for
prose). It is a lightweight alternative to a CLA that keeps the provenance of the open contract
clean and reinforces the patent grant.

Add a sign-off line to every commit:

```
Signed-off-by: Your Name <you@example.com>
```

`git commit -s` adds it automatically once `user.name` and `user.email` are set (both must be
real). By signing off you agree to the terms in [DCO](./DCO).

New source files should carry an SPDX header matching their licence, for example:

```
# SPDX-FileCopyrightText: 2026 The ZLITS steward
# SPDX-License-Identifier: Apache-2.0
```

## Ratification

The official acronym, the `national_id` numbering scheme, and production hosts are set with
the Department of Veterinary Services (DVS) / the delegated operator before `1.0.0` (non-draft)
is tagged. Until then the contract is `*-draft` and may change without a version bump.

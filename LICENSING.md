# LITS Licensing Map

LITS is **open as a standard, held as an implementation.** This repository therefore carries
more than one licence. This file is the authoritative, per-path statement of which licence
applies to what. Where a path is not listed, the most specific matching rule above it applies.

| Path | Licence | File |
|---|---|---|
| `openapi.yaml`, `openapi-admin.yaml` | **Apache-2.0** | [LICENSE](./LICENSE) |
| `examples/` | **Apache-2.0** | [LICENSE](./LICENSE) |
| `scripts/` (validator) | **Apache-2.0** | [LICENSE](./LICENSE) |
| `conformance/` (the conformance suite) | **Apache-2.0** | [LICENSE](./LICENSE) |
| `README.md`, `docs/`, `profiles/`, `CHANGELOG.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `TRADEMARK.md`, `SECURITY.md`, `PATENTS`, this file | **CC BY 4.0** | [LICENSE-docs](./LICENSE-docs) |
| The runnable **reference implementation, portals and operations** | **Source-available, held** — *not in this repo*; in a separate private repository | — |
| National **instance names** (ZLITS, MLITS, …) and the **conformance mark** | **Not** licensed by any of the above | [TRADEMARK.md](./TRADEMARK.md) |
| The **national herd data** (production) | Not in this repo; belongs to the **State** | — |

## Why this split

- **The contract is Apache-2.0** so any vendor can implement and integrate on equal terms, with a
  patent grant — that is what makes LITS a national *utility*, not a lock-in.
- **The conformance suite is Apache-2.0** so anyone can self-test their integration against the
  contract without permission.
- **The reference implementation and the portal are source-available but held** — readable, so
  integrators and auditors (and government) can verify there is no hidden behaviour, but **not**
  open-licensed: the right to *operate the national instance* flows from the State's mandate and the
  operator concession, not from possession of this code.
- **Data and the mandate are the State's** and are never licensed by a vendor.

Rationale and governance: [GOVERNANCE.md](./GOVERNANCE.md) and
[docs/spec-governance.md](./docs/spec-governance.md).

## Provenance

Open source files carry a machine-readable `SPDX-License-Identifier` header. Contributions are
signed off under the [Developer Certificate of Origin](./DCO) — see
[CONTRIBUTING.md](./CONTRIBUTING.md). The example payloads (`examples/*.json`) cannot carry a
comment header and are covered by the per-path table above.

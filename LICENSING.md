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
| `rfcs/` (RFCs — see [Why RFCs are Apache-2.0](#why-rfcs-are-apache-20-and-not-cc-by)) | **Apache-2.0** | [LICENSE](./LICENSE) |
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
- **RFCs are Apache-2.0**, not CC BY, because they carry normative schema that implementers build
  against — and CC BY grants no patent rights. See below.
- **Data and the mandate are the State's** and are never licensed by a vendor.

Rationale and governance: [GOVERNANCE.md](./GOVERNANCE.md) and
[docs/spec-governance.md](./docs/spec-governance.md).

## Why RFCs are Apache-2.0 (and not CC BY)

Recorded here in full so it is not relitigated. `rfcs/` sits at the awkward join: an RFC *reads*
like prose, which would sweep it into the CC BY row by content class, but it *contains* field-level
schema that vendors implement.

**The decisive reason is the patent grant.** This repository ships a patent non-assertion covenant
([PATENTS](./PATENTS)) precisely so a competitor can invest in implementing the contract without
fear of a patent ambush — [GOVERNANCE.md](./GOVERNANCE.md) §3 calls that a one-way ratchet.
**CC BY 4.0 grants no patent rights at all** — its § 2(b)(2) says so in terms: *"Patent and
trademark rights are not licensed under this Public License."* Publishing implementable normative
text under CC BY would therefore let the part implementers actually build against travel *without*
the protection this repo exists to provide — the one combination the whole open-standard posture is
designed to prevent.

Three further things point the same way:

- [docs/spec-governance.md](./docs/spec-governance.md) §2 already states the rule: a national
  standard that others implement needs an explicit patent grant, and CC-BY "is *not* designed for
  things that are implemented as code." An RFC carrying a schema sketch is a thing implemented as
  code.
- **Four of the five files had already converged on it.** `rfcs/0001`, `0003`, `0004` and `0005`
  each carried an `SPDX-License-Identifier: Apache-2.0` header written by hand, with no rule
  telling anyone to. That is evidence of the drafters' intent, and it is now the stated rule.
- **One licence for the whole implementable surface** means an integrator never has to work out
  which paragraph of which file arrived under which terms. RFC 0004's request fields and the
  `openapi.yaml` schema they become are governed identically.

**What this does not change.** Narrative documentation stays CC BY 4.0 — `README.md`, `docs/`,
`profiles/`, and the governance files — because attribution-only is what lets the State, donors and
integrators quote and republish the *design* freely. The line is implementability, not file format:
`docs/roadmap.md` describes what may be built, an RFC specifies it.

`rfcs/0002` carried no header at all until 2026-08-16, and the gate could not have told anyone:
`scripts/validate.py`'s SPDX check did not glob `rfcs/` and read only five files. It does now, so
this rule is enforced rather than merely written down.

## Provenance

Open source files carry a machine-readable `SPDX-License-Identifier` header. Contributions are
signed off under the [Developer Certificate of Origin](./DCO) — see
[CONTRIBUTING.md](./CONTRIBUTING.md). The example payloads (`examples/*.json`) cannot carry a
comment header and are covered by the per-path table above.

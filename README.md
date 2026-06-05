# LITS — the open standard for national livestock identification & traceability

**A vendor-neutral API contract for a national livestock registry — the source of truth for
animal identity, movement and health events.**

> **Status: DRAFT.** This repository is the open **standard** — the API contract, conformance
> and governance. It is not a running service. Each nation runs its own registry on its own
> government domain; this contract is what those registries, and every client integration,
> build against.

## What LITS is (and is not)

LITS is an **open standard**, not a product, and not owned by any software vendor. A national
instance — for example **ZLITS** (Zimbabwe) or **MLITS** (Malawi) — is the same standard run
for one country, on its own `*.gov.<cc>` domain, by its delegated operator. Farm apps,
abattoirs, auctions and veterinary offices connect to it as **clients**.

- **Open the standard; hold the implementation; the State owns the data and the mandate.**
- The contract is Apache-2.0, so any vendor integrates on equal terms — no lock-in.
- "ZLITS" / "MLITS" and the conformance mark are trademarks; "LITS" is the common name of the
  category, used descriptively — see [TRADEMARK.md](./TRADEMARK.md).

## Repository layout

| Path | What |
|---|---|
| `openapi.yaml` · `openapi-admin.yaml` | the client and control-plane API contracts |
| `examples/` | sample request / response payloads |
| `scripts/validate.py` | the contract self-test (the CI quality gate) |
| `conformance/` | how an integration proves conformance |
| `docs/` | spec governance, registry operations, the integration guide |
| `profiles/<cc>/` | per-country **open** profile: official acronym, ID numbering, zones, legal basis |

The runnable **reference implementation, portals and operations** are held privately by the
operator — they are *not* in this repository. Only the contract and conformance suite are open.

## Licensing & governance

- Contract, examples, validator, conformance suite — **Apache-2.0** ([LICENSE](./LICENSE)).
- Documentation — **CC BY 4.0** ([LICENSE-docs](./LICENSE-docs)).
- Names & conformance mark — trademarks ([TRADEMARK.md](./TRADEMARK.md)).
- Patent non-assertion covenant — [PATENTS](./PATENTS). Contributions are made under the
  [Developer Certificate of Origin](./DCO); see [CONTRIBUTING.md](./CONTRIBUTING.md).

Stewardship of the standard is committed to transfer to the State / a neutral national body on
official designation — see [GOVERNANCE.md](./GOVERNANCE.md).

## Validate

```bash
python3 scripts/validate.py
```

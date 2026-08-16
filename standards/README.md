# Standards control vocabulary

`vocabulary.v1.json` is the shared schema behind the standards registers of four related
codebases. It is **byte-identical in every repo**; each repo hashes it and fails CI on drift.

| Repo | Register | Validated by |
|---|---|---|
| FuroField (crop) | `apps/app/lib/standards/` (TypeScript) | `apps/app/lib/__tests__/standards.test.ts` |
| FuroTrack (livestock + shared engine) | `apps/api-core/furotrack_api/standards/` (Python) | `tests/test_standards_registry.py` |
| LITS (open standard) | `standards/registry.yaml` | `scripts/validate.py` |
| Dzinza (held platform) | `platform/lits/standards.py` + `standards/registry.yaml` | `platform/tests/test_standards_registry.py` |

## Why a vocabulary and not four documents

Each repo already carried standards claims as prose in markdown tables. Prose drifts: a control can
regress in code while every document still says "Implemented", and the FuroTrack↔LITS interchange
enums were pinned by hand with drift *declared* a conformance failure but never *detected*. A
register that code reads and tests enforce closes both.

## The rules the schema encodes

1. **Certification is external.** `status: external_assessment` means the controls are in place and
   an accredited third party has not been engaged. It is never rendered as "certified" or
   "compliant" — the honesty guard in each repo fails the build if it is.
2. **Normative text is copyrighted.** ISO, GLOBALG.A.P., GS1 and Codex texts may not be reproduced.
   A control carries a **clause identifier** (a fact), **our own paraphrase**, and a **citation
   URL**. The copyright guard enforces the paraphrase.
3. **A claim needs a proof.** `implemented` requires both `codePaths` and `testRefs`; `partial`
   requires `codePaths`. The coverage gate additionally checks each path still exists.
4. **"Not applicable" needs a reason.** A bare N/A is rejected; the note must say why.
5. **Evidence carries a tier.** `derived | attested_import | declared`, the ladder already used
   across these products. A roll-up inherits the weakest tier present.
6. **Seams are pinned.** `seamPin` names an interchange vocabulary shared across repos (e.g.
   `es-attestation-category`, `eudr-geometry`); the cross-repo parity check asserts both sides agree.

## Changing the vocabulary

The version is `1.0.0`. A backwards-compatible addition bumps the minor version **in all four repos
in the same change**; anything that invalidates an existing register is a major version and needs
the same treatment. Editing this file in one repo alone will fail that repo's parity test and every
other repo's cross-repo check — which is the point.

## Verify

Two checks, and they answer different questions. Run both before changing a pin.

### This repo's own gate — runs in CI

```bash
python3 scripts/check-standards-parity.py                 # in CI; no dependencies, no siblings needed
python3 scripts/check-standards-parity.py --require-siblings   # locally, when adding a seam pin
```

Wired into [`.github/workflows/validate.yml`](../.github/workflows/validate.yml) alongside
`scripts/validate.py`. It hashes this repo's `vocabulary.v1.json` against a canonical digest
recorded in the script, checks the structure the rest of the gate depends on, ties
`registry.yaml` to it, and — **when sibling checkouts happen to be present** — compares their
copies and checks each `seamPin` is named on at least one other side.

A CI runner has only this repository, so there the run reports **`PASS (SELF-CHECK ONLY)`** and
lists every sibling as `NOT COMPARED`. That wording is deliberate: an absent repo must never read
as an agreeing repo. `--require-siblings` turns absence into a failure for the local case where
you expect all four.

**Its honest limit:** a digest recorded in the same repo as the file it pins can be updated in the
same edit. It catches the *silent* drift — a reformat, an editor rewriting the file, a hand-merged
conflict — while a *deliberate* change is caught by the version-bump rule above, which check 3
ties to the register and the four-way check below ties to the siblings.

### The four-way check — lives in FuroField, reads all four

```bash
~/projects/FuroField/scripts/check-standards-parity.sh   # hashes the vocabulary + compares pinned SEAM VALUES across repos
```

It is not in this repository, and deliberately not copied into it: a fourth copy of the four-repo
topology is the exact drift this program exists to detect. It stays authoritative for the per-seam
**value** assertions (the EUDR hectare threshold and decimal precision, the E&S category enum) that
the gate above does not attempt. It is written to run from any of the four repos.

> The path above was once written `scripts/check-standards-parity.sh`, as though the file were
> here, which made it unrunnable from this repo and made the check look absent. It is not absent.

### Last run

2026-08-16 from a clean tree, **both green**. The four-way script: vocabulary hash
`737b5e9f…44e572a4` identical across FuroField, furotrack, lits and dzinza; both pinned seams
present on both sides; declared version `1.0.0` everywhere. This repo's gate: the same digest,
4 sibling copies compared and identical, both seam pins named by FuroField, the engine and Dzinza.

Both were proved capable of failing before being trusted, against **copies** — nothing in this
repository was mutated. For this repo's gate that was five separate plants in a detached worktree
(drifted own vocabulary, deleted `$defs.Status.enum`, a drifted sibling copy, a seam pin no
sibling carries, and `--require-siblings` with none present); each exited 1 naming the file or the
pin, and each restored to exit 0.

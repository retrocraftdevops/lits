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

**The script is not in this repository.** It lives in the FuroField repo and is written to be run
from any of the four — it locates its siblings relative to the parent directory. Invoke it by path:

```bash
~/projects/FuroField/scripts/check-standards-parity.sh   # hashes the vocabulary + compares pinned seams across repos
```

This line previously read `scripts/check-standards-parity.sh`, as though the file were here.
`scripts/` in this repo contains only `validate.py`, so the command could not run and the section
promised a check nobody could perform. FuroTrack's copy of this README already cites the absolute
path; this one now matches it.

Last run 2026-08-16 from a clean tree: **PASS** — vocabulary hash
`737b5e9f…44e572a4` identical across FuroField, furotrack, lits and dzinza; both pinned seams
(`eudr-geometry`, `es-attestation-category`) present on both sides; declared version `1.0.0`
everywhere. The check was proved capable of failing in the same session by mutating a **copy** of
this repo's `standards/vocabulary.v1.json` and re-running against it: it named the drifted file,
printed both hashes, and exited 1.

**What is still true, and is a real gap:** this repository's own CI
([`.github/workflows/validate.yml`](../.github/workflows/validate.yml)) has **no parity step**, so
nothing here detects drift automatically — see [`docs/roadmap.md`](../docs/roadmap.md) §"Follow-up
still open".

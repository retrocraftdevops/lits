# LITS Governance

This is the repository-root governance statement for the LITS national livestock registry
**contract**. The rationale behind these rules — and the decisions they encode — is in
[docs/zlits-spec-governance.md](./docs/zlits-spec-governance.md); the day-to-day change
mechanics are in [CONTRIBUTING.md](./CONTRIBUTING.md). This file is the canonical, citable
policy.

## 1. Principle

**Open the standard; hold the implementation; the State owns the data and the mandate.**

The contract is published openly so any vendor integrates on equal terms and no government is
locked in. The right to *operate* the national registry comes from the State's mandate and the
operator concession — never from possession of the spec. See [LICENSING.md](./LICENSING.md) for
the per-path open-vs-held map.

## 2. Stewardship — and the handover commitment

| Phase | Steward | Decision rights |
|---|---|---|
| **Pre-designation (today)** | The current steward (the contract's author/operator-candidate) | Authors v1 under the change policy below; runs the repo, CI and conformance gate |
| **On designation** | A **joint steering committee**: DVS (chair) + the delegated operator + an integrator seat | Approves sovereign-impacting changes; ratifies the official acronym, the `national_id` numbering scheme and production hosts |
| **Mature** | DVS / a neutral national body holds the standard; operator and vendors contribute | Long-run neutrality and export-market credibility |

> **Handover commitment.** Stewardship of, and copyright in, the LITS *contract* (the
> Apache-2.0 and CC-BY artifacts) **transfer to the State / a neutral national body on official
> designation** of the registry and its operator. This is committed now, in writing, because the
> standard must visibly not be "the vendor's." It costs the steward nothing it needs to keep:
> stewardship of the *standard* is separate from operation of the *instance* (held under the
> concession — see [LICENSING.md](./LICENSING.md)).

## 3. Patent non-assertion covenant

In addition to the patent grant in the Apache License 2.0 covering contributed code, the steward
and contributors covenant **not to assert any patent essential to implementing the published
LITS contract** against any conformant implementation, for as long as that implementation
remains conformant. This lets a competitor invest in integrating without fear of a patent
ambush, and is a deliberate, low-cost trust signal to government and to rival vendors.

The **canonical covenant text** — with definitions, defensive-suspension terms and the
Apache-2.0 relationship — is in [PATENTS](./PATENTS). This section is a summary; PATENTS controls.

## 4. Change & decision process

- **Path-versioned, semantic policy.** Additive, backward-compatible changes are allowed within
  `/v1`; breaking changes ship only under a new `/vN`. Full rules: [CONTRIBUTING.md](./CONTRIBUTING.md).
- **Quality gate on every change.** `scripts/validate.py` + `@redocly/cli lint`, enforced in CI
  ([.github/workflows/validate.yml](./.github/workflows/validate.yml)), plus the conformance gate
  (the conformance suite) that ties the live service to the contract so they
  cannot drift. A change that fails any gate does not merge.
- **RFC for sovereign-impacting changes.** Anything touching identity numbering, certificate
  semantics, zone authority, the two-plane split, or personal-data fields requires an RFC decided
  by the steering committee (§2) — never by a single vendor. Smaller additive changes follow the
  normal PR + CHANGELOG flow.
- **Vendor-neutrality is non-regressable.** Per [CONTRIBUTING.md](./CONTRIBUTING.md): if a change
  only helps one vendor, it does not belong in the contract.

## 5. Conformance & accreditation

Open to build on; impossible to impersonate:

- **Anyone** may read and implement the contract and run the conformance suite.
- **Only an accredited, conformance-tested integrator** with a live, per-operator API key issued
  through the Admin Portal may operate against the production registry, call itself
  **"ZLITS-conformant"**, or display the conformance mark (see [TRADEMARK.md](./TRADEMARK.md)).
- Accreditation + per-key attribution + the immutable audit trail are how the registry stays
  **open yet accountable** (see [docs/registry-operations.md](./docs/registry-operations.md) §7).

## 6. Data protection

The production registry holds personal data under the Cyber & Data Protection Act [Chapter 12:07]
(POTRAZ): the **State is controller**, the **operator is processor**. Governance of the *contract*
(this repo) does not convey any right over production data.

## 7. Amending this governance

Changes to this file follow the same PR + review flow as the contract and, once a steering
committee exists (§2), require its approval. Until designation, the steward may amend it but may
not weaken the handover commitment (§2) or the patent covenant (§3) — those are one-way ratchets.

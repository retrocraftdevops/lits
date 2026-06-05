# LITS Spec Governance — Open Standard, Held Implementation

How the LITS contract is **licensed, governed and published** so it is a credible national
utility — open enough that any vendor can integrate and government cannot be locked in, yet
structured so the operator's investment and the State's sovereignty are both protected.

> Status: DRAFT policy. Pairs with registry operations (in the private platform repo) (the
> two-plane model) and [../CONTRIBUTING.md](../CONTRIBUTING.md) (the change policy this formalises).

---

## 0. The principle in one line

**Open the standard; hold the implementation; the State owns the data and the mandate.**

Vendor-neutrality is not a slogan — it is the property that makes LITS adoptable as a *national
utility* rather than one company's lock-in. The contract is therefore published under an open
licence so competitors integrate on equal terms. That openness costs the operator nothing it needs
to keep, because **the right to *operate* the national registry comes from the State's mandate, not
from possession of the spec.**

---

## 1. What is open vs. what is held (the line)

| Artifact | Disposition | Licence |
|---|---|---|
| **API contract** — `openapi.yaml`, `openapi-admin.yaml`, `examples/` | **Open** | Apache-2.0 (incl. patent grant) |
| **Prose docs** — `README`, `docs/*.md` | **Open** | CC-BY-4.0 |
| **Conformance suite** — the conformance suite | **Open** (so anyone can self-test) | Apache-2.0 |
| **Reference implementation** — runnable service + Admin Portal (held privately) | **Source-available, held** | Proprietary; licensed to the operator under the partnership agreement — *not* an open licence |
| **Hardened / operational platform** (scale, security, deployment, signing) | **Held** | Proprietary (NewCo / operator) |
| **The "ZLITS" name & marks** | **Held** | Trademark — *not* covered by the open licence (see §3) |
| **The national herd data** | **State's** | Not licensable by any vendor; POTRAZ controller/processor |

Rule of thumb: **anything another vendor needs in order to *integrate* is open; anything needed to
*operate the sovereign instance* is held or belongs to the State.**

## 2. Licence choice — and why Apache-2.0 for the spec

- **Apache-2.0 for the contract and conformance suite.** A national standard that others implement
  needs an **explicit patent grant** so no contributor (or the author) can later ambush implementers
  with a patent claim. Apache-2.0 provides that, stays permissive, and is well understood by
  procurement and legal reviewers. CC-BY is fine for prose but is *not* designed for things that are
  implemented as code, so use it only for the narrative docs.
- **CC-BY-4.0 for prose docs** — attribution-only; lets the State, donors and integrators quote and
  republish the design freely.
- **Proprietary for the implementation.** The reference implementation may be *source-available*
  (readable, so integrators and auditors can verify behaviour and government can see there is no
  hidden back door) **without** being open-licensed. Readability builds trust; the licence still
  reserves the right to operate and to reuse the engine regionally. Open-core later is optional, never
  required.

> Replace the placeholder in [../README.md](../README.md) ("License: To be set by the operator /
> State") with: **the contract under Apache-2.0, prose under CC-BY-4.0, the reference implementation
> under a separate source-available licence.** Add `LICENSE`, `LICENSE-docs`, and a `NOTICE` file.

## 3. Trademark — open spec, controlled name

Openness applies to the **specification**, never to the **name**. The "ZLITS" word-mark and the
conformance badge are **held by the State / delegated operator** and licensed only to **accredited**
integrators. This is what keeps an open standard accountable:

- Anyone may **read and implement** the contract.
- Only an **accredited, conformance-tested** integrator with a live API key may call itself
  **"ZLITS-conformant"** or display the badge.
- A non-accredited fork may implement the API but **may not present itself as the national system** —
  that protects keepers, abattoirs and border officers from spoofed "official" certificates.

Open spec + trademark + accreditation = **open to build on, impossible to impersonate.**

## 4. Patent & non-assertion covenant

In addition to the Apache-2.0 grant on contributed code, the spec stewards publish a **non-assertion
covenant**: the steward and contributors will not assert patents **essential to implementing the
published contract** against any conformant implementation. This is the standards-world norm (it is
what lets a competitor invest in integrating without fear) and it is a cheap, high-trust signal to
government and to rival vendors.

## 5. Stewardship — who governs the spec, and the handover commitment

| Phase | Steward | Why |
|---|---|---|
| **Today (pre-mandate)** | NewCo, in the open repo, under [CONTRIBUTING.md](../CONTRIBUTING.md) | Someone must author v1; the repo, CI and conformance gate already enforce discipline |
| **On designation** | A **joint steering committee** — DVS (chair) + delegated operator + an integrator seat | Sovereign data belongs to the State; the standard must visibly not be "the vendor's" |
| **Mature** | DVS / a neutral national body holds the spec; operator and vendors contribute | Long-run neutrality and export-market credibility |

**The credibility move:** commit *in writing, now* that **spec stewardship transfers to the State /
a neutral board on designation.** That single commitment is what converts "FuroTrack's API" into "the
national standard" in a government reviewer's mind — and it is free to give, because stewardship of
the *standard* is separate from operation of the *instance* (which remains the operator's under the
concession).

## 6. Change process (formalising CONTRIBUTING.md)

The mechanics already exist in the repo; governance simply names who decides:

- **Path-versioned, semantic change policy** — additive changes within `/v1`; breaking changes only
  under a new `/vN`. (See [CONTRIBUTING.md](../CONTRIBUTING.md).)
- **Quality gate on every change** — `scripts/validate.py` + `@redocly/cli lint`, enforced by
  [`.github/workflows/validate.yml`](../.github/workflows/validate.yml), plus the conformance gate
  (the conformance suite) that ties the live service to the contract so they
  cannot drift.
- **RFC for sovereign-impacting changes** — anything touching identity numbering, certificate
  semantics, zone authority or data fields goes through the steering committee, not a single vendor.
- **Public CHANGELOG** — every change recorded; integrators rely on it.

## 7. How to publish credibly (checklist)

A short, concrete list that makes the openness *verifiable* rather than asserted:

- [ ] Add `LICENSE` (Apache-2.0), `LICENSE-docs` (CC-BY-4.0) and `NOTICE`.
- [ ] Add a `GOVERNANCE.md` stating the stewardship phases (§5) and the **handover-on-designation**
      commitment.
- [ ] Add the **patent non-assertion covenant** (§4) to `GOVERNANCE.md` or a `PATENTS` file.
- [ ] Publish the **conformance suite** and a one-command "test your integration" path.
- [ ] Host the spec at a **neutral home** (an operator/State domain, e.g. `spec.zlits.gov.zw`, or a
      clearly-labelled neutral repo) — never a vendor domain.
- [ ] State plainly in the README: **spec open; implementation held; data and mandate the State's.**
- [ ] Keep the **trademark/accreditation** terms in a `TRADEMARK.md` so "open" never means "anyone may
      pose as official."

## 8. Why this satisfies everyone at once

- **Government / DVS:** no lock-in (open contract, conformance suite, committed stewardship handover,
  escrowed continuity in the operating agreement) — adoptable as sovereign infrastructure.
- **Competitor vendors (incl. ICEcash):** can integrate on equal terms, with a patent covenant — so
  they have little reason to lobby against it and a clear path to participate.
- **The operator (NewCo):** keeps the implementation IP, the regional rights and the operating
  concession — the moat is operation, which open-licensing the *standard* does not touch.

---

*Companion (commercial, held privately): the LIT Heads of Terms — how the implementation is licensed
and the operator economics secured. Background: the Zimbabwe national-traceability strategy brief.*

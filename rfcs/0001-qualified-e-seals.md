<!--
SPDX-FileCopyrightText: 2026 The LITS steward
SPDX-License-Identifier: Apache-2.0
-->
# RFC 0001 — Qualified electronic seals (eIDAS) on certificates

- **Status:** Draft (pending steering-committee ratification per GOVERNANCE.md §"RFC for
  sovereign-impacting changes" — this touches **certificate semantics**).
- **Affects:** `openapi.yaml` (client/verification) 1.7.0-draft, `openapi-admin.yaml` 1.4.0-draft.
- **Backwards compatibility:** Additive only. No field is removed, renamed, or made required; existing
  signature verification (`signature` / `signing_key_id` / `GET /v1/keys`) is unchanged. Clients that
  ignore the new fields keep working.

## Motivation

A LITS certificate is signed with the issuer's Ed25519 key and verified against the key published at
`/v1/keys`. That is an **advanced** electronic seal: cryptographically authentic, but a foreign
authority cannot, offline, establish *which* authority the key belongs to, *when* the seal was made,
or whether the seal certificate was *revoked*. WOAH-PVS "official certification" and cross-border
recognition (the strategy's §5a moat) require a **qualified** electronic seal — the eIDAS / ETSI
construct importing authorities already know how to validate.

## Design

The qualified seal **wraps** the existing detached signature (it does not replace it) with the three
things a qualified seal adds, modeled in software (no external QTSP/HSM; production swaps software
keys for a KMS/HSM and the JSON certificates for X.509):

1. **Certificate chain to a national trust anchor.** A self-signed national root signs the issuer's
   **qualified seal certificate** (binding the published signing key, with eIDAS QC statements). A
   verifier validates against a *trusted root*, obtained from the **Trusted List** (EU LOTL pattern,
   `GET /v1/trust-list`), not a bare key.
2. **Qualified timestamp.** An internal time-stamp authority signs each seal (RFC-3161 spirit),
   giving proof-of-existence so an expired-but-timestamped seal still validates.
3. **Long-term validation data.** Level **LT** embeds the trusted-list reference + revocation snapshot
   so a border post verifies **fully offline**.

ETSI baseline levels **B / T / LT** are modeled (issuance defaults to **LT**). Verification emits an
**ETSI TS 119 102-1** report: `TOTAL_PASSED` / `INDETERMINATE` / `TOTAL_FAILED` with a sub-indication
(`SIG_CRYPTO_FAILURE`, `NO_CERTIFICATE_CHAIN`, `REVOKED`, `EXPIRED`, `OUT_OF_BOUNDS_NO_POE`,
`FORMAT_FAILURE`).

## Contract changes

- `Certificate`: add optional `seal` (`QualifiedSeal`) and `seal_level` (`B|T|LT`).
- `VerificationResult`: add optional `seal_level` + compact `seal` status.
- New schemas: `QualifiedSeal`, `SealValidationReport`, `TrustList`.
- New public paths: `GET /trust-list`, `POST /seals/verify`.
- New control-plane paths (`openapi-admin.yaml`): `GET /admin/trust`, `GET /admin/trust/list`,
  `POST /admin/trust/verify` (`trust:read`); `POST /admin/trust/seals/rotate`,
  `POST /admin/trust/seals/{serial}/revoke` (`trust:manage`).

## Security & sovereignty

The trust anchor and TSA keys are per-tenant sovereign material (`LITS_TRUST_ANCHOR_KEY`,
`LITS_TSA_KEY`); the Trusted List is per-territory. Revocation is the registry's act. Nothing here
changes the two-plane split or `national_id` numbering. Production hosting of the anchor key (HSM/KMS,
rotation cadence) and any mutual-recognition agreement with a peer territory's Trusted List are
operational decisions for the steering committee.

## Open questions for ratification

- Anchor key custody + rotation cadence in production (HSM/KMS).
- Whether to publish under the ETSI TS 119 612 trusted-list XML profile in addition to the JSON form.
- Cross-recognition: importing a peer territory's Trusted List as a trusted root.

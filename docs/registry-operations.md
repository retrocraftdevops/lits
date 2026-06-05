# ZLITS Registry Operations & Administration

How the national registry is operated: who creates zones, who runs the portal, how
certificates are issued, who audits, and which user interfaces are surfaced. Decisions
here follow the practice of mature national systems — **EU TRACES NT**, Australia **NLIS**
and New Zealand **NAIT** — adapted to Zimbabwe's legal framework (see
[../README.md](../README.md) and the partnering strategy brief).

> Status: DRAFT design. Pairs with the API contract in [../openapi.yaml](../openapi.yaml).

---

## 0. The two-plane model (the rule everything else follows)

| Plane | What it is | Who runs it | Where |
| --- | --- | --- | --- |
| **Registry control plane** | the sovereign system of record + its admin portal, public verification, certificates, audit | DVS / delegated operator | **ZLITS** (`*.gov.zw`) |
| **Client plane** | farmer/field capture apps that push events and render certs | accredited vendors (FuroTrack and others), on equal terms | each vendor |

The registry is the source of truth; clients submit and read. No client — FuroTrack
included — gets privileged data, endpoints or rendering authority. This is what makes the
system a national utility rather than a vendor lock-in.

---

## 1. Who creates zones, and how

Veterinary / FMD zones are **sovereign regulatory data** — declared by the authority and
gazetted under the **Animal Health Act [Chapter 19:01]**. Therefore:

- **Author:** DVS and Provincial Veterinary Officers, in the **ZLITS Admin Portal** (§3).
  A zone carries `{zone_code, zone_name, zone_type, movement_restriction, boundary_wkt?,
  effective_from/until, source_reference (gazette), zone_version}`.
- **Outbreak fast-path:** an authorised vet declares an FMD/quarantine zone in the portal;
  the change bumps `zone_version` immediately so every field device pulls it on next sync.
- **Distribution, not authorship, for everyone else:** clients consume zones via
  `GET /v1/zones?since_version=N` and never author them. The monotonic `zone_version` gives
  conflict-free delta sync to offline field devices.

> Migration note for FuroTrack: today FuroTrack can *create* zones locally. For
> ZLITS-governed Zimbabwe that authorship moves to the ZLITS portal; FuroTrack becomes
> read-only on national zones (its `fmd_zone_sync` consumer ingests the `/v1/zones` feed
> unchanged). Otherwise two competing zone truths emerge.

---

## 2. Should there be a management portal? Yes — it is mandatory

A national registry cannot be API-only; the authority's staff need a console, and both
NLIS and NAIT ship a first-party portal alongside their API ecosystem. The **ZLITS Admin
Portal** is part of the registry service (its own app, `*.gov.zw`) — **not** a screen in
any vendor's product.

---

## 3. The ZLITS Admin Portal — modules

Screen designs (ASCII mockups) with per-screen endpoint mappings and RBAC are in
[admin-portal.md](./admin-portal.md).

| Module | Purpose |
| --- | --- |
| **Zones** | declare / update / expire zones; outbreak fast-path; map + table view |
| **Integrators & API keys** | accredit a vendor; issue / rotate / revoke per-operator keys; usage & quotas |
| **National herd & lookup** | search any animal / holding / movement / certificate across all submissions |
| **Certificates** | issue, render, sign, reissue, revoke; manage official templates (§4) |
| **Schedule & dispatch** | schedule vet visits/inspections; assign officers (jurisdiction + workload); month calendar + subscribable `.ics` feed; email + in-app reminders. Completing an inspection visit records the inspection that releases the certificate (§4) |
| **Holdings & keepers** | register premises and keepers; the `holding_id` namespace |
| **Disease-control campaigns** | vaccination campaigns, coverage, due/overdue |
| **Audit & exports** | immutable action log, data-access log, signed audit exports (§6) |
| **Reports & analytics** | jurisdiction-scoped statistical rollups (herd by province/species, movement pipeline, certificate issuance, vaccination coverage, data quality) with **CSV / PDF / JSON** export · `GET /admin/reports`, `/admin/reports/{id}`, `/admin/reports/{id}/export?format=` |
| **Service health** | submission throughput and error rates per integrator |

---

## 4. Certificates — issued and signed by the registry (printable + API)

> **Implemented (delegated approval).** In `reference-impl/`, integrators may only *request*
> a certificate (`POST /v1/certificates` → status `requested`, unsigned). Only the authority
> (Official Vet / DVS) *issues & signs* it (`POST /admin/certificates/{id}/issue`) and *revokes*
> it — mirroring EU TRACES Part I (operator) / Part II (competent authority). An integrator key
> can never mint a sovereign document.
>
> **Certifiability gating (the substantive basis).** Signing is not a one-click mint: it models
> the real veterinary act. `cert_workflow.evaluate()` runs a **per-kind requirement checklist**
> — identity & registration, registered/active holding, origin-zone clear of restriction,
> vaccinations valid, and (export) negative lab tests within validity — and a **recent physical
> inspection** must be recorded (`POST /admin/certificates/{id}/inspection`; export requires a
> *designated inspection point*). The vet then **attests a standardized declaration under their
> registration number**; the attestation is **bound into the signed payload** and printed on the
> certificate. Unmet requirements **block** issuance unless **overridden with a documented,
> audited reason**. This makes legitimacy *"these conditions were verified, this inspection
> happened, this declaration was made"* — not *"a vet clicked sign."*
>
> **Multi-step approval (maker-checker, segregation of duties).** Higher-risk certificates use a
> tiered approval matrix (the four-eyes principle). **Movement permits & domestic health** are a
> single signing step. **Export** is two steps with **segregation of duties** — an *issuing
> veterinarian* inspects, attests and **recommends**, then a *different, senior competent
> authority* **endorses** (counter-signs), which issues the certificate (the USDA VEHCS / UK EHC
> model). A step may **reject** (terminal) or **return** for more information; every decision is
> recorded (who / when / comment) for audit. Workflows are **data-driven**, tiered by **kind and
> consignment size** — a consignment over ~50 head escalates a *domestic* certificate to
> maker-checker too. **Every certificate type is governed by its own independent policy**,
> configured by the tenant authority (Administration → Approval policy: per kind — require
> endorsement, the escalation threshold, and **which roles may recommend vs. endorse**;
> `GET /admin/approval-policy`, `PATCH /admin/approval-policy/{kind}`, DVS-admin only) — a
> sovereign decision, not the platform's. When a step advances
> the **next approver is emailed + notified in-app** (via the Postmark integration). Endpoints:
> `GET /admin/certificates/{id}/workflow`, `POST /admin/certificates/{id}/approve`.
>
> **Subjects — per animal or per consignment.** A certificate's subject is a single **animal**
> or a **consignment** (a batch/herd certified together; movement permits group by the movement).
> The certifiability checks run **per animal across the batch**, the consignment size drives the
> maker-checker escalation, and the PDF lists the consignment reference + its member IDs — one
> certificate for a truckload, not 200 certificates. `POST /admin/consignments` defines a batch.

**Decision (best practice, TRACES-aligned):** ZLITS is the **issuer and signer** of the
authoritative certificate, and renders the **canonical printable PDF centrally**. EU
TRACES NT generates each certificate in-system, auto-creating the QR code and official
reference number and applying the competent authority's electronic signature — the
authority renders the official artifact; it is **not** rendered per-vendor.

So ZLITS provides all of:

1. **Signed structured data** via API — the machine interface and the root of trust.
2. **A canonical, formatted PDF** (movement permit, health/veterinary certificate, export
   certificate) generated by the registry, with:
   - an auto-generated **official reference number**,
   - a **QR code** resolving to the public `GET /v1/verify/{token}` endpoint, and
   - the **competent authority's e-signature** (the registry holds the signing key).

   In the reference impl, `GET /v1/certificates/{id}/pdf` renders this as a **true A4 PDF**
   (`application/pdf`) via ReportLab — an authority header + national emblem, the particulars
   grid (subject / holding / movement / validity), an endorsement block with an embossed
   department seal, the verification QR, and the full HMAC signature printed in a security
   footer. State is reflected on the artifact itself: **VALID / EXPIRED / REVOKED** (red
   overstamp) / **PENDING** (an unsigned request shows no QR and is marked "not a valid
   instrument"). ReportLab/qrcode are imported lazily; the endpoint degrades to a plain HTML
   record if they are unavailable. See `reference-impl/zlits/certificate_pdf.py`.
3. **Public verification** — anyone scans the QR and sees the authoritative status with no
   login and no dependence on any vendor.

Clients (FuroTrack and others) may *fetch, embed and print* the registry-signed certificate
and may show a preview, but they **do not mint their own "national" certificates** — that
would re-introduce a competing authority and break recognisability at borders/abattoirs.
The signed payload is exposed so clients can verify and interoperate; the *official document*
is the ZLITS-rendered PDF.

> Contract status: `POST /v1/certificates`, `GET /v1/certificates/{id}` (incl. `pdf_url`)
> are a planned **v1.1** addition to `openapi.yaml`; `GET /v1/verify/{token}` already exists.

---

## 5. Who administers the portal

The **authority and its delegated operator — never a vendor.**

| Role | Who | Scope |
| --- | --- | --- |
| **Competent authority** | DVS (+ Provincial Veterinary Officers) | declare zones, approve establishments, oversight |
| **Operator (processor)** | LIT-style trust / PPP concessionaire | run the platform, accredit integrators, issue/rotate keys, support |
| **Official Veterinarians / field officers** | DVS field staff | endorse movement permits, sign certificates, record campaigns |
| **Data-protection roles** | **State = controller, operator = processor** (Cyber & Data Protection Act [Chapter 12:07], POTRAZ) | least-privilege RBAC; every action audited |

The company that builds ZLITS operates it **as the processor under the conferred mandate**,
not as owner. The herd data and the mandate belong to the State.

---

## 6. Who audits, and what

National registries must be independently auditable. Three tiers:

| Tier | Auditor | What |
| --- | --- | --- |
| **Internal** | operator | immutable append-only log of every write & admin action: key issuance, zone declarations, certificate issue/revoke, movement approvals/blocks |
| **Regulator / State** | DVS, Auditor-General, **POTRAZ** | conformance of declarations to gazette; data-protection compliance; who-accessed-whose-data |
| **Independent / trade** | third-party or importing competent authority | end-to-end traceability-chain audit for export-market recognition |

The design is **auditable without trusting the operator**: signed certificates + the public
verify endpoint + an immutable audit trail let any auditor verify a chain independently.
Surface **read-only auditor accounts** and **signed, timestamped audit exports**.

---

## 7. UI surfaces

| Surface | Audience | Login | Owner |
| --- | --- | --- | --- |
| **Registry Admin Portal** (§3) | DVS / operator staff | yes, RBAC | **ZLITS** (new) |
| **Public verification page** | anyone | none | **ZLITS** (new) — trust anchor |
| **Thin first-party field/web baseline** ("My ZLITS", §9) | DVS officers & smallholders without a vendor app | yes (keeper / staff) | **ZLITS** (new, minimal) |
| **Field capture (rich)** | farmers, agents | yes | **FuroTrack & other accredited clients** (exists) |

The keeper-facing baseline ("My ZLITS") is a **first-party client of the registry API** — the
same plane FuroTrack occupies, not a screen inside the Admin Portal — deployed on its own
keeper subdomain (`my.zlits.gov.zw`) under the **ZLITS** (sovereign) brand, never Dzinza (the
operator) and never the marketing apex. It carries a **low-trust keeper identity** distinct from
staff RBAC and reads/writes the **same registry rows** every integrator does (no private store).
The identity, deduplication and portability rules that make this safe are in §9.

### Field capture — first-party baseline + accredited ecosystem (best practice)

NAIT lets farmers use the **NAIT online portal directly, a third-party app, or an accredited
"information provider"**; NLIS pairs a central database with a funded **third-party
integrator** programme. The consistent pattern is a **government baseline plus a vendor
ecosystem** — never API-only, never vendor-only.

**Decision:** ZLITS ships a **deliberately thin first-party baseline** (mobile-friendly web +
optional light field app) so DVS officers and smallholders are never forced to buy a vendor
app — limited to registration, movement-permit lodging, vaccination-campaign capture and
QR verification. The **rich experience comes from accredited integrators** (FuroTrack and
competitors) via API keys. Build the baseline minimal on purpose; do not out-compete the
ecosystem.

### Accreditation

Mirroring NLIS integrators / NAIT information providers: vendors are **accredited**, then
issued a per-operator API key (§3). Accreditation + the audit trail + per-key attribution
are how the registry stays open yet accountable.

---

## 8. Build order

1. **Registry core + Admin Portal** (zones, keys/accreditation, lookup, audit) — the control plane.
2. **Public verification page** — the trust anchor (smallest surface, highest leverage).
3. **Certificates** (v1.1 contract): central rendering, e-signature, QR/reference.
4. **Identity spine** (§9): keeper SSOT + natural key, find-or-claim, one animal-ID with
   cross-references, tag lifecycle/retag, authorization grants, and the admin merge. This
   precedes both the keeper baseline and live integrator onboarding so duplicates are
   impossible from day one rather than reconciled later.
5. **Thin first-party field baseline / "My ZLITS"** — only the minimum DVS and keepers need
   without a vendor app (§7, §9).
6. Accredited-integrator onboarding (FuroTrack first, in dry-run, then live).

---

## 9. Identity, deduplication & tag lifecycle

The registry owns three identities — **keeper, animal, certificate**. Every consumer (the
"My ZLITS" keeper surface, FuroTrack, any other accredited vendor) holds a **reference** to a
registry row, never a private copy. That single rule is what guarantees one keeper per person,
one lifetime ID per animal, and clean vendor portability. It also follows directly from the
data-protection roles in [legal-basis-and-mandate.md §3](./legal-basis-and-mandate.md): the
keeper is the data subject, the State the controller — so the canonical record cannot live in a
vendor's database.

```
                 REGISTRY (single source of truth)
   keeper ──owns──< animal (national_id) ──< certificate   (registry-issued/signed)
      ▲                  ▲
      │ authorization    │ external_ref
      │ grant            │
  ┌───┴───────┬──────────┴────────────┐
  My ZLITS    FuroTrack            Next vendor
 (keeper app) (integrator)        (integrator)
   — each holds a reference (grant + cross-ref), never a copy —
```

### 9.1 Keeper — one row, many lenses (SSOT)

One `keeper` row per real person, keyed on a **sovereign natural key** — national ID number
and/or a verified MSISDN. Animals reference the keeper by **`keeper_id` (FK)**, retiring the
free-text `keeper_name` the reference impl carries today
([reference-impl/zlits/models.py](../reference-impl/zlits/models.py)). "My ZLITS" **binds a login
to a `keeper_id`** and keeps no keeper store of its own — it is one lens onto the same row the
Admin Portal and every integrator read.

### 9.2 No duplicate keepers across vendors — find-or-claim

A vendor must **resolve before it creates**. Add a find-or-claim step —
`POST /v1/keepers:resolve {national_id_no | msisdn}` → returns the existing `keeper_id`, or
creates **idempotently on that key**. If a keeper already exists (because they used My ZLITS, or
another vendor onboarded them), the vendor links to the same row instead of forking it. This is
**entity-level** identity resolution and is distinct from the request-level `Idempotency-Key`
([reference-impl/zlits/routers/api_v1.py](../reference-impl/zlits/routers/api_v1.py)), which only
makes a *single retried request* safe — it does not stop two *different* submissions from
duplicating the same real person. Today `register_keeper` mints a fresh id on every call
([reference-impl/zlits/domain.py](../reference-impl/zlits/domain.py)); that becomes find-or-claim.

### 9.3 Vendor portability — authorization grants, not ownership

The vendor relationship is a **consented authorization**, separate from ownership:
`keeper_authorizations(keeper_id, integrator_id, scope, granted_at, revoked_at)`. Ownership of
animals and certificates is the keeper↔registry link and never belongs to a vendor. **Switching
vendors = revoke one grant, add another**; the new vendor "syncs" by reading the keeper's herd by
`keeper_id` and attaching its own cross-references. Nothing is copied or re-minted. **Certificates
are portable by construction** — they are registry-issued/signed (§4) and hang off `national_id`,
so a vendor switch loses zero certificates. The keeper granting/revoking access is also how the
data subject exercises control under POTRAZ.

### 9.4 One authoritative animal ID

`national_id` is the **only** animal identity and is **permanent for life**. Two additions enforce
this against multi-source capture:

- **Find-or-create on the physical tag** (`eid` preferred, else `visual_tag`): if the tag already
  maps to a `national_id`, return it; only mint when the tag is genuinely new. Today
  `register_animal` mints a fresh id whenever the caller omits `national_id`
  ([reference-impl/zlits/domain.py](../reference-impl/zlits/domain.py)) — so two vendors tagging the
  same beast produce two IDs. This closes that.
- **Per-integrator cross-references** — `external_references[integrator_id] = vendor_animal_id`.
  Vendors keep their own internal IDs as **aliases that point at `national_id`**, never as a
  competing identity.

### 9.5 Tag lifecycle & retagging — the ID never changes, the device does

A tag (`eid`/`visual_tag`) is a **replaceable device that points at the `national_id`**; replacing
it is a routine event (loss, damage, retag, EID upgrade), **not** a re-registration. An animal
therefore holds a **set of tag bindings**, each with status `active | retired | lost | replaced`,
supporting concurrent visual + EID tags and full history.

- **Retag is an event, not a new animal.** The Admin Portal can *already* overwrite `eid`/`visual_tag`
  through the animal-correction path (`PATCH /admin/animals/{id}` → `update_animal`) — but as a flat
  overwrite, with no history, no retire and no duplicate guard. The addition turns that into a
  **binding event**: record the new binding `active`, mark the prior one `retired`, leave
  `national_id` untouched — so movements, vaccinations and certificates, all keyed on `national_id`,
  carry over automatically. It is not a new mutation primitive, it is history + status + a guard on
  the mutation that already exists.
- **Duplicate prevention:** (1) a retag is a *binding* operation, never `register_animal`; (2) the
  find-or-create guard (§9.4) checks a new tag against a **tag→`national_id` index** (active **or**
  retired) before minting; (3) retired tags are **kept, not deleted** and stay in that index, so a
  **lookup-by-tag** still resolves to the live animal, flagged "tag replaced" — this is registry
  *lookup* and is distinct from the certificate-token `GET /v1/verify/{token}`, which is unaffected;
  (4) a fresh registration whose attributes match an animal with a recently lost tag is surfaced as a
  **merge candidate** (§9.6).
- **Authority-endorsed in the mandatory regime:** retagging is a primary stock-theft laundering
  vector, so a keeper **requests** a replacement via My ZLITS but an Official Vet / dip officer
  **confirms** the new binding — the same Part I/Part II split as certificates (§4). Every retag is
  audited (old→new tag, reason, actor, location). A same-code replacement (the EU model, which
  retains the animal's identification code across an eartag swap) requires no registry change at
  all.

**So: a farmer never revokes the animal's identity.** They record a tag replacement — new tag yes,
new `national_id` no.

### 9.6 Safety net — merge (the only thing that retires an ID)

Find-or-claim cannot catch everything (typos, unverified self-signups), so the Admin Portal needs
an audited, staff-only **merge**: fold keeper/animal B into A, re-pointing animals, grants,
cross-references and tag history. Pair it with **verification tiers** on keeper identity
(`claimed` from low-trust My ZLITS self-signup vs `verified` against a national ID), so an
unverified account is reconciled into the authoritative row rather than standing as a fork.
`national_id` is **never reissued**; a merge is the only operation that retires one — the losing
row redirects to the survivor.

### 9.7 Contract & schema delta — what to *extend* vs *add*

Everything here is **additive**: it stays in `/v1` and keeps the load-bearing client conventions
([integration-guide.md §2](./integration-guide.md)), so no existing field is removed. In particular
`keeper_name` (today's documented `owner_name → keeper_name` adapter mapping) is **kept, deprecated in
place**, with `keeper_id` added alongside. Each row names what already exists so it is *reused, not
re-declared* — client-side additions land in [../openapi.yaml](../openapi.yaml), admin/merge ones in
[../openapi-admin.yaml](../openapi-admin.yaml) (both at `1.2.0-draft`; this is the next draft minor,
ratified with DVS per [CONTRIBUTING.md](../CONTRIBUTING.md)).

| Capability | Already there (reuse) | Additive change |
| --- | --- | --- |
| **Keeper SSOT** | `Keeper` / `KeeperCreate`, `POST /admin/keepers`, `Holding.keeper_id`; `register_keeper` | natural-key fields (`national_id_no`, `msisdn`) + `verification` on `Keeper`; `keeper_id` (alongside deprecated `keeper_name`) on `AnimalRegistration` / `AnimalRecord` / `AnimalUpdate` |
| **Find-or-claim** | — (no keeper endpoint on the client contract; `register_keeper` always mints) | `POST /v1/keepers/resolve` → existing `keeper_id`, else idempotent create on the natural key |
| **One animal ID** | `registerAnimal` already returns `already_exists` (idempotent on `national_id` / `Idempotency-Key`); `eid`/`visual_tag` already on the animal; the guide already implies `national_id` *or* `eid_tag` addressing | extend dedupe to a **tag→`national_id` index** (`eid` then `visual_tag`); a tag-keyed **lookup**; `external_references` map on the animal |
| **Tag lifecycle** | `eid`/`visual_tag`; `PATCH /admin/animals/{id}` (`update_animal`) already mutates them | a `tags[]` binding array (`status` / `since` / `endorsed_by`) on `AnimalRecord`; a retag **event** (keeper/client *requests*, admin correction path *confirms*) — history + guard, not a new primitive |
| **Portability** | per-operator keys + accreditation (`Integrator` / `ApiKey`) — but that is *vendor* identity, not *keeper consent* | `keeper_authorizations(keeper_id, integrator_id, scope, granted_at, revoked_at)` + grant/revoke; a vendor-readable "authorized herd" filter. **Open decision:** grants are keeper-consent actions and the client contract is `operatorApiKey`-only, so they live on the **My ZLITS keeper surface** (keeper session) + the Admin Portal — *not* the integrator client API |
| **Merge** | — | control-plane `POST /admin/keepers/{id}/merge`, `POST /admin/animals/{id}/merge` (audited; re-points animals, grants, cross-refs, tag history) |

> Downstream doc to update in lock-step: the [integration-guide.md §1](./integration-guide.md) field
> map (`owner_name → keeper_name`) gains an optional `→ keeper_id` via `POST /v1/keepers/resolve`.

### 9.8 Reference-impl data-model delta

The reference impl is still the in-memory `Store`
([reference-impl/zlits/store.py](../reference-impl/zlits/store.py)) — Postgres is Phase 0 of
[saas-platform-architecture.md](./saas-platform-architecture.md) and not yet built — so this is a
**`Store` / `domain` delta, not a SQL migration**, and it stays within the existing shape (the store
already anticipates a SQLite/Postgres swap):

- **`Store` (new):** `tag_index: dict[str, str]` (tag → `national_id`), `keeper_by_key: dict[str, str]`
  (natural key → `keeper_id`), `authorizations: list[dict]`. `animals` rows gain `tags`, `keeper_id`,
  `external_references`; `keepers` rows gain the natural-key fields + `verification`.
- **`domain` (changes/new):** `register_animal` consults `tag_index` before `next_national_id()`
  (extending the existing `already_exists` path); new `resolve_keeper`, `record_retag`,
  `grant_authorization` / `revoke_authorization`, `merge_keepers` / `merge_animals`; `register_keeper`
  populates `keeper_by_key`. All write through the existing `store.log(...)` audit trail.
- **Indexes are derived, not authoritative** — rebuildable from `animals` / `keepers`, so the future
  Postgres port replaces them with unique constraints (tag, keeper natural key) + FKs rather than
  carrying them as data.

---

## References

- EU TRACES NT — [certificates, documents & features](https://food.ec.europa.eu/animals/traces/certificates-documents-and-features_en) ·
  [OECD, electronic sanitary certificates (2023)](https://www.oecd.org/content/dam/oecd/en/publications/reports/2023/02/electronic-sanitary-certificates-for-trade-in-animal-products_a889f609/5417ff4f-en.pdf)
- Australia NLIS — [third-party integrators](https://www.integritysystems.com.au/identification--traceability/NLIS-Database-Uplift-Project/third-party-integrators/)
- New Zealand NAIT — [programme overview](https://www.mpi.govt.nz/animals/national-animal-identification-tracing-nait-programme)
- ZLITS API contract — [../openapi.yaml](../openapi.yaml) · principle & legal basis — [../README.md](../README.md)

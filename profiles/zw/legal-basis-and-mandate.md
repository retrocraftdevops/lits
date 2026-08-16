# ZLITS Legal Basis & Nationalization Pathway

How ZLITS acquires the **authority** to be the national source of truth, who holds which
legal role over the data, and the concrete path from *draft contract* to a *mandatory*
national system. Authority for a national registry is **conferred by the State, never
self-declared** — this document is the map of how that conferral happens.

> Status: DRAFT design. Pairs with registry-operations.md (who
> operates it) and [spec-governance.md](../../docs/spec-governance.md) (how the *standard*
> is governed). The commercial terms and the full nationalization strategy live in the
> partnering strategy brief held privately with the anchor client. Statutory references are
> to-be-confirmed with the Department of Veterinary Services (DVS) before `1.0.0`.

---

## 0. The principle in one line

**A registry is "national" only when the State says so.** Software, an API contract and a
running service do not by themselves make a system the official record. The authority to
**compel** identification, movement permits and disease reporting comes from law — and the
designation of *which* system carries that authority comes from a subsidiary legal
instrument (a Statutory Instrument) under the Animal Health Act. Everything ZLITS does
before that instrument is **voluntary**; everything after it is **mandatory**.

---

## 1. The legal instruments (and what each one confers)

| Instrument | Regulator | What it confers on ZLITS |
| --- | --- | --- |
| **Animal Health Act [Chapter 19:01]** | DVS | The substantive power: to **compel** animal identification, require **movement permits**, declare **veterinary / FMD zones**, and mandate **disease control / reporting**. This is the Act under which the designating Statutory Instrument is made (§2). |
| **Cyber & Data Protection Act [Chapter 12:07]** | POTRAZ | Governs the **personal data** ZLITS holds (keeper names, holdings, contacts). Fixes the **controller / processor** split (§3) and the lawful basis for processing. |
| **Public Procurement & Disposal of Public Assets Act [Chapter 22:23]** | PRAZ | One route by which an **operator** is lawfully engaged — open tender for a public ICT system. |
| **Zimbabwe Investment & Development Agency Act [Chapter 14:37]** | ZIDA | The alternative route — a **PPP / concession** (build-operate) for the operator. (§4) |

The README carries the short version of this table; this document is the working detail
behind it. None of these instruments names ZLITS today — that is the gap the designation
step closes.

---

## 2. The designation mechanism — a Statutory Instrument

The Animal Health Act is **enabling** legislation: it empowers the Minister / DVS to make
**Statutory Instruments (SIs)** that put specific obligations into force. The act that turns
ZLITS from "a system that exists" into "the system you must use" is an SI made under
[Chapter 19:01] that:

1. **Designates the official system** — names ZLITS (final acronym set at ratification, see
   [../CONTRIBUTING.md](../../CONTRIBUTING.md)) as the national livestock identification &
   traceability register.
2. **Designates the operator** — names the delegated operator and the legal basis of the
   delegation (the concession or tender award, §4).
3. **Defines mandatory scope** — which events must be lodged (registration, movement
   permits, mandatory disease events) and for which species (**cattle first**, aligned with
   the National Cattle Identification Program; extensible to small stock).
4. **Sets the data roles** — affirms the State as controller and the operator as processor
   (§3), consistent with [Chapter 12:07].
5. **Sets fees & offences** (if any) — registration / permit fees and the consequence of
   moving stock without a registry permit.

> Until this SI is gazetted, ZLITS operates as a **voluntary** registry: keepers and vendors
> may use it, certificates verify, but nothing compels participation. The SI is the single
> legal switch that flips the system mandatory — which is why the build-out (§5) front-loads
> everything that does *not* need the SI, so the system is fully proven the day it lands.

---

## 3. Data-protection roles (controller vs processor)

ZLITS holds personal data — keeper names, holdings, districts, contacts. Under
[Chapter 12:07] (POTRAZ) the roles are fixed and **non-negotiable**:

| Role | Party | Meaning |
| --- | --- | --- |
| **Controller** | **The State** (DVS) | Determines the purposes and means of processing; owns the mandate and the national herd data. |
| **Processor** | **The delegated operator** | Processes data **on the controller's instructions only**; runs the platform, but does not own the data. |
| **Data subjects** | **Keepers / owners** | Hold rights (access, correction) over their personal data; animals themselves are not personal data, but the keeper link is. |

Consequences that shape the build:

- **Least-privilege RBAC and a full audit trail** are legal requirements, not features — see
  registry-operations.md §5–6 and [GOVERNANCE.md §6](../../GOVERNANCE.md).
- **Operator change / exit must not lose data** — because the operator is only a processor,
  the data and its continuity belong to the State (escrow / handover in the operating
  agreement).
- **Cross-border export certificates** move data to importing competent authorities; that
  transfer is bounded to the **sanitised, certificate-scoped** fields the public
  `GET /v1/verify/{token}` already exposes — never the full keeper record.

This is also why no client (FuroTrack included) is a controller or processor of the national
record: clients **submit and read** under their own keys; the registry is the system of
record. See the two-plane model in registry-operations.md §0.

---

## 4. How the operator is lawfully engaged — two routes

| Route | Basis | Fits when |
| --- | --- | --- |
| **Open tender** | Public Procurement Act [Chapter 22:23] (PRAZ) | The State funds and owns the build and buys an operator's services. Most transparent; slowest; State carries delivery risk. |
| **PPP / concession** | ZIDA Act [Chapter 14:37] | An operator **builds and operates** at its own investment and earns a regulated return (fees / service charge) under a time-bound concession. Fits a build-operate-transfer model where the operator already has the implementation. |

The concession route is the natural fit for ZLITS because the implementation already exists
as a **held** asset (see [spec-governance.md §1](../../docs/spec-governance.md)): the State
confers the mandate and oversight; the operator brings the working system and run it as
processor. The **standard stays open** (so there is no lock-in and competitors integrate on
equal terms) while the **operating concession** is what the operator actually holds. Opening
the spec costs the operator nothing it needs to keep — the moat is *operation*, not
*possession of the contract*.

---

## 5. The nationalization pathway (contract → mandatory)

This deepens the README roadmap into the legal/sequencing view. The ordering principle:
**do everything that does not need the SI first**, so designation is a switch, not a project.

| Phase | What happens | Needs the SI? |
| --- | --- | --- |
| **1. Contract** (this repo) | `openapi.yaml` ratified with DVS; official acronym + `national_id` numbering scheme agreed. | No |
| **2. Reference implementation** | A running service on an operator/State domain, POTRAZ-aligned governance, the Admin Portal. | No |
| **3. Sandbox** | Issue operator API keys; FuroTrack and other clients integrate in **dry-run**, then live. | No |
| **4. District pilot** | Voluntary pilot on the funded drivers — **dipping, movement permits, stock-theft, disease control** — in one or more districts to prove value and gather DVS evidence. | No (voluntary) |
| **5. Mandatory** | The Statutory Instrument (§2) is gazetted; participation becomes compulsory, nationwide. | **Yes** |

The pilot (phase 4) is the evidence base the SI is argued from: a working system with real
movement permits and disease records is far easier to designate than a proposal. By the time
the SI lands, the contract, the registry, the portal and the integrator ecosystem already
work — designation only changes *who must* use them.

---

## 6. Who owns what (the sovereignty line)

| Asset | Belongs to | Why |
| --- | --- | --- |
| **The national herd data** | **The State** | Sovereign record; operator is only a processor ([Chapter 12:07]). |
| **The mandate** | **The State** | Conferred by the SI; can be withdrawn or re-tendered by the State. |
| **The API contract & conformance suite** | **Open** (anyone) | Apache-2.0; the standard is public so the system cannot be locked in. |
| **The reference implementation / hardened platform** | **The operator** | Source-available but held; the operator's IP and regional rights. |
| **The "ZLITS" name & conformance mark** | **State / operator** | Trademark — open spec, controlled name (impersonation protection). |

The credibility move is to commit, **in writing and now**, that spec stewardship transfers to
the State / a neutral board on designation — see [GOVERNANCE.md §2](../../GOVERNANCE.md) and
[spec-governance.md §5](../../docs/spec-governance.md). That single commitment is what turns
"a vendor's API" into "the national standard" in a government reviewer's eyes, and it is free
to give because stewardship of the *standard* is separate from operation of the *instance*.

---

## 7. Open items (to confirm before `1.0.0`)

- [ ] Exact citation of the designating SI and its parent provisions in [Chapter 19:01].
- [ ] The `national_id` numbering scheme and the official acronym (set with DVS — see
      [../CONTRIBUTING.md](../../CONTRIBUTING.md)).
- [ ] Engagement route chosen (tender vs concession, §4) and the operating agreement's
      data-continuity / escrow terms.
- [ ] POTRAZ registration of the controller/processor relationship.
- [ ] Alignment of mandatory scope with the National Cattle Identification Program timeline.
- [ ] **Which disease-response milestones this territory's law requires, and how each is
      derived.** Owed by this profile since the contract gained `QuarantineOrder.milestones` at
      `2.2.0`. The contract deliberately carries **no jurisdiction's arithmetic** (RFC 0003 §3):
      it publishes a date and what the date means (`day_zero`, `slaughter_window_opens`,
      `slaughter_window_closes`, `review_due`, `lift_eligible`), and the registry computes those
      dates under *this* profile. Until this item is answered, a ZW registry has no stated basis
      for the numbers it emits. **A milestone this profile needs but the vocabulary lacks is the
      trigger to extend the vocabulary once, for everyone** — never to add a ZW-only field.
- [ ] **Whether a verbally-declared order is enforceable before written confirmation**, and how
      long the confirmation may lag. The contract carries `declared_verbally_at` and
      `confirmed_in_writing_at` and decides nothing (RFC 0003 §7); this profile decides, and its
      registry refuses to activate on a verbal declaration alone if the answer is no. Raised
      against **Gazette 54972**, which is **UNVERIFIED** — it must be read and confirmed, or
      replaced, before anything relies on it.

---

## References

- ZLITS principle & instruments — [../README.md](../../README.md)
- Operations, RBAC & audit — registry-operations.md
- Standard governance, licensing & stewardship handover — [spec-governance.md](../../docs/spec-governance.md), [../GOVERNANCE.md](../../GOVERNANCE.md)
- Change & ratification policy — [../CONTRIBUTING.md](../../CONTRIBUTING.md)
- Comparable national frameworks — Australia **NLIS**, New Zealand **NAIT**, EU **TRACES NT** (see registry-operations.md → References)

# MozLITS Legal Basis & Nationalization Pathway

How MozLITS acquires the **authority** to be Mozambique's national livestock source of truth, who
holds which legal role over the data, and the path from *voluntary pilot* to a *mandatory* national
system. As with every LITS instance, authority is **conferred by the State, never self-declared**.

> Status: DRAFT design, mirroring [../zw/legal-basis-and-mandate.md](../zw/legal-basis-and-mandate.md).
> **Every statutory reference and institution name below is TO-VERIFY** with the Mozambican
> counterpart (MAAP / DINAV) before `1.0.0`. Mozambique's ministries were consolidated in 2025, so
> the ministry name in particular must be confirmed against current gazette.

---

## 0. The principle in one line

**A registry is "national" only when the State says so.** A running service and an API contract do
not make a system the official record. The authority to **compel** identification, movement permits
and disease reporting comes from Mozambican animal-health law and the subsidiary instrument (a
*diploma ministerial* / regulamento) that designates *which* system carries it. Before that
instrument, MozLITS is **voluntary**; after it, **mandatory**.

---

## 1. Institutional actors (TO-VERIFY)

| Actor | Role | Notes |
| --- | --- | --- |
| **MAAP** — Ministério da Agricultura, Ambiente e Pescas | Parent ministry | Post-2025 consolidation of the former agriculture/land portfolios. **Confirm current name.** |
| **DINAV** — Direcção Nacional de Veterinária | National veterinary authority | The competent authority for animal health, movement control, and export certification. The MozLITS "authority" in the tenant registry. |
| **National Directorate of Livestock** (Pecuária) | Livestock development | Herd census, restocking, breeding — a data producer/consumer alongside DINAV. |
| **SDAE** — Serviço Distrital de Actividades Económicas | District administration | Under the District Administrator; per **Regulation 146/2009** runs livestock censuses, restocking, veterinary infrastructure and animal-health programmes at district level. The MozLITS `district_officer` maps to the SDAE técnico. |
| **Autoridades comunitárias** — régulos + secretários | Community authorities | Recognised by **Decree 15/2000**: régulos (traditional chiefs) and secretários de bairro/aldeia (neighbourhood/village secretaries). The MozLITS community-attestor layer (chief / village_head). |
| **INCM** | Communications regulator | Allocates the USSD short code (TO-VERIFY the dial code). |
| Data-protection authority | Personal-data oversight | Confirm the applicable Mozambican data-protection regime and the controller/processor split. |

## 2. Designation mechanism

The designating instrument (a *diploma ministerial* or regulamento under the animal-health law —
**exact citation TO-VERIFY**) would: (1) designate MozLITS as the official national livestock
identification & traceability register; (2) designate the operator and the legal basis of the
delegation; (3) define mandatory scope (registration, movement permits, notifiable disease events)
and species (**cattle first**); (4) fix the data-protection roles (State as controller, operator as
processor); (5) set fees and offences, if any.

## 3. Community governance layer (the MozLITS distinctive)

Mozambique's communal reality maps cleanly onto the platform's grassroots-governance model:

| MozLITS concept | Mozambican actor | Legal basis |
| --- | --- | --- |
| `district_officer` (RBAC role, district-scoped) | Técnico do SDAE | Reg. 146/2009 |
| `health_inspector` (RBAC role) | Inspector sanitário / meat inspector | animal-health law |
| Community attestor `chief` | Régulo | Decree 15/2000 |
| Community attestor `village_head` | Secretário de bairro/aldeia | Decree 15/2000 |
| Community attestor `dip_attendant` | Encarregado do banho carrapaticida | operational |

Régulos and secretários **attest** provenance and ownership at village level (a claim with local
standing, the `community_attestor` trust tier) — they never *confirm*; DINAV/SDAE confirm. This is
the same trust discipline the whole platform enforces: community actors attest, the State confirms.
The optional community approval chain on a movement permit (village attestation → SDAE/health check →
DINAV review) is configured per tenant and is the on-the-ground governance point the pilot showcases.

## 4. Data-protection roles

Controller = the State (DINAV/MAAP); processor = the delegated operator; data subjects = keepers.
Least-privilege RBAC and a full audit trail are legal requirements, not features. Cross-border export
certificates move only the sanitised, certificate-scoped fields the public verify endpoint exposes —
never the full keeper record. **Confirm the applicable Mozambican data-protection statute.**

## 5. Nationalization pathway (voluntary → mandatory)

| Phase | What happens | Needs the instrument? |
| --- | --- | --- |
| **1. Contract** | MZ profile ratified with DINAV; `national_id` scheme + acronym agreed. | No |
| **2. Reference implementation** | MozLITS running on `registry.gov.mz`; Portuguese keeper surfaces; DINAV admin console. | No |
| **3. Sandbox** | Operator API keys; integrators (incl. FuroTrack) integrate dry-run → live. | No |
| **4. District pilot** | Voluntary pilot on the funded drivers — **dipping, movement permits, FMD corridor control, informal-slaughter capture** — in a border district (Manica/Gaza). | No (voluntary) |
| **5. Mandatory** | The designating instrument is issued; participation becomes compulsory. | **Yes** |

The pilot (phase 4) is the evidence base the designation is argued from — a working system with real
movement permits and dip records is far easier to designate than a proposal.

## 6. Open items (confirm before `1.0.0`)

- [ ] Current ministry name (MAAP vs prior MASA/MADER) and the exact animal-health law + designating instrument citation.
- [ ] DINAV as the named competent authority; the SDAE's statutory livestock mandate under Reg. 146/2009.
- [ ] Decree 15/2000 as the basis for régulo/secretário attestation in a permit chain.
- [ ] The applicable data-protection statute and the controller/processor registration.
- [ ] INCM USSD short code + DINAV hotline (shipped values are placeholders).
- [ ] Export destinations and the SADC/OIE zoning MozLITS must certify against.
- [ ] **Which disease-response milestones Mozambican law requires, and how each is derived.**
      Owed by this profile since the contract gained `QuarantineOrder.milestones` at `2.2.0`. The
      contract carries **no jurisdiction's arithmetic** (RFC 0003 §3) — it publishes a date and
      what the date means, and the registry computes it under *this* profile. The periods are not
      assumed to match Zimbabwe's; that they may differ is the reason the contract refuses to
      carry either.
- [ ] **Whether a verbally-declared order is enforceable before written confirmation**, and how
      long the confirmation may lag (RFC 0003 §7). Answered per territory, and the answer here is
      independent of the ZW one — this profile's régulo/secretário attestation chain (§3) may
      bear on how a verbal order is witnessed.

---

## References

- ZW equivalent (structure mirrored) — [../zw/legal-basis-and-mandate.md](../zw/legal-basis-and-mandate.md)
- Standard governance & stewardship — [../../docs/spec-governance.md](../../docs/spec-governance.md)
- SDAE mandate — Regulation 146/2009 (Serviço Distrital de Actividades Económicas)
- Community authorities — Decree 15/2000 (autoridades comunitárias)
- Comparable national frameworks — Australia **NLIS**, New Zealand **NAIT**, EU **TRACES NT**

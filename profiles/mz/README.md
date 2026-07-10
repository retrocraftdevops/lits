# Profile: Mozambique (MozLITS)

The Mozambique national instance of the LITS standard — the platform's immediate pilot. This profile
defines the Mozambican expression of the open contract: the official brand (**MozLITS**), the
`national_id` scheme (`MZ-…`), the veterinary authority (**DINAV**), the administrative and community
governance structure, and the legal basis under Mozambican animal-health law.

Mozambique is a **new tenant on the same multi-country spine** already serving Zimbabwe (ZLITS) and
Malawi (MLITS) — not a new platform. Country differences live in configuration (tenant registry +
reference profile + role labels + language), never in code forks.

> Status: tenant + reference profile shipped; legal basis in DRAFT pending DINAV confirmation.
> Every institutional fact below is flagged **TO-VERIFY** until confirmed with the Mozambican
> counterpart.

## Contents

- [legal-basis-and-mandate.md](legal-basis-and-mandate.md) — how MozLITS acquires the authority to be
  the national source of truth (MAAP/DINAV mandate, SDAE district administration, Decree 15/2000
  community authorities, the nationalization pathway).
- [use-case-pack.md](use-case-pack.md) — the Mozambique-specific use cases that drive the pilot (FMD
  corridor control, southern restocking, communal dipping, informal slaughter, SDAE + régulo
  governance).

## Snapshot (all TO-VERIFY)

| Field | Value | Source |
| --- | --- | --- |
| Brand / system | **MozLITS** — Sistema de Identificação e Rastreabilidade Animal | operator |
| Ministry | **MAAP** — Ministério da Agricultura, Ambiente e Pescas | post-2025 consolidation |
| Veterinary authority | **DINAV** — Direcção Nacional de Veterinária | under MAAP |
| District administration | **SDAE** — Serviço Distrital de Actividades Económicas | Reg. 146/2009 |
| Community authorities | **régulos** (chiefs) + **secretários de bairro/aldeia** | Decree 15/2000 |
| `national_id` prefix | `MZ-` (e.g. `MZ-CAT-0000001`) | minted from country code |
| Keeper language | Portuguese (`pt`) | tenant `lang` |
| Provinces | 10 + Maputo City | — |
| Priority species | Cattle first (Landim, Bovino de Tete, Angone…) | extensible to small stock |
| Custom domain | `registry.gov.mz` | State-delegated |

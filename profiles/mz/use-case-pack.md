# MozLITS Use-Case Pack

The Mozambique-specific use cases that drive the pilot. Each is expressed in terms of platform
capabilities that already exist (the grassroots-governance foundation), so the pilot is a
configuration + data-loading exercise, not a build.

> Every factual claim (outbreak locations, breeds, export destinations) is **TO-VERIFY** with DINAV.

---

## 1. FMD corridor control (Manica / Gaza / Tete)

**Context.** Foot-and-mouth disease is active across southern and central Mozambique — reported in
Maputo (Moamba), Gaza, Manica, Tete (Angónia) and Niassa — with a live corridor risk along the
Zimbabwe border in Manica and Gaza. Uncontrolled cattle movement across the corridor is the primary
transmission vector.

**MozLITS use.** Declare FMD zones (`zone_type` corridor/infected/surveillance) over the affected
districts; the movement-permit state machine gates any permit whose origin/destination crosses a
standstill zone (the existing chokepoint gates). A permit from a Gaza village toward the Manica
corridor runs the community approval chain — village attestation → SDAE/health check → DINAV review —
before it can be approved. FuroTrack and other integrators poll `GET /v1/zones` to surface the
standstill to keepers in the field.

## 2. Southern restocking herds (Gaza / Maputo — Landim)

**Context.** Post-conflict and post-cyclone restocking has repopulated the southern provinces with
communal cattle, predominantly the indigenous **Landim** (Sanga type). These herds enter the system
as *incumbent baseline* stock, not born-in-system.

**MozLITS use.** The onboarding wizard's `incumbent_baseline` basis registers existing stock with a
crush-pen confirmation; a régulo/secretário attestation of ownership (the `village_head` attestor at
`community_attestor` tier) accompanies the claim, giving provenance where paper records are absent.
The animal mints an `MZ-CAT-…` national id that never changes.

## 3. Communal dipping (tick-borne disease control)

**Context.** Dipping against ticks/tick-borne disease is the front line of communal herd health.
Dip tanks serve a catchment of villages; attendance is the compliance signal.

**MozLITS use.** Register dip tanks as managed places with a catchment (the geography tree); open a
dip session on dipping day; capture attendance by SDAE officer scan or by keeper self-report over
USSD in Portuguese (the `community` trust tier). Animals in a tank's catchment with no recent dip
surface as compliance gaps that feed the graduated enforcement ladder — no new enforcement machinery.

## 4. Informal / home slaughter + meat inspection

**Context.** Most communal slaughter happens at small butcheries or at home, outside any accredited
abattoir — today invisible to traceability, and the point where stolen or diseased stock leaves the
trace.

**MozLITS use.** Register butcheries as light actors; capture a slaughter slip (butchery or
informal/home) declared by an SDAE officer, an agent, or the keeper over USSD, carrying a provenance
grade set by the channel. The slip sets the animal terminal and opens a meat-inspection task an
`health_inspector` (inspector sanitário) closes with passed/conditional/condemned — bringing the
informal end of the value chain into the trace for the first time.

## 5. SDAE district governance + régulo attestation

**Context.** Livestock administration in Mozambique is a district function (SDAE), with community
authority vested in régulos and secretários (Decree 15/2000).

**MozLITS use.** The `district_officer` role (labelled "Técnico do SDAE") is scoped to its district —
it sees and reviews only its district's holdings, permits and dip/slaughter records. Régulos and
secretários are registered community attestors whose attestations satisfy the community steps of a
permit chain. The whole governance layer reads in Portuguese via the per-tenant role labels and i18n
catalog.

## 6. Exports & regional trade (TO-VERIFY)

**Context.** Mozambique's beef trade and any export ambition depend on OIE/SADC-recognised zoning and
certificate integrity. **Destinations and the applicable zoning regime are TO-VERIFY with DINAV.**

**MozLITS use.** The export certificate path (two-step maker-checker: issuing vet recommends →
competent authority endorses) and the sanitised public verify endpoint are already in place; the MZ
profile supplies the zones and destinations once confirmed.

## 7. Accredited abattoir as an integrator node

**Context.** Use case 4 brings the *informal* end of slaughter into the trace. The formal end is the
mirror image and is currently just as invisible: a licensed, capacity-scaled plant receives animals
from many holdings, and unless it reports, the registry loses the chain at precisely the point where
the animal ceases to exist. A plant is also the densest reporting node available — one integration
covers the terminal event for every animal that passes through it, rather than one keeper at a time.

**MozLITS use.** An accredited abattoir registers as a holding of type `abattoir` and is issued its own
integrator API key, so the registry attributes every submission to it. The plant's own system (an
accredited farm-management platform or plant LIMS) then:

- reconciles **arrivals** against lodged movement permits, so an animal arriving without a valid
  permit — or across a standstill zone declared under use case 1 — is an exception the registry sees
  rather than a gap it never learns about;
- reports the **slaughter event**, setting the animal terminal at the `accredited` provenance grade
  (contrast the `declared` grade a keeper self-report carries in use case 4);
- records the **meat-inspection outcome** (passed / conditional / condemned) against the same
  inspection task an `health_inspector` closes for informal kills, so both channels land in one queue.

Nothing here is a new registry capability: it is the existing movement, slaughter-slip and
meat-inspection surface, exercised by a high-volume integrator instead of a district officer. The
distinction that matters is the **provenance grade**, which lets DINAV report formal and informal
slaughter separately without maintaining two records.

**Why it strengthens the pilot.** The corridor-control argument (use case 1) is about animals moving;
the designation argument needs animals *arriving somewhere accountable*. A plant in a pilot district
closes that loop, and gives the operator a second class of counterparty — commercial, contract-capable
and motivated by provenance for its own brand and export reasons — alongside district administration.

> **TO-VERIFY with DINAV:** the accreditation regime for abattoirs, which authority licenses them,
> whether ante-mortem and post-mortem records are already statutorily required, and whether plant
> reporting can be made a condition of licence independently of the wider designating instrument.

---

## Pilot scoping note

The natural first pilot is a **border district in Manica or Gaza** where the FMD corridor, communal
dipping, restocking and informal slaughter all coincide — a single district exercising every use case
above, producing the evidence base for national designation.

Where such a district also contains an **accredited abattoir** (use case 7), prefer it: the plant
supplies a commercial integrator, a dense terminal-event feed, and a counterparty whose own provenance
and export interests align with the registry's — without which the pilot rests entirely on public
administration capacity.

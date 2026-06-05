# Changelog

All notable changes to the ZLITS API contract are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The **contract** is versioned
in the URL path (`/v1`); see [CONTRIBUTING.md](./CONTRIBUTING.md) for the change policy.

## [Unreleased]

### Added

- **Platform modules: Observability · Compliance · Feature flags.** Rounding out the back
  office, no dead ends. **Observability** (`/platform/observability`): cross-tenant rollup
  (tenants/users/animals/API-calls/open-requests) + per-tenant health (error rate, load) +
  simulated uptime/p95. **Compliance** (`/platform/compliance`): data-residency view, **legal
  hold** (blocks suspension while held), and a **signed per-tenant data export** (portability /
  DSAR, secrets redacted). **Feature flags** (`/platform/features`): per-tenant toggles that
  override the plan default and feed `billing.has_feature` (the app enforces entitlements).
  Verified (56 tests): observability rollup, legal-hold 409, redacted signed export, feature
  override wins + tenant role 403.

- **Platform impersonation (login-as, audited).** A platform operator can **impersonate** a
  tenant from the Tenants screen (`POST /platform/tenants/{slug}/impersonate`,
  `platform:impersonate`): it issues a session for the tenant's admin and a `zlits_tenant`
  cookie the BFF proxy forwards as **X-Tenant**, so the whole console scopes to that tenant. A
  persistent **banner** marks the session; **Exit** re-auths as the operator. Logged to the
  platform audit. Verified: impersonate botswana → `/admin/me` = admin@botswana.gov in that
  tenant's context.

- **Notifications (the bell) + workflow surfacing.** A topbar bell with unread count + dropdown
  and a `/notifications` manage page (inbox / archived, mark-read, mark-all, archive). Events
  generate notifications: a tenant **support** request → the platform bell; a platform **reply**
  → the requester's bell; a **bulletin** → broadcasts to every tenant. Per-recipient read/archive.
  Bulletins now have a **lifecycle**: optional **expiry** (auto-drop from My Day) and platform
  **delete**; the platform Support & comms screen lists/removes active bulletins. **Requested
  certificates** now surface for the issuer — a high-priority work-queue task (`Issue & sign`)
  and a notification on request — answering 'how are certs surfaced'. Verified end-to-end.

- **Comms: support/feedback channel + bulletins.** A complete two-way channel for platform
  requests. A tenant user raises a threaded request (`POST /admin/support`, kind support/
  feedback/billing/request); the platform sees every tenant's requests in one inbox
  (`GET /platform/support`), **replies** (threaded), and **resolves**. The platform also
  **broadcasts bulletins** (`POST /platform/announcements`) that surface on every tenant's My
  Day. Console: tenant **Help & feedback** (`/support`, from the user menu) and a platform
  **Support & comms** screen (`/platform/support`). Verified end-to-end: raise → reply →
  resolve → tenant sees the thread; bulletin → appears on My Day.

- **User & invitation row actions.** The Users & access screen rows gained a `⋯` menu:
  **change role**, **reset MFA**, **remove user** (self-removal blocked, 409); invitations get
  **copy invite link** and **revoke**. Backed by `PATCH/DELETE /admin/users/{email}`,
  `POST …/reset-mfa`, `DELETE /admin/invitations/{token}` (all `users:write`).

- **Command palette / first-class search.** Press **⌘K** (or **/**, or just start typing while
  not in a field) to jump into search from anywhere. Results span **Pages** (the nav,
  permission-filtered) and **Records** (animals, permits, certificates, holdings, integrators);
  keyboard-navigable, records deep-link to the exact entity. Search is now the fast path to any
  page or record.

- **My Day — a personalised landing.** A common place to start: a greeting + date, the user's
  action items (the role/jurisdiction-scoped work queue), actionable stat tiles that drill to
  source, **quick actions** (only the ones the role can do), platform **bulletins**, a rotating
  operational **tip**, and recent activity. Backed by one aggregation endpoint `GET /admin/my-day`;
  all roles now land here (`ROLE_HOME`). Gives an officer a reason to log in — their work, first.

- **Phase 3 — billing, plans & usage metering.** Plan catalogue (trial/starter/pro/sovereign)
  bundling **entitlement limits** (animals/users/integrators) + **features** (modules), and a
  **usage meter** (tenant-tagged events → aggregation). Entitlements are enforced in the domain:
  the `users` seat limit blocks invitations (402) and the `animals` limit blocks client-API
  registration (402) on capped plans; the sovereign plan is unlimited. Privileged creates emit
  meter events (animals, certificates, movements, api.call). Platform billing endpoints:
  `GET /platform/plans`, `/platform/tenants/{slug}/usage` (limits · counts · usage · estimated
  charge), `/platform/billing` (cross-tenant MRR estimate, `platform:billing`-gated). Tenants
  carry a `billing_mode` (invoice/PO for government, card for commercial). In-memory now; the
  same surface fronts Stripe Billing / invoice in production. Verified (53 tests): seat + animal
  limits enforced, metering recorded, billing overview.
- **Console: Platform section** — `/platform/tenants` (provision + lifecycle kebab + a plan /
  limits / usage detail sheet) and `/platform/billing` (MRR estimate + per-tenant usage). Shown
  only to platform operators: `hasPerm` now treats `platform:*` as a hard boundary so a tenant
  `dvs_admin` (`*`) doesn't see the plane (mirrors backend `require_platform`); platform roles
  land on `/platform/tenants` and are added to the dev role switcher.
- **Phase 2 — identity (credential auth, MFA, invitations; OIDC-ready).** Production auth path
  alongside the (now config-gated) dev-login. `POST /auth/login` with **scrypt** password
  verification and **TOTP MFA** (RFC 6238, stdlib — enrol `/auth/mfa/enroll`, confirm
  `/auth/mfa/verify`); `/auth/me`, `/auth/logout`. **Invitations**: a tenant admin
  (`users:write`) issues `POST /admin/invitations`; the invitee accepts via
  `POST /auth/accept-invite` (sets their own password) and is created in the inviting tenant.
  Seeded users carry a hashed dev password so credential login is testable; dev-login gates on
  `ZLITS_DEV_AUTOLOGIN` (off ⇒ production credential-only). **OIDC/SSO** is the integration
  point: config (`ZLITS_OIDC_*`) + `/auth/oidc/login|config`, guarded to 501 until an issuer is
  set (per-tenant issuer config lives in the control plane; a live IdP completes it). Verified
  (49 tests + live HTTP): login/MFA/invite flows, auditor cannot invite (403), dev-login
  disable, OIDC guard.
- **Console: identity UI.** Public **`/login`** (email · password · MFA prompt) and
  **`/accept-invite`** (set name + password) pages — bare, outside the admin chrome. A
  **Users & access** admin screen (`/users`, `users:read`): user list with MFA status, an
  invite form (role select) surfacing the shareable accept link, the pending-invitations list,
  and **self-service MFA enrolment** (secret + `otpauth` URI → confirm a code). Verified
  end-to-end through the proxy: invite → accept → login → MFA enrol/verify.
- **Phase 1 — multi-tenancy + platform control plane (first slice).** The reference impl is now
  genuinely multi-tenant: a per-request `X-Tenant` context selects one in-memory `Store` per
  tenant via a context-var-backed proxy, so the ~hundreds of `store.*` call sites isolate by
  tenant with no changes (and the Phase 0 Postgres repos key off the same context). New
  **platform control plane** (`/platform/*`) — tenant provisioning, lifecycle (suspend/plan),
  and a platform audit log — gated by **platform roles** (`platform_super_admin`/`support`/
  `billing`) that are a hard trust boundary: a tenant `dvs_admin` holds `*` but is still
  rejected from the platform plane. Platform operators are global/tenant-independent.
  Verified live: provisioning a tenant yields full data isolation (seeded `zlits` herd vs an
  empty `demo`, same endpoint); tenant roles 403 on `/platform`. 45 tests pass.
- **Phase 0 — Postgres persistence foundation (multi-tenant from the start).** Opt-in Postgres
  backend behind `ZLITS_DATABASE_URL`; the in-memory store stays the default (demo + tests run
  with no database, `psycopg` imported lazily). Ships: `db/migrations/0001_init.sql` (platform
  `tenants` table + tenant-scoped registry tables, each with `tenant_id` and **row-level
  security** keyed on the per-request GUC `app.tenant_id`, fail-closed); a migration runner
  (`python -m zlits.migrate`); a connection + tenant-context layer (`zlits/db.py`); and a
  **repository seam** (`zlits/repository.py`) with in-memory + Postgres implementations — the
  **Animal** aggregate end-to-end as the reference pattern. Verified live: RLS isolates tenants
  (each sees only its rows, cross-tenant writes rejected), jsonb roundtrip, migration runner as
  a non-superuser owner; the 42 in-memory tests stay green (PG test skips without a DB). See
  `reference-impl/db/README.md` and `docs/saas-platform-architecture.md`.
- **Working dashboard filters.** The National Command pills are now live selectors —
  **province** (national roles), **species**, and **time range** (7 / 14 / 30 / 90 days). They
  thread through `/admin/kpis`, `/admin/overview`, `/admin/series`, `/admin/tasks` as query
  params; records lacking a field (e.g. integrators have no province) pass through so national
  metrics stay visible. Drill-down links carry the active province/species so **count still
  equals its drill-down** under a filter. Provincial vets stay pinned to their jurisdiction.
- **Animal record editing — closes the data-quality loop.** `PATCH /admin/animals/{id}` (new
  `herd:write` permission — DVS admin + provincial/official vet) corrects fields like district,
  holding, breed. An "Edit record" mode on the herd detail page. Fixing a record resolves its
  data-quality issue (the issues are computed, so e.g. correcting an invalid district makes the
  issue disappear). Contract + `AnimalUpdate` schema + test (fix → issue resolved).
- **Movement permit creation.** `POST /admin/movements` creates a permit in `draft` (the
  lifecycle then advances via transitions), gated by `movements:review`. "New permit" form on
  the Movements screen. Contract + `MovementCreate` schema + test.
- **Holding & keeper registration.** `POST /admin/holdings` and `POST /admin/keepers`, gated by
  `holdings:write` (DVS admin + provincial vet) — closing a previously dead permission that had
  no endpoint. Register forms on the Holdings/Keepers screens (shown only with the permission);
  holdings link to an existing keeper. Contract + schemas + tests added.
- **Public certificate verification (no-login).** A standalone `/verify` surface outside the
  admin chrome — token entry + a result card showing VALID / REVOKED / UNKNOWN, certificate
  details, a revocation warning, and a PDF link. The console layout now branches on route
  (`AppShell`): public routes get no sidebar / topbar / auth gate. The public JSON endpoint
  `GET /v1/verify/{token}` is enriched (valid_until, subject, pdf_url — already public via the
  HTML surface); `VerificationResult` schema updated to match.
- **Vaccination-campaign CRUD + workflow actions.** Full lifecycle on `campaigns:write` (DVS
  admin + provincial vet): create (`POST /admin/campaigns`), edit (`PATCH …/{id}`), delete
  (`DELETE …/{id}`), state transitions (`POST …/{id}/{action}` — pause | resume | complete,
  `completed` terminal), and **progress recording** (`POST …/{id}/record` — add vaccinations
  capped at target, log cold-chain exceptions, clear overdue follow-ups; recomputes coverage).
  Campaigns screen: a Create form plus per-card kebab actions (record vaccinations, clear
  follow-ups, log cold-chain, edit target, lifecycle, delete) and record/lifecycle buttons in
  the detail sheet. Contract (paths + `Campaign`/`CampaignCreate`/`Update`/`Progress` schemas)
  and tests added.
- **Console interactivity pass.** Row/card actions consolidated into a `⋯` kebab dropdown;
  clickable rows/cards open slide-in **detail sheets** — certificates (signature/issuance),
  movements (lifecycle stepper), integrators (per-key rotate/revoke), zones (version-history
  timeline), campaigns (coverage gauges). First-class **Holdings** and **Keepers** screens —
  detail sheets show linked records (holding → keeper + its animals; keeper → its holdings),
  cross-navigable into the herd, backed by new `GET /admin/holdings/{id}` and
  `/admin/keepers/{id}` detail endpoints. New **Audit** screen — filterable action log,
  HMAC-signed export download, and a data-access trail. New **Data Quality** triage screen —
  category summary cards (filterable) over the seeded issues (duplicate EID, missing holding,
  invalid district, stale record, unlinked movement); each row links to the record that needs
  fixing. **Global search** wired to `/admin/search` (debounced
  typeahead, keyboard nav); animals deep-link to a new **`/herd/{id}`** detail + lifecycle
  timeline. **Dark mode** (toggle + no-flash inline script) with charts and the Leaflet map
  re-toned for dark surfaces.
- **`web/` — modern operations console (Next.js 16 + React 19 + Tailwind v4 + shadcn/ui +
  Recharts + lucide).** A real SPA on top of the existing ZLITS JSON API (no backend rewrite):
  a BFF proxy (`/api/zlits/*`) forwards cookies so session auth + dev-login work same-origin.
  Governmental theme (soft-neutral bg, deep-navy grouped sidebar, emerald primary, severity-
  encoded colours). **National Command** dashboard follows the operations brief — *urgent
  first, context second, metrics third*: severity-grouped priority strip (Critical / Review /
  Maintenance), a 65/35 split (prioritised **work queue** + **province-risk / sync / recent-
  audit** panel), Recharts trends (registrations area + movement-pipeline bar), and a compact
  drill-down KPI band. Every number routes to its exact source list. Role switcher + scoped
  data. New API endpoints back it: `/admin/me`, `/admin/overview`, `/admin/series`,
  `/admin/movements`, `/admin/campaigns`.

### Fixed

- **BFF proxy 204 handling.** The proxy built a `Response` with a body for null-body statuses
  (204/205/304), throwing and 500-ing every `DELETE` — API-key revoke was broken. Now returns a
  null body for those.
- **Console stuck on "Loading…" via `127.0.0.1`.** Next 16 dev blocks cross-origin `/_next/*`
  resources, breaking hydration on `127.0.0.1`; added `allowedDevOrigins` + an auth-gate
  loading self-heal.
- **Kebab menu crash.** `DropdownMenuLabel` (Base UI `Menu.GroupLabel`) requires a `Menu.Group`
  wrapper; replaced the menu header with a plain element.
- **Auditor home 404.** The auditor's `ROLE_HOME` is `/audit`, but the SPA had no such route —
  login dead-ended. Added the Audit screen at `/audit`.
- **RBAC only gated actions, not navigation or pages.** The sidebar showed every section and
  any page was reachable (the API 403'd the data, leaving a dead empty screen). `/admin/me` now
  returns the role's resolved `permissions`; the sidebar hides items the user can't reach, a
  `PermGuard` denies direct navigation to unauthorized routes (route→perm derived from the nav),
  and the client capability helpers (`canIssueCerts`, …) are rebuilt on `hasPerm(me, perm)` —
  removing the duplicated client role model so it can't drift from the server.

### Changed

- **Reference impl refactored into an operational control room.** `app.py` split into a
  `zlits/` package (config, store, security, rbac, kpis, tasks, domain, seed, models, ui,
  routers). **Hardened RBAC** (5 roles — dvs_admin, provincial_vet, official_veterinarian,
  operator_admin, auditor — enforced per route + jurisdiction scoping + role-home routing +
  dev role switch). **Rich seed** (provinces, holdings/keepers, integrators with sandbox/live
  keys, permits across every lifecycle state, campaigns, audit + data-access, data-quality).
  **Server-rendered control room** (left sidebar, role homes, KPI tiles that drill into their
  exact source list — count==drilldown, work queue, themed dashboards, global search, status
  badges, formatted timestamps) backed by JSON endpoints (`/admin/kpis`, `/admin/tasks`,
  `/admin/search`). Health metrics labelled *simulated*. New tests: `test_control_room.py`.
- **Operational modules implemented** (control plane + UI):
  - **Zones** — list/declare/`PATCH`/expire/outbreak + version history; Leaflet map editor,
    WKT, gazette ref, effective/expiry.
  - **Integrators & keys** — accredit, issue (sandbox/live + scopes), rotate, revoke
    (secret shown once); conformance + error badges.
  - **Audit** — actor/action filters, **data-access log**, **signed audit export**.
  - **Herd lookup + holdings/keepers** first-class (animal timeline; `/admin/holdings`,
    `/admin/keepers`, `/admin/animals/{id}`).
  - **Movement permits** — full lifecycle (`draft→lodged→vet_review→approved|rejected→
    departed→arrived→completed|cancelled`) with validated transition endpoints.
  - **Public verification** — a polished standalone no-login surface (`/verify`).
  - **Thin field baseline** — mobile-friendly officer view (`/field`).
- **Certificates → delegated approval (sovereignty fix).** Integrators may only **request**
  (`POST /v1/certificates` → status `requested`, unsigned); only the authority (Official Vet /
  DVS) **issues & signs** (`POST /admin/certificates/{id}/issue`) and **revokes**
  (`POST /admin/certificates/{id}/revoke`). Client-side revoke removed.

- **Modern UI/UX pass.** Dependency-free design system (slate + emerald palette, soft
  shadows, type/space scale, rounded cards, pill badges, inline-SVG iconography). Information
  architecture splits **Needs attention** (urgent: outbreaks, blocked permits, expiring certs,
  DQ) from **Operations** (registrations, issued certs, integrators), each its own section with
  visual hierarchy. KPI tiles gain **trend indicators** (real 7d-vs-prior-7d deltas) and tinted
  icon chips; refined sidebar, topbar search, and tables.

### Contract (1.2.0-draft)

- `openapi.yaml` → 1.2.0-draft: `POST /certificates` is now a *request* (status `requested`);
  `Certificate.status` enum adds `requested`/`expired`; `Certificate.required` relaxed to
  `[id, kind, reference, status]` (a requested cert is unsigned); client revoke path removed.
- `openapi-admin.yaml` → 1.2.0-draft: adds certificate `issue`/`revoke`, movement transitions,
  and `Certificate`/`Movement`/`Revocation` schemas. Validator + conformance green.

### Added

- `reference-impl/`: a **runnable** FastAPI reference implementation of the contract
  (client API + a control-plane subset) with a thin Admin Portal UI — login + dev
  auto-login, dashboard, zones, and verify screens. In-memory store, per-operator bearer
  auth, `Idempotency-Key`, HMAC certificate signing, and a seeded demo (admin login, API
  key, zones, animal, movement, and a certificate with verify token `DEMO-TOKEN`). Tests
  (`pytest`) and a CI `reference-impl` job.
- `reference-impl/tests/test_conformance.py`: conformance gate asserting the live service
  emits every field the contract (`openapi.yaml`) marks `required` — ties the implementation
  to the contract so they cannot drift.
- `docs/admin-portal.md`: Admin Portal screen designs (ASCII mockups) for dashboard, zones,
  integrators/keys, herd lookup, certificates, audit, and public verification — each mapped
  to the control-plane (`openapi-admin.yaml`) or client (`openapi.yaml`) endpoints, plus RBAC.

## [1.1.0-draft] — 2026-06-03

### Added

- **Certificates** in the client contract (`openapi.yaml`, additive within `/v1`):
  `POST /v1/certificates`, `GET /v1/certificates/{id}`, `POST /v1/certificates/{id}/revoke`,
  with `Certificate` / `CertificateRequest` / `CertificateRevocation` schemas and an example.
  Registry-issued and e-signed; response carries `reference`, `verify_url` and `pdf_url`.
- **Control-plane spec** `openapi-admin.yaml` (separate `adminSession` security): zone
  authoring (`/admin/zones`, outbreak fast-path), integrator accreditation & API-key
  management (`/admin/integrators`, `/admin/keys`), and audit read/export.
- `docs/registry-operations.md`: operations & administration design (zone authorship,
  Admin Portal, certificates, roles, audit tiers, UI surfaces, field-capture model) —
  grounded in EU TRACES NT, Australia NLIS and NZ NAIT practice.

### Changed

- `scripts/validate.py` now validates **all** `openapi*.yaml` specs; CI lints both.
- README and CONTRIBUTING document the two-spec (client vs control-plane) split.

## [1.0.0-draft] — 2026-06-03

### Added

- Initial ZLITS API v1 contract (`openapi.yaml`, OpenAPI 3.1):
  - `POST /v1/animals`, `GET /v1/animals/{national_id}`
  - `POST /v1/movements`, `POST /v1/vaccinations`
  - `GET /v1/zones` (delta sync), `GET /v1/verify/{token}` (public), `GET /healthz`
  - Per-operator bearer auth, `Idempotency-Key` on writes, acknowledgement IDs.
- `README.md` (principle, legal basis, client integration model).
- `examples/` sample request/response payloads.
- Quality gate: `scripts/validate.py` + `validate-contract` CI workflow.

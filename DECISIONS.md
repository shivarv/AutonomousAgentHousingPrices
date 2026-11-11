# Decisions

Format: date — decision — alternatives considered — reason.

- 2026-11-10 — Merge mode is `pr` (gh is logged in and `origin` exists) — local merges — run-agent.sh
  rule: PR mode whenever GitHub is available.
- 2026-11-10 — Stack task branches (each branched from the previous task branch) and push them —
  local `--no-ff` merge (also needs approval); stop working — `gh pr` and `git merge` into main
  need an interactive approval that can't be given unattended (see BLOCKERS.md); stacking lets
  later tasks build on earlier ones while leaving the merge decision to the owner.
- 2026-11-10 — gh works in session 2: drop branch stacking, return to normal PR mode (branch each
  task from up-to-date main) — keep stacking — stacking was only a workaround for the blocker.
- 2026-11-10 — scripts/db.sh uses `-k /tmp` for the Unix socket and connects over TCP
  (localhost:5544) — socket in data/pg — the project path contains a space, which breaks socket
  paths in some clients; TCP matches DATABASE_URL.
- 2026-11-10 — Backend is a non-packaged uv project (`tool.uv.package = false`), imports rooted at
  backend/ (`app.*`, `pipeline.*`) — src-layout package — simplest for `uv run` and Alembic.
- 2026-11-10 — Alembic URL from app settings, overridable by ALEMBIC_DATABASE_URL (to migrate
  housing_test) — separate ini sections — one source of truth for the URL.
- 2026-11-10 — Frontend look: "survey map" palette (paper #eef2f4, harbour ink #14324a, survey-marker
  ochre #c98a0b focus/accent; shortage #b3261e and surplus #1f7a5c always paired with a sign/label;
  estimate violet #6b4fa0), Public Sans (US civic typeface, self-hosted via @fontsource, tabular
  numerals) — cream/serif or dark dashboard defaults — fits a civic planning audience, no
  external font requests.
- 2026-11-10 — Frontend lint is oxlint (the current Vite template default) — add ESLint —
  `npm run lint` is what the plan requires; oxlint covers react hooks rules.
- 2026-11-10 — Latest vintages: TIGER/Line 2026 (2020 tracts, 1,620 MA tracts; 351 towns =
  county subdivisions excluding the 6 "not defined" water records), ACS 2020-2024 5-year, CHAS
  2018-2022, PIT/HIC 2007-2025, HUD CoC boundaries 2025 (10 MA CoCs), Picture of Subsidized
  Households 2025 — older vintages — newest releases available on 2026-11-10.
- 2026-11-10 — huduser.gov answers non-browser clients with an empty HTTP 202; HUD downloads send
  a browser User-Agent string — skip HUD data — the files are public-domain federal data meant
  for download; no login or terms are bypassed.
- 2026-11-10 — ZIP→tract: HUD USPS crosswalk needs an API token we don't have; use the Census 2020
  ZCTA-tract relationship file, weighted by residential share = 2020 block housing units
  (TIGER tabblock20 HOUSING20, block internal point located in a ZCTA polygon) — land-area
  weights — residential weighting is what PLAN.md asks for.
- 2026-11-10 — RTA GTFS from the MobilityData catalogue mirror (latest.zip per feed), including
  WRTA and GATRA whose direct feeds are marked inactive — agency sites one by one — one stable
  source; stop locations change slowly. MBTA GTFS comes directly from cdn.mbta.com.
- 2026-11-10 — Parcels: MassGIS statewide L3 parcels gdb (754 MB, 2.2 M polygons, 2.55 M assessing
  rows) — 8.5 GB aggregate gdb / per-town downloads — fits the 8 GB budget. Owner name/address
  columns are never read or stored.
- 2026-11-10 — Shelters: no public structured list of MA shelter addresses with beds exists (HIC is
  CoC-level only). Use OpenStreetMap homeless-shelter features (10 in MA), with DV-related tags
  excluded in the Overpass query so DV locations are never downloaded — scraping commercial
  directories (terms) — only open-licensed option. Consequence handled in Phase 5.
- 2026-11-10 — Evictions: Eviction Lab tract filings (2000-2018, validated) — MA Trial Court
  dashboard (no machine-readable export) — only tract-level open source; its age is reported.
- 2026-11-10 — DATA_SOURCES.md is generated from a Python registry (pipeline/sources.py) plus the
  download manifests, and parsed back to load `data_sources` (matched to a stable key by dataset
  name) — hand-written markdown — keeps file, table and manifests consistent.

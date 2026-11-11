# Project: Massachusetts Housing Need & Site Finder

## Goal
Build a working product for **the whole state of Massachusetts** (all 351 cities and towns,
every census tract, 14 counties) that answers two questions:

**Outcome 1 – The picture:** How many people are homeless or at risk, where is the affordable
housing shortage, and which places are available and suitable for building new homes?
Delivered as statewide/county/town statistics and a ranked list of candidate construction sites.

**Outcome 2 – The site explorer:** An interactive map where a user can press "Show best
location", or drag a pin anywhere, and immediately see how many people experiencing
homelessness (estimated) and at-risk households could benefit, and whether there is a shortage
or surplus of affordable homes, in two ways:
- **Areas:** the subdivision under the pin (tract, Boston neighbourhood, town, county or
  homelessness region) is highlighted with its numbers, and neighbouring areas can be added to
  a "benefit area" with a running total.
- **Rings:** three distance rings around the pin.

Boston and Greater Boston matter most (most people, most need), but everything must work
statewide.

Deliverables:
1. Data pipeline: downloads real public data, cleans it, loads it into Postgres.
2. Affordable housing shortage/surplus for every tract.
3. Modelled homelessness distribution per tract (clearly labelled estimates).
4. Housing Need Index (0-100) for every tract.
5. Candidate construction sites, screened and ranked, with reasons.
6. Home-value model (land/home cost context for sites).
7. FastAPI backend, including a radius-stats service for any point on the map.
8. React web app: statistics overview, site list, and the interactive site explorer map.
9. Docker files and a written report.

## Audience
City planners and housing nonprofits. Every number must be trustworthy and traceable, and
every estimate must be labelled as an estimate with its method available.

## How to work (details in CLAUDE.md and .claude/skills/)
- Branch per task, split into items, commit per item, merge to main when checks pass
  (skill: git-task-workflow).
- Backend layering controller → service → DAO → model/schema (skill: python-backend).
- Database: private local Postgres 18 on port 5544 (skill: postgres). No PostGIS: geometry as
  GeoJSON in jsonb; spatial work with geopandas/shapely/pyproj in Python.
- Frontend: modular feature folders, Tailwind v4 (skills: react, tailwind, frontend-design).
- Maps: Leaflet + OpenStreetMap tiles; address search with the US Census Geocoder. No Google
  Maps and no API keys for maps.
- Docker files (skills: docker-project-foundations, docker-compose-patterns,
  docker-build-strategies). Docker isn't installed here: write the files, don't run them.

## Target layout
```
backend/    FastAPI app (app/) + data pipeline (pipeline/) + alembic/ + tests/   (one uv project)
frontend/   React + TypeScript + Vite + Tailwind
scripts/    db.sh (local Postgres), validate.py
reports/    REPORT.md, STATISTICS.md, model_metrics.json, top_tracts.csv, candidate_sites.csv,
            data_audit.md, charts
data/       raw/ interim/ processed/ pg/   (git-ignored)
compose.yaml, backend/Dockerfile, frontend/Dockerfile
```

## Data sources (try in order; log failures in BLOCKERS.md and move on)
| Need | Primary source | Fallback |
|---|---|---|
| Tract, county, municipality boundaries | Census TIGER/Line (state FIPS 25, latest year) | MassGIS municipal boundaries |
| Boston neighbourhood boundaries | Analyze Boston (BPDA neighbourhood boundaries) | — |
| Homelessness region (CoC) boundaries | HUD CoC GIS boundaries | Build from CoC member-municipality lists |
| Population, income, poverty, overcrowding, tenure, rent burden, housing units, vacancy | ACS 5-year via api.census.gov for every MA tract (env var CENSUS_API_KEY) | data.census.gov bulk download |
| Affordable housing gap | HUD CHAS tract-level data (extremely-low-income renter households; units affordable and available to them) | ACS income x gross-rent tables |
| Homeless counts (CoC level ONLY) | HUD Point-in-Time counts for every MA Continuum of Care, sheltered vs unsheltered, several years | HUD Exchange CoC reports |
| Shelter beds | HUD Housing Inventory Count (HIC) per MA CoC | — |
| Shelter locations | Public shelter directories (mass.gov, CoC websites, Analyze Boston). Never include domestic-violence shelters (confidential) | HIC project names geocoded with the Census Geocoder |
| Student homelessness | MA DESE homeless student counts for every school district | — |
| Subsidised housing | HUD LIHTC database, HUD Picture of Subsidized Households (MA) | — |
| Parcels, land use, assessed values | MassGIS Standardized Assessors' Parcels (statewide; land-use codes, lot size, land and building values) | Analyze Boston property assessment |
| Build constraints | MassGIS Protected and Recreational Open Space, MassDEP Wetlands, FEMA National Flood Hazard Layer | — |
| Zoning for multifamily | MBTA Communities (Section 3A) district maps from mass.gov | — |
| Transit | MBTA GTFS stops (subway, commuter rail, bus); regional transit authority GTFS | — |
| Value/rent trends | Zillow Research ZHVI and ZORI (all MA ZIPs) | Redfin Data Center |
| Evictions | MA Trial Court housing court filings | Eviction Lab |
| ZIP to tract mapping | HUD USPS ZIP-tract crosswalk | Census ZCTA-to-tract relationship file |

Data size: statewide parcel and constraint layers are large. Keep only the columns and parcels
you need (e.g. vacant/developable parcels with geometry; other parcels attributes only), simplify
geometry, and stay within the 8 GB data budget.

## Tasks (in order; each task = one branch; split into items before starting)

### Phase 1 – Foundations
- [x] Repo skeleton: folders above, root README stub, .gitignore additions.
  - [x] item: folders (backend, frontend, scripts, reports, data/*) with keep files
  - [x] item: root README stub, .gitignore additions, PROGRESS/DECISIONS/BLOCKERS files
- [x] scripts/db.sh (init/start/stop/status) for the local Postgres on port 5544; databases
      `housing` and `housing_test`.
  - [x] item: scripts/db.sh with idempotent init/start/stop/status, verified
- [x] Backend skeleton: uv project (Python 3.12), FastAPI app with core/, models/, schemas/,
      dao/, services/, controllers/, dependencies.py; /api/health; Alembic; pytest + ruff passing.
  - [x] item: uv project, app layers (core/models/schemas/dao/services/controllers), /api/health
  - [x] item: Alembic configured against DATABASE_URL
  - [x] item: pytest + ruff config and health tests passing
- [x] Frontend skeleton: Vite React TS, Tailwind v4, react-router, react-query, react-leaflet,
      @/ alias, layout shell; build and lint passing.
  - [x] item: Vite React TS scaffold, Tailwind v4, @/ alias, dependencies
  - [x] item: app providers (react-query), router, layout shell, placeholder-free pages
  - [x] item: build and lint passing

### Phase 2 – Data collection (backend/pipeline/download/)
- [x] One idempotent download module per source, saving untouched files to data/raw/<source>/.
  - [x] item: download helpers (idempotent, manifest with url/date/sha256)
  - [x] item: boundaries (TIGER 2026 tracts/towns/counties, Boston neighbourhoods, HUD CoC 2025)
  - [x] item: ACS 2020-2024 5-year tract variables
  - [x] item: HUD CHAS 2018-2022 tract tables + dictionary
  - [x] item: HUD PIT and HIC counts by CoC
  - [x] item: subsidised housing (LIHTC, Picture of Subsidized Households)
  - [x] item: transit GTFS (MBTA + RTAs)
  - [x] item: Zillow ZHVI/ZORI and ZCTA-tract relationship file
  - [x] item: MassGIS parcels (assessor attributes + developable candidates)
  - [x] item: build constraints (open space, wetlands, FEMA flood) and MBTA Communities 3A
  - [x] item: shelters, DESE homeless students, evictions (best effort)
  - [x] item: pipeline.download CLI running every module
- [x] DATA_SOURCES.md entries for every dataset, plus a `data_sources` table loaded from it.
  - [x] item: dataset registry + DATA_SOURCES.md generated from download manifests
  - [x] item: DataSource model + first Alembic migration
  - [x] item: data_sources loader (DAO + service) from DATA_SOURCES.md, with tests
- [x] reports/data_audit.md: rows, years, geography, missing-value rates, known issues.
  - [x] item: pipeline.audit generating reports/data_audit.md for all 23 datasets

### Phase 3 – Database schema and loading
- [x] Models + Alembic migrations: data_sources, counties, municipalities, cocs (with member
      municipalities and boundary), boston_neighbourhoods (boundary, member tracts by area
      share), tracts (geoid, county, municipality, coc, neighbourhood, centroid,
      simplified GeoJSON, land area), tract_metrics (tract x metric x year, with source_id),
      homelessness_counts (coc x year x sheltered/unsheltered/total), shelters (name, type,
      beds, lat/lon, source; no DV shelters), subsidised_housing, transit_stops, parcels
      (developable candidates only, with geometry), site_candidates, model_runs.
  - [x] item: ORM models for every table (geography, metrics, homelessness, housing, sites)
  - [x] item: Alembic migration, applied to housing and housing_test (downgrade/upgrade checked)
- [x] Pipeline clean/ + load.py: cleaned data into the tables via DAOs. ZIP data to tracts via
      the crosswalk, weighted by residential share (record in DECISIONS.md).
  - [x] item: clean geography (counties, towns, CoCs, neighbourhoods, tracts + area shares)
  - [x] item: clean ACS, PIT/HIC, shelters, subsidised housing, transit, ZIP weights, Zillow, evictions
  - [x] item: load.py via BulkDao/LoadService, dropped-row log and reports/load_summary.md
- [x] Tests: tract count matches statewide TIGER, 351 municipalities, 14 counties, every MA
      CoC present, no duplicate geoids, every metric row has a source, dropped rows logged.
  - [x] item: tests/test_data_integrity.py against the loaded housing database

### Phase 4 – Affordable housing shortage
- [x] Per tract from CHAS: extremely-low-income (<=30% AMI) and very-low-income (<=50% AMI)
      renter households, units affordable and available to them, and the gap
      (households - available units; negative = surplus). Also affordable units per 100 ELI
      renters.
  - [x] item: pipeline.features.affordability (CHAS Tables 8, 15C, 14B) loaded as tract metrics
  - [x] item: tests (gap arithmetic, coverage, VLI includes ELI)
- [x] Context per tract: total housing units, vacant for rent/sale (ACS), subsidised units.
  - [x] item: metrics loaded in Phase 3 (ACS housing_units, vacant_for_rent/sale; HUD PSH hud_assisted_units; LIHTC lihtc_low_income_units); coverage test for every tract
- [x] Aggregate to municipality, county and state. Tests that tract sums equal the totals.
  - [x] item: area_metrics table + tract_municipalities.housing_share (migrations)
  - [x] item: pipeline.features.aggregate (county/CoC/neighbourhood/state by primary area; towns by block housing share)
  - [x] item: tests (unit arithmetic; DB totals equal tract sums at every level, 351 towns)

### Phase 5 – Homelessness: official counts and modelled distribution
- [x] Official layer: PIT counts per CoC and year (sheltered, unsheltered, total, trend) and
      HIC beds per CoC. These are the only exact figures; present them as CoC totals.
  - [x] item: homelessness DAO + schemas + service (CoC series with sheltered/unsheltered/total, year-on-year trend, HIC beds, statewide sum, "official CoC count" label)
  - [x] item: tests (trend arithmetic, every CoC has the latest year, state = sum of CoCs)
- [x] Modelled layer: allocate each CoC's latest total to its tracts. Sheltered people by share
      of the CoC's shelter beds located in each tract; unsheltered and at-risk weighting by the
      tract's share of severely rent-burdened ELI renter households. Tract estimates must sum
      exactly to the CoC total. Store as metric `homeless_estimate` with method and year.
  - [x] item: pipeline.features.homeless_estimate (allocation, exact CoC sums, flags) + load + re-aggregate
  - [x] item: tests (sums equal PIT per CoC, estimate flag/method/year on every row, non-negative)
- [x] Document the method and its limits in DECISIONS.md and reports/REPORT.md. Every API
      response and UI label for this metric says "estimate".
  - [x] item: reports/REPORT.md method + limits section; DECISIONS.md limits entry
  - [x] item: HomelessFigure schema (label "estimate" / "official CoC count", method, year) for Phases 9-10, with tests
- [x] Sensitivity check: alternative allocation (population share); report how much the top
      areas change.
  - [x] item: pipeline.features.homeless_sensitivity (population-share allocation, top-20 tract/town overlap, rank correlation) -> reports/homeless_sensitivity.md
  - [x] item: tests + REPORT.md summary

### Phase 6 – Housing Need Index
- [x] Components scaled 0-1: affordable gap per ELI renter, severe rent burden share, eviction
      filing rate, poverty rate, overcrowding rate, 5-year rent growth, homeless estimate per
      1,000 residents, distance to nearest shelter or subsidised unit.
  - [x] item: pipeline.index.components (8 raw components, direction, percentile scaling 0-1, missing kept NULL)
  - [x] item: tests (scaling range/order, distance, ratio NULL on zero denominators)
- [x] Equal weights to start (justify changes in DECISIONS.md); store index and components.
  - [x] item: pipeline.index.need_index (weighted mean of available scores x 100, min 5 of 8, flags) -> metrics_need.parquet, loaded
  - [x] item: tests (0-100 range, equal weights, renormalisation over missing, NULL + flag below minimum; loaded rows)
- [x] Sensitivity check with 3 alternative weightings; report top-20 stability.
  - [x] item: pipeline.index.sensitivity (affordability-heavy, homelessness/eviction-heavy, dense-components-only) -> reports/need_index_sensitivity.md/.json
  - [x] item: tests + REPORT.md summary
- [x] reports/top_tracts.csv (top 50 statewide plus top 10 per county) and a municipality
      summary (population-weighted index).
  - [x] item: population-weighted need_index in area_metrics (town/county/CoC/neighbourhood/state)
  - [x] item: pipeline.index.report -> reports/top_tracts.csv and reports/municipality_need.csv
  - [x] item: tests (weighted mean arithmetic, CSV contents)

### Phase 7 – Home-value model (cost context for sites)
- [x] Residential parcels statewide; split 70/15/15 stratified by county; test split saved once,
      never used for tuning.
  - [x] item: pipeline.clean.parcels (assessor attributes without owner/address, parcel points located in tract/town/county)
  - [x] item: pipeline.model.dataset (residential use codes, value filters logged, 70/15/15 split stratified by county, saved once)
  - [x] item: tests (split proportions/stratification/immutability, lot size units)
- [x] Baseline: municipality median value. Then linear regression and LightGBM (validation
      tuning only). Target: beat baseline MAPE by >= 25% on test.
  - [x] item: pipeline.model.home_value features (parcel, train-only town/tract medians, tract context)
  - [x] item: baseline, ridge and gradient boosting (HistGradientBoosting; LightGBM blocked) tuned on validation; one final test evaluation -> reports/model_metrics.json
  - [x] item: tests (MAPE, baseline fallback, train-only encodings, test never used for selection)
- [x] Also estimate land value per square foot by tract (from assessor land values) for site
      cost scoring.
  - [x] item: pipeline.features.land_value (median LAND_VAL / lot sq ft per tract, taxable non-condo parcels; flag < 10 parcels) loaded into tract_metrics
  - [x] item: tests (filters, record summing, flag, missing stays NULL)
- [x] Save model, reports/model_metrics.json, feature importances, error-by-county chart,
      model_runs row.
  - [x] item: pipeline.model.artifacts (permutation importances on validation, error-by-county chart/table, model_runs row)

### Phase 8 – Candidate construction sites
- [x] Screening: parcels with vacant or developable land-use codes (document the codes used),
      minimum lot size (start 0.5 acre; record choice), not in protected open space, wetlands
      or FEMA 100-year flood zones (drop parcels with >50% overlap; flag partial overlap).
  - [x] item: pipeline.sites.screen (developable codes, 0.5-acre GIS lot, open space/wetland/flood overlap shares and union, 3A district, simplified boundary)
  - [x] item: tests (codes and sums, lot size and poly type, overlap union not double-counted)
- [x] Features per site: need index and affordable gap within 1.5/5/15 km, homeless estimate
      and shelter beds within those rings, distance to nearest MBTA/RTA stop, inside an MBTA
      Communities (3A) district, estimated land cost, lot size, municipality.
  - [x] item: app.services.rings (geodesic circles, tract area shares, share-weighted totals, weighted mean) shared with /api/area-stats
  - [x] item: pipeline.sites.features (rings 1.5/5/15 km, nearest stop, shelters, land cost, municipality)
  - [x] item: tests (circle area, shares inside/crossing/outside, missing values, land cost)
- [x] Site score 0-100 with documented weights; a plain-English "why this site" summary
      generated from the features (no invented facts).
  - [x] item: pipeline.sites.score (7 weighted percentile components, ranks state/county, missing component flagged)
  - [x] item: plain-English summary from the site's own features (strengths, need, gap, estimate label, transit, land cost, flags)
  - [x] item: tests (percentile bounds/direction, score range, missing = 0, summary facts)
- [x] reports/candidate_sites.csv: top 100 statewide and top 10 per county. Store all scored
      sites in site_candidates.
  - [x] item: pipeline.sites.load (candidate_sites.csv, parcels, site_candidates, model_runs site_scoring row); bulk batches capped by parameter limit
  - [x] item: tests (batch size, JSON cleaning, report selection) and REPORT.md 3.5

### Phase 9 – Backend API (controllers → services → DAOs)
- [x] GET /api/stats/overview?level=state|county|municipality&id= : population, homeless counts
      (official, by CoC, with trend), shelter beds, ELI renters, affordable gap, vacancy, need index.
  - [x] item: scripts/seed_test_db.sh (migrate housing_test, copy housing data) and `seeded` test fixture
  - [x] item: AreaDao, MetricValue schema, StatsService.overview (CoC official counts + trend, area estimate, HIC beds), controller
  - [x] item: API tests (state sum = CoCs, county/town, validation and 404)
- [x] GET /api/tracts?county=&municipality= (GeoJSON with index + key metrics; statewide must
      be fast: simplified geometry, cached) and GET /api/tracts/{geoid}.
  - [x] item: TractDao, TractService (pre-serialised GeoJSON cached per filter, detail with every metric, source, year, flags), controller, gzip
  - [x] item: API tests (1,620 features < 1 s warm, filters, estimate labels, 404)
- [x] GET /api/sites?county=&municipality=&limit= and GET /api/sites/{id}; GET /api/sites/best
      (top site overall or within a filter).
  - [x] item: SiteDao, SiteService (ranked list with total, best with offset for "next best", detail with rings, components, weights, overlaps), controller
  - [x] item: API tests (ranking, filters, best/next, labels, 404/422)
- [x] POST /api/area-stats {lat, lon, radii_km: [r1, r2, r3]}: for each ring, totals weighted by
      the share of each tract's area inside the circle (geodesic buffers via pyproj): estimated
      homeless, at-risk households (severely burdened ELI renters), ELI renter households,
      affordable units available, gap (shortage or surplus), shelters and beds, subsidised units,
      population. Also return "nearby points" for drawing: tracts with their estimate and
      centroid, and shelters with beds, inside the largest ring. Response < 1 s statewide.
  - [x] item: GeoDao + GeoIndex (process-wide cache per database: tract polygons, metric arrays, area STRtrees, neighbours, point layers)
  - [x] item: AreaService.ring_stats (geodesic rings, area-share totals, gap status, shelters, nearby tracts/shelters, sources), controller
  - [x] item: API tests (Boston/Worcester/Springfield, all metrics, < 1 s, validation and outside-MA message)
- [x] GET /api/areas/at?lat=&lon=&level=tract|neighbourhood|municipality|county|coc : the area
      containing the point (point-in-polygon with a cached shapely STRtree), with its boundary
      (simplified GeoJSON), neighbouring areas' ids, and the same metrics as area-stats.
      Homeless figure is the official count at level=coc and the summed estimate otherwise;
      the response says which. Points outside MA (or outside Boston for neighbourhood) return
      a clear message.
  - [x] item: GeoIndex memberships (tract weights per area, same rules as area_metrics) and official PIT/HIC per CoC
  - [x] item: AreaService.area_at (STRtree point-in-polygon, boundary, neighbours, figures; official count at CoC, estimate elsewhere), controller
  - [x] item: API tests (three cities x levels, CoC estimate sum = official, outside Boston/MA messages)
- [x] GET /api/areas?level=&bbox= : boundaries for drawing the outline layer (simplified, cached).
  - [x] item: AreaService.outlines (all areas of a level, pre-serialised and cached; bbox via STRtree), controller
  - [x] item: API tests (counts per level, bbox, validation)
- [x] POST /api/areas/summary {level, ids: [...]} : combined totals for a user-built benefit area.
  - [x] item: AreaService.summary (combined tract weights per level, official at CoC level), controller
  - [x] item: API tests (counties and towns add up to the state, neighbours, CoC official, validation)
- [x] GET /api/homelessness (per CoC by year, labelled CoC-level), GET /api/shelters,
      GET /api/model/metrics, GET /api/sources.
  - [x] item: ShelterDao/Service, ModelService, reference controller (homelessness overall and per CoC, shelters, model metrics from model_runs, sources)
  - [x] item: API tests (CoC-level labels, no DV shelters, model metrics, sources)
- [x] API tests for every endpoint against housing_test, including validation errors (radius
      limits 0.5-80 km, points outside MA return a clear message).
  - [x] item: route-coverage test (every OpenAPI path is called by a test); validation cases in each endpoint test file

### Phase 10 – Frontend
- [x] Overview page (Outcome 1): statewide headline statistics, CoC homelessness trend chart,
      affordable shortage by county, top municipalities by need, and the ranked candidate site
      list (filterable by county/town, each row links to the map).
  - [x] item: GET /api/stats/areas (county/town table for rankings and filters) + tests
  - [x] item: shared UI (loading/error states, estimate/official label, select), areas feature (filters), sites feature (ranked list linking to the map)
  - [x] item: overview feature (headline stats with sources, PIT trend line, CoC table, county shortage bars, top towns), screenshot checked
- [x] Site explorer map (Outcome 2), features/site-explorer:
  - Opens on all of Massachusetts; county and town filters zoom the map; address search
    (Census Geocoder).
  - "Show best location" button: drops the pin on the top-ranked site (respecting filters);
    "Next best" steps through the list.
  - Draggable pin: drag it anywhere (or click the map) and the rings and numbers update
    (debounced call to /api/area-stats).
  - Mode toggle: **Areas** (default) or **Rings**.
  - Areas mode: a boundary-level selector (Census tract, Boston neighbourhood, City/town,
    County, Homelessness region). Faint outline lines show all areas at that level; the area
    under the pin is highlighted and filled, with its name and numbers. Click neighbouring
    areas to add/remove them from the "benefit area"; a running total shows estimated homeless
    people, at-risk households, affordable shortage/surplus, shelters and beds for the whole
    selection. "Clear" resets it. Label the homeless figure "official count" at region level
    and "estimate" at every other level.
  - Rings mode: three concentric rings around the pin with presets Urban 1.5 / 5 / 15 km
    (default) and Regional 5 / 25 / 50 km, plus a custom slider per ring.
  - Small dots around the pin inside the rings: tract centroids sized by estimated homeless
    count (labelled "estimate"), and shelters with bed counts (a distinct marker).
  - Side panel per ring: estimated homeless nearby, at-risk households, affordable units,
    shortage/surplus (shown in red for shortage, green for surplus), shelters and beds.
  - Layer switcher for the background: Need Index, affordable gap, homeless estimate,
    candidate sites; legend for each.
  - [x] item: GET /api/geocode (Census Geocoder relay, MA matches only) + tests
  - [x] item: explorer state, API hooks (debounced area-stats/areas-at, outlines, summary, tracts, geocode)
  - [x] item: map layers (tract choropleth with classed CVD-safe scales, outlines with pin area + benefit areas, draggable pin, rings, nearby estimate dots and shelters, site markers, viewport zoom to filters)
  - [x] item: panel (filters, best/next best, address search, mode toggle, layer select, keyboard pin control, areas and rings panels, legend, deep links ?site= / ?lat=&lon=&mode=), screenshots checked
- [x] Tract and site detail panels: every number with its source and year; estimates labelled.
  - [x] item: site provenance (year and source per feature group) in /api/sites/{id} + test
  - [x] item: tract detail panel (all metrics grouped, source, year, estimate and flags) in Areas mode; site detail panel (score breakdown, rings, land cost, transit, zoning, constraints, provenance); screenshot checked
- [x] Pages: Overview, Site explorer (home), Methodology & sources, About the estimates.
  - [x] item: methodology feature (methods in prose, live model results and site weights from /api/model/metrics, sources table from /api/sources; #homeless-estimate anchor for HomelessFigure.method_url)
  - [x] item: About the estimates page (what an estimate is, limits, sensitivity, privacy); screenshot checked
- [x] Loading, error and empty states everywhere; responsive down to phone width; the map is
      keyboard accessible (pin can be moved with arrow keys).
  - [x] item: map layer status overlay (loading/error), collapsible legend, fixed-height map on phones; every async view has loading/error/empty states
  - [x] item: keyboard: arrow-key pin control, focus-visible outlines, labelled controls, radio/pressed states; phone-width screenshots checked

### Phase 11 – Docker
- [x] backend/Dockerfile (multi-stage, uv, non-root), frontend/Dockerfile (build + static
      server), compose.yaml (postgres:18 with healthcheck, backend runs migrations then
      uvicorn, frontend), .dockerignore files. Validate YAML parses and paths exist; note in
      README that it's untested here.
  - [x] item: backend/Dockerfile (uv multi-stage, non-root, migrations then uvicorn) + backend/.dockerignore
  - [x] item: frontend/Dockerfile (npm build, nginx static server proxying /api) + frontend/.dockerignore
  - [x] item: compose.yaml (postgres:18 healthcheck, backend, frontend, optional pipeline profile), static validation test, README note

### Phase 12 – Statistics, report and final checks
- [x] reports/STATISTICS.md (Outcome 1 in writing): statewide and per-county homeless counts and
      trends, shelter capacity, affordable shortage, top need areas, top candidate sites.
  - [x] item: pipeline.stats_report (figures via StatsService/HomelessnessService/SiteService; CoC official counts, county estimates labelled) + tests
  - [x] item: reports/STATISTICS.md generated
- [x] reports/REPORT.md: question, data, methods (especially the homeless estimate and site
      scoring), results, limitations, next steps.
  - [x] item: question, data summary, results (figures from STATISTICS.md / model_metrics.json), limitations, next steps; methods 3.1-3.5 already written in earlier phases
- [x] README.md: what it is, how to run (local and Docker), how to rebuild data from scratch.
  - [x] item: README (what it is, local run and checks, full rebuild order, Docker untested note, licences)
- [ ] scripts/validate.py passes (see Definition of done).

## Definition of done
All tasks merged into main AND `uv run --project backend python scripts/validate.py` exits 0.
validate.py checks that:
- every metric in tract_metrics has a source in data_sources, and DATA_SOURCES.md lists them all;
- homeless estimates per tract sum to the official CoC totals (within rounding);
- tract affordable-gap sums match municipality/county/state totals;
- Need Index and site scores are within 0-100 with no missing values (or each gap documented);
- site_candidates is non-empty and no candidate overlaps >50% with open space, wetlands or flood zones;
- /api/area-stats returns all metrics for 3 rings at a Boston, a Worcester and a Springfield point;
- /api/areas/at returns the right tract, town, county and CoC for those three points, and the
  summed tract estimates for a CoC equal its official count;
- reports/model_metrics.json exists; the test result meets the target, or REPORT.md says
  plainly that it doesn't (never change the target);
- reports/STATISTICS.md, REPORT.md, top_tracts.csv and candidate_sites.csv exist and aren't empty;
- the database covers all MA tracts, 351 municipalities, 14 counties;
- backend `pytest` and `ruff check` pass; frontend `npm run build` and `npm run lint` pass;
- git: no unmerged task/* branches, working tree clean (and, in PR mode, no open PRs).
Then write DONE to the file STATUS (on main).

## Out of scope
User accounts, paid data or paid map APIs, scraping sites whose terms forbid it, exact
locations of individual homeless people, publishing domestic-violence shelter locations,
deploying anywhere.

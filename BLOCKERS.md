# Blockers

- 2026-11-10 — (RESOLVED 2026-11-10, session 2) `gh pr create` / `git merge` stopped at a
  permission approval prompt in session 1. In session 2 `gh` works unattended, so PR mode is
  used normally; the stacked branches were merged in order via PRs.
- 2026-11-10 — Shelter locations with bed counts: no public machine-readable source (mass.gov
  pages return 403 to automated clients; HIC is published per CoC only). Fallback: OSM shelters
  (10 locations, no beds). Phase 5 sheltered allocation by tract bed share is therefore not
  possible as specified; see DECISIONS.md for the fallback chosen there.
- 2026-11-10 — MA DESE homeless student counts: published only on mass.gov / DESE web pages that
  refuse automated clients (403); skipped (optional context, not used by any required metric).
- 2026-11-10 — MA Trial Court eviction filings: no downloadable dataset; Eviction Lab used.
- 2026-11-10 — LightGBM cannot load on this Mac: its wheel links @rpath/libomp.dylib with rpaths
  only to Homebrew/MacPorts locations, and libomp is not installed (no global installs allowed).
  Tried (1) plain import, (2) preloading scikit-learn's bundled libomp via ctypes RTLD_GLOBAL,
  (3) DYLD_FALLBACK_LIBRARY_PATH pointing at that libomp. Fallback: scikit-learn
  HistGradientBoostingRegressor (histogram gradient boosting, the algorithm family LightGBM
  implements; OpenMP bundled). See DECISIONS.md.

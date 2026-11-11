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

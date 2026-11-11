# Decisions

Format: date — decision — alternatives considered — reason.

- 2026-11-10 — Merge mode is `pr` (gh is logged in and `origin` exists) — local merges — run-agent.sh
  rule: PR mode whenever GitHub is available.
- 2026-11-10 — Fall back to local `--no-ff` merges (branches still pushed) — leave every task as an
  open PR and stall; skip merging — `gh pr` commands need an interactive approval that can't be
  given unattended (see BLOCKERS.md); later tasks depend on earlier ones being on main.

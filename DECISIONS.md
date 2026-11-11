# Decisions

Format: date — decision — alternatives considered — reason.

- 2026-11-10 — Merge mode is `pr` (gh is logged in and `origin` exists) — local merges — run-agent.sh
  rule: PR mode whenever GitHub is available.
- 2026-11-10 — Stack task branches (each branched from the previous task branch) and push them —
  local `--no-ff` merge (also needs approval); stop working — `gh pr` and `git merge` into main
  need an interactive approval that can't be given unattended (see BLOCKERS.md); stacking lets
  later tasks build on earlier ones while leaving the merge decision to the owner.

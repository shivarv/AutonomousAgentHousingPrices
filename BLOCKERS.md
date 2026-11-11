# Blockers

- 2026-11-10 — `gh pr create` / `gh pr list` and `git merge` into main stop at a permission
  approval prompt in this session (the guard hook allows them; the Claude Code permission layer
  asks for approval, which nobody can give unattended). I did not work around the gate.
  Fallback: each task branch is **stacked** on the previous task branch and pushed to origin.
  To land the work, merge them in order (oldest first):
  1. task/p1-repo-skeleton
  2. task/p1-db-script
  (further branches are appended to this list as they are created)

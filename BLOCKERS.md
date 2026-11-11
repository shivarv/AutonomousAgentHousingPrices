# Blockers

- 2026-11-10 — `gh pr create` / `gh pr list` stop at a permission approval prompt in this unattended
  session (the guard hook allows them; the Claude Code permission layer asks for approval, which
  nobody can give). Fallback: task branches are still pushed to origin for the record, and merged
  locally into main with `git merge --no-ff` (local-mode procedure). main is not pushed (rule:
  never push main). The owner can push main or open PRs afterwards.

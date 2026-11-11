---
name: git-task-workflow
description: The branch-per-task workflow for this project - split each task into items, work on a task branch, commit per item, verify, then merge via a GitHub pull request (PR mode) or a local merge (local mode), and delete the branch. Use at the start and end of every task and whenever committing.
---

# Git task workflow

Every task in PLAN.md is done on its own branch and merged into `main` only when its checks pass.

**Mode:** the environment variable `MERGE_MODE` is set by run-agent.sh:
- `pr` → GitHub is connected: merge through a pull request with the `gh` CLI.
- `local` → no GitHub login: merge locally with `git merge --no-ff`.

## 1. Start (or resume) a task
```bash
git status                       # must be clean; if not, see "Resuming"
git switch main
[ "$MERGE_MODE" = pr ] && git pull --ff-only origin main
git switch -c task/<phase>-<short-slug>      # e.g. task/p4-baseline-model
```

## 2. Split the task into items
Before coding, write the items as sub-bullets under the task in PLAN.md:
```
- [ ] Baseline model ...
  - [ ] item: split data and save test set
  - [ ] item: municipality-median baseline
  - [ ] item: metrics written to reports/model_metrics.json
  - [ ] item: tests
```
Items are small (roughly 15-45 minutes each).

## 3. One commit per item
After each item: run the relevant checks, tick the item, then
```bash
git add -A
git commit -m "<area>: <what changed>"     # e.g. "model: add municipality baseline"
```

## 4. Verify
All of these must pass before merging (run whichever exist so far):
```bash
(cd backend && uv run pytest && uv run ruff check .)
(cd frontend && npm run build && npm run lint)
```
Tick the task itself in PLAN.md and add a line to PROGRESS.md as the last commit on the branch.

## 5a. Merge — PR mode (`MERGE_MODE=pr`)
```bash
git push -u origin task/<phase>-<short-slug>
gh pr create --base main --head task/<phase>-<short-slug> \
  --title "<Phase N>: <task title>" \
  --body "<what changed, items done, checks run and their results, decisions made>"
gh pr merge task/<phase>-<short-slug> --merge --delete-branch
git switch main
git pull --ff-only origin main
git branch -d task/<phase>-<short-slug> 2>/dev/null || true
```
- The PR body is the record for the owner: list items, test results, and anything uncertain.
- If `gh pr merge` fails (conflict, network), fix the branch, push again and retry. If it can't
  be fixed, leave the PR open, note it in BLOCKERS.md and continue with an independent task.

## 5b. Merge — local mode (`MERGE_MODE=local`)
```bash
git switch main
git merge --no-ff task/<phase>-<short-slug> -m "Merge task/<phase>-<short-slug>: <task title>"
git branch -d task/<phase>-<short-slug>
```

## Resuming
At the start of a session, if `git branch --show-current` is a `task/...` branch, finish that
task's unticked items. In PR mode also check `gh pr list --state open`: finish and merge any
open PR from an earlier session before starting new work. Commit or discard any uncommitted
changes before switching branches.

## If checks fail and can't be fixed
Don't merge. Commit the work on the branch (in PR mode, push it and open the PR as a draft with
`gh pr create --draft`), write the problem in BLOCKERS.md, and move to the next task that
doesn't depend on it.

## Never
- Never commit directly to main except in local mode for docs-only fixes; in PR mode,
  everything goes through a PR.
- Never push to main, never `--force`, never delete remote branches other than via
  `gh pr merge --delete-branch`, never rewrite history.
- Only these gh commands are allowed: `gh pr create|merge|list|view|status|checks|diff|comment`,
  `gh auth status`, `gh repo view`. The guard hook blocks everything else.

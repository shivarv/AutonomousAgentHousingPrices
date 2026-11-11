# Rules for the autonomous agent

## Working style
- You are working unattended. Never ask questions; make the best decision and record it in
  DECISIONS.md (date, decision, alternatives considered, reason).
- At the start of every session: run `git status` and `git branch --show-current`, read PLAN.md,
  then PROGRESS.md, DECISIONS.md and BLOCKERS.md if they exist. If you're on a task/* branch,
  finish that task; otherwise start the first unticked task.
- If an approach fails 3 times, write it up in BLOCKERS.md and move to a fallback or the next
  independent task. Don't loop on the same error.

## Skills: use them
Project skills live in .claude/skills/. Follow them for every change:
- git-task-workflow: branch per task, split into items, commit per item, merge to main.
- python-backend: controller → service → DAO → model/schema layering, pipeline layout.
- postgres: private local database on port 5544 via scripts/db.sh, Alembic, schema rules.
- react + tailwind + frontend-design: modular feature folders, Tailwind v4, good UI.
- docker-project-foundations, docker-compose-patterns, docker-build-strategies: Docker files.

## Git
- Every task: its own `task/<phase>-<slug>` branch, split into items, one commit per item,
  merged into main only after tests/lint pass, then the branch is deleted.
- `MERGE_MODE=pr`: push the task branch, open a pull request with `gh pr create`, merge it with
  `gh pr merge --merge --delete-branch`, then `git pull --ff-only` on main.
  `MERGE_MODE=local`: merge locally with `git merge --no-ff`. See the git-task-workflow skill.
- Push only task/* branches. Never push to main, never `--force`, never rewrite history.

## Your workspace
- You may freely create, edit and delete anything inside this project folder, except the
  protected setup files: .claude/ (including skills), CLAUDE.md, run-agent.sh, .env.
- Outside this folder you may read, download and edit, but never delete or move anything away.
  /tmp is fine for scratch.
- A guard hook enforces this. If a command is blocked, read the message and take another route.
- Start the local database with `scripts/db.sh start` when needed, and leave it running between
  tasks; run-agent.sh stops it at the end.

## Data integrity (most important)
- NEVER invent, guess or hard-code data values. Every number must come from a downloaded file
  or be computed from one. Never ship mock or placeholder data in the product.
- Never fill missing values silently. If you impute, add a flag and record the method in
  DECISIONS.md.
- Official homelessness counts exist only per CoC. The only tract-level homeless numbers allowed
  are the modelled estimates from PLAN.md Phase 5: they must sum to the CoC totals, carry the
  method and year, and be labelled "estimate" everywhere (data, API, UI, reports).
- Never show or store the location of individual homeless people, and never publish
  domestic-violence shelter locations.
- Treat data/raw/ as read-only once downloaded; write derived files elsewhere.
- DATA_SOURCES.md entry format, one per dataset:
  `name | URL | download date | licence/terms | geography | year(s) | file path | columns used`

## Modelling integrity
- The test split is only for the final evaluation. Never tune, select features or choose models
  using it.
- Report honest metrics, including when a target is missed. Never change a target or metric to
  make results look better.

## Engineering
- Python 3.12 via uv (`uv add`, `uv run`); Node via npm in frontend/. No global installs.
- Files in data/ stay out of git. Commit code, small outputs (<5 MB) and reports.
- Keep total data under 8 GB; delete data/interim files you no longer need.
- The Census API key is in the CENSUS_API_KEY environment variable. Never read, print or copy
  .env, and never write the key into any file, log or commit.

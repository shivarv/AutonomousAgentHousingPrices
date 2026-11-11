#!/usr/bin/env bash
# Starts the autonomous run. NOTHING runs until you execute this script yourself:
#
#     bash run-agent.sh              # 5 hours (default)
#     HOURS=3 bash run-agent.sh      # custom duration
#
# It runs Claude Code in repeated unattended sessions until one of these happens:
#   - STATUS contains DONE (project finished)
#   - the time budget runs out
#   - you create a file named STOP in this folder (kill switch: `touch STOP`)
# Usage limits: when hit, it waits 30 minutes and continues.

set -u
cd "$(dirname "$0")"

HOURS=${HOURS:-5}
END=$(( $(date +%s) + HOURS * 3600 ))
SESSION_MINUTES=${SESSION_MINUTES:-60}

# --- Pre-flight checks -------------------------------------------------------
[ -f .env ] && { set -a; . ./.env; set +a; }
if [ -z "${CENSUS_API_KEY:-}" ] || [ "$CENSUS_API_KEY" = "paste_your_key_here" ]; then
  echo "Put your Census API key in .env first (CENSUS_API_KEY=...)."; exit 1
fi
command -v claude >/dev/null || { echo "Claude Code isn't installed: npm install -g @anthropic-ai/claude-code"; exit 1; }
command -v uv >/dev/null || { echo "uv isn't installed: https://docs.astral.sh/uv/"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required for the guardrail hook."; exit 1; }
command -v npm >/dev/null || { echo "Node.js/npm is required for the frontend."; exit 1; }
[ -x /Library/PostgreSQL/18/bin/pg_ctl ] || { echo "PostgreSQL 18 binaries not found in /Library/PostgreSQL/18/bin."; exit 1; }

# Stop the agent's private database (if it started one) when the run ends.
cleanup() { [ -x scripts/db.sh ] && scripts/db.sh stop >/dev/null 2>&1; }
trap cleanup EXIT

# `timeout` is missing on macOS unless coreutils is installed (then it's `gtimeout`).
if command -v timeout >/dev/null; then LIMIT="timeout ${SESSION_MINUTES}m"
elif command -v gtimeout >/dev/null; then LIMIT="gtimeout ${SESSION_MINUTES}m"
else LIMIT=""; echo "Note: no timeout command; sessions are limited by --max-turns only."; fi

mkdir -p logs
rm -f STOP

if ! git rev-parse HEAD >/dev/null 2>&1; then
  git add -A && git commit -qm "Project setup: plan, rules and guardrails"
fi

# Merge mode: pull requests on GitHub when `gh` is logged in and `origin` exists, else local merges.
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1 && git remote get-url origin >/dev/null 2>&1; then
  export MERGE_MODE=pr
  # Pull requests need a main branch on GitHub. Publish it once if the remote has none.
  if ! git ls-remote --exit-code --heads origin main >/dev/null 2>&1; then
    echo "[$(date)] Publishing main to GitHub (first run)."
    git push -u origin main || { echo "Couldn't push main to origin. Fix GitHub access or log out of gh to use local mode."; exit 1; }
  fi
else
  export MERGE_MODE=local
fi
echo "[$(date)] Merge mode: $MERGE_MODE"

PROMPT='Read CLAUDE.md and PLAN.md, then PROGRESS.md, DECISIONS.md and BLOCKERS.md if they exist.
Check `git status` and the current branch first. If you are on a task/* branch, finish that task;
otherwise start the first unticked task in PLAN.md. Follow the project skills in .claude/skills,
especially git-task-workflow: one branch per task, split it into items, commit per item, and merge
into main only when tests and lint pass. Work through as many tasks as you can.
Never ask questions; decide and record the decision in DECISIONS.md.
When the Definition of done in PLAN.md is fully met, write DONE to the file STATUS on main.'

# --- Main loop ---------------------------------------------------------------
session=0
echo "[$(date)] Starting autonomous run for up to ${HOURS}h. Stop any time with: touch STOP"
while [ "$(date +%s)" -lt "$END" ]; do
  [ -f STOP ] && { echo "[$(date)] STOP file found. Exiting."; break; }
  grep -q DONE STATUS 2>/dev/null && { echo "[$(date)] Project complete."; break; }

  session=$((session + 1))
  log="logs/session-$(printf %03d "$session").log"
  echo "[$(date)] Session $session -> $log"

  $LIMIT claude -p "$PROMPT" \
    --permission-mode acceptEdits \
    --max-turns 150 \
    > "$log" 2>&1
  code=$?

  # Checkpoint whatever was done, even if the session stopped mid-task.
  git add -A && git commit -qm "Checkpoint after session $session" 2>/dev/null

  if grep -qiE "usage limit|rate limit|limit reached|limit will reset" "$log"; then
    echo "[$(date)] Usage limit reached. Waiting 30 minutes."
    sleep 1800
  elif [ "$code" -ne 0 ]; then
    echo "[$(date)] Session ended with exit code $code. Pausing 60 s."
    sleep 60
  else
    sleep 5
  fi
done
echo "[$(date)] Finished after $session session(s). Review: git log, PROGRESS.md, reports/"

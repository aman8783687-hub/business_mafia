#!/usr/bin/env bash
# One Mafia of Business run (local): makes exactly ONE episode and finalizes it into
# output/<slug>/. opencode is re-invoked (up to MAX_ATTEMPTS) until a NEW
# finalized episode is recorded; each retry receives the tail of the last attempt.
# Nothing is committed back to the repo.
set -u
cd "$(dirname "$0")/.."
mkdir -p .scratch
# State lives in MongoDB, not git: load it now, save it on any exit (success or failure).
python3 scripts/state_db.py pull || { echo "could not load state from MongoDB"; exit 1; }
trap 'python3 scripts/state_db.py push || echo "WARNING: could not save state to MongoDB"' EXIT
MAX_ATTEMPTS="${MAX_ATTEMPTS:-4}"
MODEL_ARGS=()
[ -n "${OPENCODE_MODEL:-}" ] && MODEL_ARGS=(-m "$OPENCODE_MODEL")
# Headless: never block on a question or a permission prompt.
export OPENCODE_PERMISSION='{"question":"deny","external_directory":{"**":"allow"}}'

finalized_count() {
  python3 - <<'PY'
import json, pathlib
n = 0
for f in pathlib.Path("episodes").glob("*/08_publish/finalize_log.json"):
    try:
        n += json.loads(f.read_text()).get("status") == "ok"
    except (OSError, ValueError, AttributeError):
        pass
print(n)
PY
}

before="$(finalized_count)"
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  prompt="$(cat cycle_prompt.md)"
  # GitHub Actions manual trigger: workflow_dispatch inputs arrive here
  # (CYCLE_EXTRA_PROMPT). Empty locally, so local ./make-video is unchanged.
  if [ -n "${CYCLE_EXTRA_PROMPT:-}" ]; then
    prompt="$prompt

$CYCLE_EXTRA_PROMPT"
  fi
  if [ "$attempt" -gt 1 ]; then
    prompt="$prompt

RETRY $attempt of $MAX_ATTEMPTS: the previous attempt ended before a NEW episode was finalized into output/. The tail of its output is below. Diagnose the actual cause and choose a different approach instead of repeating the failing command. If an episode is pending, resume it; otherwise start a new episode. Never backfill an old one.

$(tail -60 .scratch/last_attempt.log)"
  fi
  echo "=== attempt $attempt/$MAX_ATTEMPTS $(date -Is) ==="
  opencode run "${MODEL_ARGS[@]}" -- "$prompt" 2>&1 | tee .scratch/last_attempt.log
  pending="$(python3 scripts/pending_episodes.py)" && pending_rc=0 || pending_rc=1
  after="$(finalized_count)"
  if [ "$pending_rc" -eq 0 ] && [ "$after" -gt "$before" ]; then
    echo "=== episode finalized ($before -> $after) ==="
    exit 0
  fi
  echo "=== not done after attempt $attempt; pending: ${pending:-none, but no new finalized episode} ==="
  [ "$attempt" -lt "$MAX_ATTEMPTS" ] && sleep $((attempt * 60))
done
echo "=== gave up after $MAX_ATTEMPTS attempts ==="
exit 1

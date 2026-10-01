#!/usr/bin/env bash
# One scheduled RedHat Engineer run on GitHub Actions: makes exactly ONE episode and
# uploads it to Content Lab. opencode is re-invoked (up to MAX_ATTEMPTS) until
# a NEW upload is recorded; each retry receives the tail of the last attempt.
# Nothing is committed back to the repo.
# IMAGINE_ERROR_SLOT (set by the workflow's slot check) is marked done on success or charged one
# failure otherwise, so the next workflow_dispatch run knows whether to try again.
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

mark_slot() {
  [ -n "${IMAGINE_ERROR_SLOT:-}" ] || return 0
  python3 scripts/state_db.py "slot-$1" "$IMAGINE_ERROR_SLOT" || echo "WARNING: could not record slot-$1 for $IMAGINE_ERROR_SLOT"
}

uploaded_count() {
  python3 - <<'PY'
import json, pathlib
n = 0
for f in pathlib.Path("episodes").glob("*/08_publish/upload_log.json"):
    try:
        n += json.loads(f.read_text()).get("content_lab", {}).get("status") == "ok"
    except (OSError, ValueError, AttributeError):
        pass
print(n)
PY
}

before="$(uploaded_count)"
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  prompt="$(cat cycle_prompt.md)"
  if [ "$attempt" -gt 1 ]; then
    prompt="$prompt

RETRY $attempt of $MAX_ATTEMPTS: the previous attempt ended before a NEW episode was uploaded to Content Lab. The tail of its output is below. Diagnose the actual cause and choose a different approach instead of repeating the failing command. If an episode is pending, resume it; otherwise start a new episode. Never backfill an old one.

$(tail -60 .scratch/last_attempt.log)"
  fi
  echo "=== attempt $attempt/$MAX_ATTEMPTS $(date -Is) ==="
  opencode run "${MODEL_ARGS[@]}" -- "$prompt" 2>&1 | tee .scratch/last_attempt.log
  pending="$(python3 scripts/pending_episodes.py)" && pending_rc=0 || pending_rc=1
  after="$(uploaded_count)"
  if [ "$pending_rc" -eq 0 ] && [ "$after" -gt "$before" ]; then
    echo "=== episode uploaded to Content Lab ($before -> $after) ==="
    mark_slot done
    exit 0
  fi
  echo "=== not done after attempt $attempt; pending: ${pending:-none, but no new upload} ==="
  [ "$attempt" -lt "$MAX_ATTEMPTS" ] && sleep $((attempt * 60))
done
echo "=== gave up after $MAX_ATTEMPTS attempts ==="
mark_slot failed
exit 1

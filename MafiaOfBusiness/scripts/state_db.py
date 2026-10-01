"""Mafia of Business's MongoDB-backed state: topic bank, episode records,
and channel_state.json's live counters. There is
no topic_bank.json or committed episode state -- MongoDB is the only
copy. CLI:

    state_db.py pull                         -- load state from Mongo into local files
    state_db.py push                         -- save local files' state back to Mongo
    state_db.py recent [N]                   -- last N episode records
    state_db.py topics [queued|used|rejected] -- list topics by status
    state_db.py topics-count                 -- counts per status
    state_db.py topic-add                    -- add topic(s), JSON object or list on stdin
    state_db.py topic-use "<name>"           -- mark a queued topic used
    state_db.py topic-reject "<name>" "<why>" -- reject a queued topic
    state_db.py episode-posted <slug> <url>  -- mark a finalized episode as posted on YouTube
    state_db.py episode-abandon <slug> "<why>" -- retire an episode that cannot be finished
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pymongo

WORKSPACE = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
import env_loader  # noqa: E402
from state import STATE_PATH  # noqa: E402

TOPIC_STATUSES = ("queued", "used", "rejected")
EPISODE_TEXT_FILES = (
    "topic.json",
    "02_script/script.md",
    "02_script/shotlist.json",
    "03_audio/chunk_plan.json",
    "08_publish/metadata.json",
    "08_publish/finalize_log.json",
    "08_publish/abandoned.json",
)
CHANNEL_STATE_ID = "channel_state"
DEFAULT_DB_NAME = "mafia_of_business_pipeline"
IST = timezone(timedelta(hours=5, minutes=30))


def get_db():
    uri = env_loader.get("MONGODB_URI")
    db_name = env_loader.get("MONGODB_DB", DEFAULT_DB_NAME)
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]
    _seed_topics(db, WORKSPACE)
    return db


def _seed_topics(db, workspace: Path) -> None:
    if db.topics.count_documents({}) > 0:
        return
    seed_path = workspace / "seed" / "topic_bank.seed.json"
    if not seed_path.exists():
        return
    seed = json.loads(seed_path.read_text())
    topic_add(db, seed.get("queued", []))


def topics(db, status: str = "queued") -> list[dict]:
    assert status in TOPIC_STATUSES
    docs = db.topics.find({"status": status}).sort("order", 1)
    return [{"topic": d["_id"], **d["data"]} for d in docs]


def topics_count(db) -> dict:
    return {status: db.topics.count_documents({"status": status}) for status in TOPIC_STATUSES}


def _edge_order(db, status: str, lowest: bool) -> int:
    sort_dir = 1 if lowest else -1
    doc = db.topics.find({"status": status}).sort("order", sort_dir).limit(1)
    docs = list(doc)
    if not docs:
        return 0
    return docs[0]["order"] + (-1 if lowest else 1)


def topic_add(db, items: list[dict]) -> tuple[list[str], list[str]]:
    added, skipped = [], []
    for item in items:
        if "topic" not in item or "category" not in item:
            raise ValueError(f"topic item missing required 'topic'/'category' keys: {item!r}")
        name = item["topic"]
        if db.topics.find_one({"_id": name}):
            skipped.append(name)
            continue
        order = _edge_order(db, "queued", lowest=False)
        db.topics.insert_one({"_id": name, "status": "queued", "order": order, "data": item})
        added.append(name)
    return added, skipped


def _move_topic(db, name: str, status: str, extra: dict, lowest_first: bool = False) -> None:
    doc = db.topics.find_one({"_id": name})
    if not doc:
        raise ValueError(f"unknown topic: {name!r}")
    order = _edge_order(db, status, lowest=lowest_first)
    new_data = {**doc["data"], **extra}
    db.topics.update_one({"_id": name}, {"$set": {"status": status, "order": order, "data": new_data}})


def topic_use(db, name: str, date: str | None = None) -> None:
    date = date or datetime.now(IST).date().isoformat()
    _move_topic(db, name, "used", {"published": date})


def topic_reject(db, name: str, reason: str) -> None:
    _move_topic(db, name, "rejected", {"rejected_reason": reason})


def episode_ready(db, slug: str, doc: dict) -> None:
    db.episodes.update_one({"_id": slug}, {"$set": {"slug": slug, **doc}}, upsert=True)


def episode_posted(db, slug: str, url: str) -> None:
    db.episodes.update_one(
        {"_id": slug},
        {"$set": {"slug": slug, "status": "posted", "youtube_url": url,
                  "posted_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


def episode_abandon(db, slug: str, reason: str, workspace: Path = WORKSPACE) -> None:
    """Retire an episode that cannot be finished, so pending_episodes.py stops
    reporting it and `pull` stops restoring it. Writes a marker file (the
    local source of truth) and records the status in MongoDB."""
    ep_dir = workspace / "episodes" / slug
    now = datetime.now(timezone.utc).isoformat()
    if ep_dir.exists():
        marker = ep_dir / "08_publish" / "abandoned.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"reason": reason, "at": now}))
    db.episodes.update_one({"_id": slug}, {"$set": {"slug": slug, "status": "abandoned",
                                                    "abandoned_reason": reason, "abandoned_at": now}}, upsert=True)


def _episode_status(files: dict) -> tuple[str, str | None]:
    raw = files.get("08_publish/finalize_log.json")
    if raw:
        try:
            log = json.loads(raw)
            if log.get("status") == "ok":
                return "ready", log.get("output_dir")
        except json.JSONDecodeError:
            pass
    if files.get("08_publish/abandoned.json"):
        return "abandoned", None
    return "pending", None


def _push_episodes(db, workspace: Path) -> None:
    episodes_dir = workspace / "episodes"
    if not episodes_dir.exists():
        return
    for ep_dir in sorted(episodes_dir.iterdir()):
        if not ep_dir.is_dir():
            continue
        files = {}
        for rel in EPISODE_TEXT_FILES:
            p = ep_dir / rel
            if p.exists():
                files[rel] = p.read_text()
        if not files:
            continue
        status, output_dir = _episode_status(files)
        topic_raw = files.get("topic.json")
        topic = json.loads(topic_raw)["topic"] if topic_raw else None
        existing = db.episodes.find_one({"_id": ep_dir.name}) or {}
        if existing.get("status") in ("posted", "abandoned") and status == "pending":
            status = existing["status"]
        if existing.get("status") == "posted":
            status = "posted"
        db.episodes.update_one(
            {"_id": ep_dir.name},
            {"$set": {
                "slug": ep_dir.name, "topic": topic, "status": status, "output_dir": output_dir,
                "files": files, "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )


def _restore_unfinished_episodes(db, workspace: Path) -> None:
    episodes_dir = workspace / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    for doc in db.episodes.find({"status": "pending"}):
        ep_dir = episodes_dir / doc["slug"]
        for rel, content in doc.get("files", {}).items():
            path = ep_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


# Only these keys are live run state. Everything else in channel_state.json
# (voice, style, format, captions, ...) is config owned by git: a stale
# MongoDB copy must never overwrite it, or a rebrand would silently not ship.
LIVE_STATE_KEYS = ("counters", "baselines", "active_experiment")


def merge_live_state(config: dict, stored: dict) -> dict:
    merged = dict(config)
    for key in LIVE_STATE_KEYS:
        if key in stored:
            merged[key] = stored[key]
    return merged


def pull(db, workspace: Path = WORKSPACE) -> None:
    state_doc = db.state.find_one({"_id": CHANNEL_STATE_ID})
    if state_doc and STATE_PATH.exists():
        config = json.loads(STATE_PATH.read_text())
        STATE_PATH.write_text(json.dumps(merge_live_state(config, state_doc["data"]), indent=2))
    _restore_unfinished_episodes(db, workspace)


def push(db, workspace: Path = WORKSPACE) -> None:
    if STATE_PATH.exists():
        data = json.loads(STATE_PATH.read_text())
        db.state.update_one({"_id": CHANNEL_STATE_ID}, {"$set": {"data": data}}, upsert=True)
    _push_episodes(db, workspace)


def recent(db, n: int = 10) -> list[dict]:
    return list(db.episodes.find().sort("updated_at", -1).limit(n))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__, file=sys.stderr)
        return 1
    cmd, *rest = argv
    db = get_db()

    if cmd == "pull":
        pull(db)
    elif cmd == "push":
        push(db)
    elif cmd == "recent":
        n = int(rest[0]) if rest else 10
        for ep in recent(db, n):
            print(f"{ep['slug']}\t{ep['status']}\t{ep.get('youtube_url') or ep.get('output_dir') or ''}")
    elif cmd == "topics":
        status = rest[0] if rest else "queued"
        for t in topics(db, status):
            print(json.dumps(t))
    elif cmd == "topics-count":
        print(json.dumps(topics_count(db)))
    elif cmd == "topic-add":
        raw = json.loads(sys.stdin.read())
        items = raw if isinstance(raw, list) else [raw]
        added, skipped = topic_add(db, items)
        print(json.dumps({"added": added, "skipped": skipped}))
    elif cmd == "topic-use":
        topic_use(db, rest[0])
    elif cmd == "topic-reject":
        topic_reject(db, rest[0], rest[1])
    elif cmd == "episode-abandon":
        episode_abandon(db, rest[0], rest[1] if len(rest) > 1 else "no reason given")
    elif cmd == "episode-posted":
        episode_posted(db, rest[0], rest[1])
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

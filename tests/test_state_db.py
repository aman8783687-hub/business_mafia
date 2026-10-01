import pytest
import mongomock

import state_db


@pytest.fixture
def db():
    return mongomock.MongoClient()["test"]


def test_missing_uri_raises(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.setattr(state_db.env_loader, "load_env", lambda: {})
    with pytest.raises(RuntimeError):
        state_db.get_db()


def test_topic_add_requires_category_not_pillar(db):
    with pytest.raises(ValueError):
        state_db.topic_add(db, [{"topic": "The Vanishing Lighthouse Keeper"}])
    added, skipped = state_db.topic_add(
        db, [{"topic": "The Vanishing Lighthouse Keeper", "category": "Vanishings", "setting": "1920s Maine coast"}]
    )
    assert added == ["The Vanishing Lighthouse Keeper"]
    assert skipped == []


def test_topic_add_skips_duplicates(db):
    item = {"topic": "The Locked Room", "category": "Curses"}
    state_db.topic_add(db, [item])
    added, skipped = state_db.topic_add(db, [item])
    assert added == []
    assert skipped == ["The Locked Room"]


def test_topic_use_moves_to_used(db):
    state_db.topic_add(db, [{"topic": "The Empty Village", "category": "Ghost Stories"}])
    state_db.topic_use(db, "The Empty Village")
    assert [t["topic"] for t in state_db.topics(db, "used")] == ["The Empty Village"]
    assert state_db.topics(db, "queued") == []


def test_default_db_name_is_mafia_of_business(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost/ignored")
    assert state_db.DEFAULT_DB_NAME == "mafia_of_business_pipeline"


def test_pull_keeps_git_config_and_takes_only_live_state(db, tmp_path, monkeypatch):
    state_path = tmp_path / "channel_state.json"
    state_path.write_text('{"channel": {"name": "RedHat Engineer"}, "counters": {"episodes_published": 0}}')
    monkeypatch.setattr(state_db, "STATE_PATH", state_path)
    db.state.insert_one({"_id": "channel_state", "data": {
        "channel": {"name": "Imagine Error"},
        "counters": {"episodes_published": 5},
        "baselines": {"completion_rate_30d": 0.4},
    }})
    state_db.pull(db, tmp_path)
    merged = __import__("json").loads(state_path.read_text())
    assert merged["channel"]["name"] == "RedHat Engineer"
    assert merged["counters"]["episodes_published"] == 5
    assert merged["baselines"]["completion_rate_30d"] == 0.4
def test_episode_ready_then_posted(db):
    state_db.episode_ready(db, "2026-10-02-chai", {"title": "t", "status": "ready", "output_dir": "/o"})
    doc = db.episodes.find_one({"_id": "2026-10-02-chai"})
    assert doc["status"] == "ready" and doc["output_dir"] == "/o"
    state_db.episode_posted(db, "2026-10-02-chai", "https://youtu.be/x")
    doc = db.episodes.find_one({"_id": "2026-10-02-chai"})
    assert doc["status"] == "posted" and doc["youtube_url"] == "https://youtu.be/x"


def test_episode_status_reads_finalize_log():
    assert state_db._episode_status({}) == ("pending", None)
    files = {"08_publish/finalize_log.json": '{"status": "ok", "output_dir": "/o"}'}
    assert state_db._episode_status(files) == ("ready", "/o")


def test_push_does_not_downgrade_a_posted_episode(db, tmp_path, monkeypatch):
    monkeypatch.setattr(state_db, "STATE_PATH", tmp_path / "missing.json")
    ep = tmp_path / "episodes" / "e1" / "08_publish"
    ep.mkdir(parents=True)
    (ep / "finalize_log.json").write_text('{"status": "ok", "output_dir": "/o"}')
    state_db.episode_posted(db, "e1", "https://youtu.be/x")
    state_db.push(db, tmp_path)
    assert db.episodes.find_one({"_id": "e1"})["status"] == "posted"


def test_no_slot_commands_remain():
    assert not hasattr(state_db, "slot_check")


def test_abandon_retires_a_pending_episode_everywhere(db, tmp_path, monkeypatch):
    monkeypatch.setattr(state_db, "STATE_PATH", tmp_path / "missing.json")
    ep = tmp_path / "episodes" / "e9"
    (ep / "02_script").mkdir(parents=True)
    (ep / "02_script" / "script.md").write_text("[HOOK]\n1. x\n")
    state_db.push(db, tmp_path)
    assert db.episodes.find_one({"_id": "e9"})["status"] == "pending"
    state_db.episode_abandon(db, "e9", "topic rejected", tmp_path)
    assert (ep / "08_publish" / "abandoned.json").exists()
    assert db.episodes.find_one({"_id": "e9"})["status"] == "abandoned"
    state_db.push(db, tmp_path)  # a later push must not resurrect it as pending
    assert db.episodes.find_one({"_id": "e9"})["status"] == "abandoned"
    import pending_episodes
    assert pending_episodes.find_pending(tmp_path / "episodes") == []


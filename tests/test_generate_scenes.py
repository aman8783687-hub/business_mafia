import json

import generate_scenes


def test_parse_beats_arg():
    assert generate_scenes.parse_beats_arg(None) is None
    assert generate_scenes.parse_beats_arg("1,3,5-7") == {1, 3, 5, 6, 7}


def test_standalone_run_copies_shotlist_forward_from_script_dir(tmp_path, monkeypatch):
    # Regression test: generate_scenes.py used to hard-require
    # 05_scenes/shotlist.json, which is only ever created by
    # run_episode.py's own copy-forward step. Running generate_scenes.py
    # standalone (as the docs' manual review step instructs) before
    # run_episode.py must not fail -- it should copy the authored
    # 02_script/shotlist.json forward itself.
    episode_dir = tmp_path / "episodes" / "ep-1"
    (episode_dir / "03_audio").mkdir(parents=True)
    (episode_dir / "02_script").mkdir(parents=True)
    (episode_dir / "03_audio" / "timings.json").write_text(json.dumps({
        "beats": [{"beat": 1, "text": "a foggy dock"}]
    }))
    (episode_dir / "02_script" / "shotlist.json").write_text(json.dumps([
        {"scene": 1, "description": "a foggy dock at night", "motion": "slow push in"},
    ]))
    # No 05_scenes/shotlist.json written -- that's the point of this test.
    monkeypatch.setattr(generate_scenes, "WORKSPACE", tmp_path)

    def boom(*a, **k):
        raise AssertionError("the image backend must not be called on --dry-run")
    monkeypatch.setattr(generate_scenes, "generate_episode_scenes", boom)

    rc = generate_scenes.main(["ep-1", "--dry-run"])
    assert rc == 0
    copied = episode_dir / "05_scenes" / "shotlist.json"
    assert copied.exists()
    assert json.loads(copied.read_text())[0]["scene"] == 1


def test_standalone_run_errors_clearly_when_neither_shotlist_exists(tmp_path, monkeypatch):
    episode_dir = tmp_path / "episodes" / "ep-1"
    (episode_dir / "03_audio").mkdir(parents=True)
    (episode_dir / "02_script").mkdir(parents=True)
    (episode_dir / "03_audio" / "timings.json").write_text(json.dumps({"beats": []}))
    monkeypatch.setattr(generate_scenes, "WORKSPACE", tmp_path)

    rc = generate_scenes.main(["ep-1", "--dry-run"])
    assert rc == 1


def test_dry_run_writes_prompt_plan_without_calling_the_backend(tmp_path, monkeypatch):
    episode_dir = tmp_path / "episodes" / "ep-1"
    (episode_dir / "03_audio").mkdir(parents=True)
    (episode_dir / "05_scenes").mkdir(parents=True)
    (episode_dir / "03_audio" / "timings.json").write_text(json.dumps({
        "beats": [{"beat": 1, "text": "a foggy dock"}, {"beat": 2, "text": "a locked door"}]
    }))
    (episode_dir / "05_scenes" / "shotlist.json").write_text(json.dumps([
        {"scene": 1, "description": "a foggy dock at night", "motion": "slow push in"},
        {"scene": 2, "description": "a locked wooden door", "motion": "slow push out"},
    ]))
    monkeypatch.setattr(generate_scenes, "WORKSPACE", tmp_path)

    def boom(*a, **k):
        raise AssertionError("the image backend must not be called on --dry-run")
    monkeypatch.setattr(generate_scenes, "generate_episode_scenes", boom)

    rc = generate_scenes.main(["ep-1", "--dry-run"])
    assert rc == 0
    plan = json.loads((episode_dir / "05_scenes" / "prompt_plan.json").read_text())
    assert len(plan) == 2
    assert plan[0]["beat"] == 1


def test_backend_defaults_to_perchance_and_can_be_switched(monkeypatch):
    from scenes import cloudflare_orchestrator, flux_orchestrator, perchance_orchestrator

    calls = []
    monkeypatch.setattr(perchance_orchestrator, "generate_episode_scenes",
                        lambda *a: calls.append("perchance") or ([1], []))
    monkeypatch.setattr(flux_orchestrator, "generate_episode_scenes",
                        lambda *a: calls.append("flux") or ([1], []))
    monkeypatch.setattr(cloudflare_orchestrator, "generate_episode_scenes",
                        lambda *a: calls.append("cloudflare") or ([1], []))

    monkeypatch.setattr(generate_scenes.env_loader, "load_env", lambda: {})
    monkeypatch.delenv("IMAGE_BACKEND", raising=False)
    assert generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1]) == ([1], [])
    monkeypatch.setenv("IMAGE_BACKEND", "")
    generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1])
    monkeypatch.setenv("IMAGE_BACKEND", "flux")
    generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1])
    monkeypatch.setenv("IMAGE_BACKEND", "cloudflare")
    generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1])
    assert calls == ["perchance", "perchance", "flux", "cloudflare"]

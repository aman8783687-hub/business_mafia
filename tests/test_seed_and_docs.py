import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WS = ROOT / "MafiaOfBusiness"
SKILL = ROOT / ".claude" / "skills" / "mafia-of-business-youtube"


def test_seed_has_30_complete_topics_across_categories():
    queued = json.loads((WS / "seed" / "topic_bank.seed.json").read_text())["queued"]
    assert len(queued) >= 30
    for t in queued:
        for key in ("topic", "category", "setting", "myth", "angle", "visual_hooks", "score", "keywords"):
            assert key in t, (t.get("topic"), key)
        assert 3 <= len(t["keywords"]) <= 5
    assert len({t["category"] for t in queued}) >= 6
    # abstract/distant topics flopped for comparable channels (spec 4.1)
    for flop in ("आईपीएल", "यूपीआई", "कोचिंग", "ट्रेन"):
        assert not any(flop in t["topic"] for t in queued), flop
    assert len({t["topic"] for t in queued}) == len(queued)


def test_docs_reference_current_pipeline_only():
    texts = [p.read_text() for p in [*SKILL.rglob("*.md"), WS / "cycle_prompt.md", ROOT / "AGENTS.md", ROOT / "README.md"]]
    blob = "\n".join(texts)
    for stale in ("Content Lab", "content_lab", "upload_log", "publish_all", "RedHat", "red fedora",
                  "COLD_OPEN", "RISING_MYSTERY", "CLIMAX_REVEAL", "en-US-Ava", "slot-check"):
        assert stale not in blob, stale
    for needed in ("[HOOK]", "[RAAZ]", "finalize_log.json", "output/", "hi-IN-MadhurNeural", "check_script.py",
                   "thumbnail_scene", "आपके सवाल", "playlist", "मान लीजिए"):
        assert needed in blob, needed


def test_skill_frontmatter_names_the_channel():
    head = (SKILL / "SKILL.md").read_text().split("---")[1]
    assert re.search(r"^name: mafia-of-business-youtube$", head, re.M)
    assert "Business Mafia" in head

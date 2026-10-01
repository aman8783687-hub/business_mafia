from subtitles import segment, ass_builder


def test_segment_phrases_breaks_on_gap():
    words = [
        {"text": "The", "start": 0.0, "end": 0.2}, {"text": "keeper", "start": 0.2, "end": 0.6},
        {"text": "vanished.", "start": 0.6, "end": 1.0},
        {"text": "It", "start": 1.5, "end": 1.7}, {"text": "was", "start": 1.7, "end": 1.9},
    ]
    phrases = segment.segment_phrases(words, max_words=5, min_words=2, max_gap_seconds=0.2)
    assert len(phrases) == 2
    assert [w["text"] for w in phrases[0]] == ["The", "keeper", "vanished."]


def test_segment_phrases_breaks_on_max_words():
    words = [{"text": str(i), "start": i * 0.3, "end": i * 0.3 + 0.2} for i in range(7)]
    phrases = segment.segment_phrases(words, max_words=3, min_words=1, max_gap_seconds=1.0)
    assert all(len(p) <= 3 for p in phrases)


def test_build_ass_contains_style_and_dialogue():
    phrases = [[{"text": "The", "start": 0.0, "end": 0.3}, {"text": "keeper", "start": 0.3, "end": 0.8}]]
    config = {
        "title": "Mafia of Business animated captions",
        "font_family": "DejaVu Sans", "font_size": 50, "bold": True,
        "primary_color_ass": "&H00FFFFFF", "outline_color_ass": "&H00000000",
        "highlight_color_ass": "&H00F65C8B", "outline_width": 3.0, "shadow_depth": 1.2,
        "alignment": 2, "margin_v_ratio": 0.12, "safe_margin_side_px": 80,
        "pop_scale_percent": 115, "pop_duration_ms": 120, "settle_duration_ms": 100,
    }
    ass = ass_builder.build_ass(phrases, config, 1920, 1080)
    assert "PlayResX: 1920" in ass
    assert "PlayResY: 1080" in ass
    assert "Style: Caption" in ass
    assert "Dialogue:" in ass
    assert "Title: Mafia of Business animated captions" in ass


HINDI_CONFIG = {
    "title": "Mafia of Business animated captions",
    "font_family": "Noto Sans Devanagari", "font_size": 58, "bold": True, "uppercase": False,
    "max_chars_per_line": 22,
    "primary_color_ass": "&H00FFFFFF", "outline_color_ass": "&H00000000",
    "highlight_color_ass": "&H0017A0D4", "outline_width": 3.5, "shadow_depth": 1.2,
    "alignment": 2, "margin_v_ratio": 0.12, "safe_margin_side_px": 80,
    "pop_scale_percent": 115, "pop_duration_ms": 120, "settle_duration_ms": 100,
}


def _hindi_words():
    texts = ["एक", "कप", "चाय", "दस", "रुपये", "की।", "मुनाफ़ा", "कितना?"]
    return [{"text": t, "start": i * 0.3, "end": i * 0.3 + 0.25} for i, t in enumerate(texts)]


def test_devanagari_phrases_never_split_a_word():
    phrases = segment.segment_phrases(_hindi_words(), max_words=4, min_words=2, max_gap_seconds=0.2)
    flat = [w["text"] for p in phrases for w in p]
    assert flat == [w["text"] for w in _hindi_words()]
    assert all(len(p) <= 4 for p in phrases)


def test_devanagari_ass_keeps_text_and_font_and_drops_danda():
    phrases = segment.segment_phrases(_hindi_words(), max_words=4, min_words=2, max_gap_seconds=0.2)
    ass = ass_builder.build_ass(phrases, HINDI_CONFIG, 1920, 1080)
    assert "Style: Caption,Noto Sans Devanagari,58" in ass
    assert "मुनाफ़ा" in ass and "रुपये" in ass
    assert "।" not in ass
    assert "\\c&H0017A0D4" in ass

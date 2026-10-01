"""Builds an ASS (Advanced SubStation Alpha) subtitle file with
TikTok/Reels-style animated captions: short phrases, a highlight that
moves word-by-word in sync with speech, and a small scale "pop" on the
word that just became active. Burned in later via ffmpeg's libass
`subtitles` filter (see assemble_episode.py).

Why ASS instead of plain SRT/drawtext: SRT has no styling or animation
at all, and building the same per-word pop/highlight effect out of
ffmpeg drawtext filter chains directly would mean one drawtext node per
word transition with hand-rolled enable-time expressions -- ASS's
override-tag system (`\\t` transforms, `\\c` color runs, `{\\r}` resets)
does exactly this natively, and libass (linked into ffmpeg on this
machine) renders it in one pass. This is the same general technique
most existing open-source "auto-caption" tools use.

Each phrase becomes N Dialogue events (N = words in that phrase), one
per word's on-screen time slice, all showing the FULL phrase text so
the highlight appears to move across otherwise-static text rather than
words popping in one at a time.
"""
from __future__ import annotations

from .segment import phrase_span


def _fmt_ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _split_lines(words: list[dict], max_chars: int) -> list[list[dict]]:
    """If the phrase is wide, break it into two roughly-even lines at a
    word boundary. Keeping this simple (at most 2 lines) matches the
    brand's short-phrase captions -- these are 2-5 words, not paragraphs."""
    full_len = sum(len(w["text"]) + 1 for w in words) - 1
    if full_len <= max_chars or len(words) < 2:
        return [words]
    best_split, best_diff = 1, None
    running = 0
    for i, w in enumerate(words[:-1]):
        running += len(w["text"]) + 1
        diff = abs(running - full_len / 2)
        if best_diff is None or diff < best_diff:
            best_diff, best_split = diff, i + 1
    return [words[:best_split], words[best_split:]]


def build_ass(phrases: list[list[dict]], config: dict, width: int, height: int) -> str:
    uppercase = config.get("uppercase", True)
    max_chars_per_line = config.get("max_chars_per_line", 20)
    margin_v_px = round(config["margin_v_ratio"] * height)
    bold_flag = -1 if config.get("bold", True) else 0
    pop_scale = config.get("pop_scale_percent", 118)
    pop_ms = config.get("pop_duration_ms", 120)
    settle_ms = config.get("settle_duration_ms", 100)

    header = f"""[Script Info]
Title: {config.get('title', 'animated captions')}
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{config['font_family']},{config['font_size']},{config['primary_color_ass']},{config['primary_color_ass']},{config['outline_color_ass']},&H00000000,{bold_flag},0,0,0,100,100,0,0,1,{config['outline_width']},{config['shadow_depth']},{config['alignment']},{config['safe_margin_side_px']},{config['safe_margin_side_px']},{margin_v_px},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]

    for phrase in phrases:
        line_groups = _split_lines(phrase, max_chars_per_line)
        _, phrase_end = phrase_span(phrase)
        # Event boundaries: each word's own start, ending at the next
        # word's start (continuous coverage, no flicker between words),
        # last word's event ends at the phrase's own end.
        starts = [w["start"] for w in phrase]
        ends = starts[1:] + [phrase_end]

        for active_idx in range(len(phrase)):
            ev_start, ev_end = starts[active_idx], ends[active_idx]
            if ev_end <= ev_start:
                continue
            line_texts = []
            word_cursor = 0
            for group in line_groups:
                runs = []
                for w in group:
                    shown = w["text"].replace("।", "").strip() or w["text"]
                    display = _escape(shown.upper() if uppercase else shown)
                    if word_cursor == active_idx:
                        runs.append(
                            f"{{\\t(0,{pop_ms},\\fscx{pop_scale}\\fscy{pop_scale})"
                            f"\\t({pop_ms},{pop_ms + settle_ms},\\fscx100\\fscy100)"
                            f"\\c{config['highlight_color_ass']}}}{display}{{\\r}}"
                        )
                    else:
                        runs.append(display)
                    word_cursor += 1
                line_texts.append(" ".join(runs))
            text = "\\N".join(line_texts)
            lines.append(
                f"Dialogue: 0,{_fmt_ts(ev_start)},{_fmt_ts(ev_end)},Caption,,0,0,0,,{text}\n"
            )

    return "".join(lines)

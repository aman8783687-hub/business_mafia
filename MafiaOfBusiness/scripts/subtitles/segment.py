"""Group a flat list of timed words into short on-screen phrases (2-5
words, TikTok/Reels-style), from word_timings.json's absolute-time word
list. See references/captions.md for why phrase length is capped this
low instead of showing a full sentence at once.
"""
from __future__ import annotations


def segment_phrases(
    words: list[dict], max_words: int, min_words: int, max_gap_seconds: float = 0.2
) -> list[list[dict]]:
    """Greedy left-to-right grouping, breaking a phrase whenever EITHER
    it hits max_words OR there's a natural pause (gap between this word's
    start and the previous word's end) longer than max_gap_seconds.

    The gap check matters more than word count: without it, a phrase can
    span a real silence -- e.g. the ~0.4s gap stitch_audio.py inserts
    between script sections -- gluing the tail of one sentence to the
    start of an unrelated one into a single on-screen caption. min_words
    is a soft target, not enforced against a gap break: a short trailing
    phrase caused by a real pause is correct, not a defect to merge away.
    """
    phrases: list[list[dict]] = []
    current: list[dict] = []
    for w in words:
        if current:
            gap = w["start"] - current[-1]["end"]
            if gap > max_gap_seconds or len(current) >= max_words:
                phrases.append(current)
                current = []
        current.append(w)
    if current:
        phrases.append(current)
    return phrases


def phrase_span(phrase: list[dict]) -> tuple[float, float]:
    return phrase[0]["start"], phrase[-1]["end"]

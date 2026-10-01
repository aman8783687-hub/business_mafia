#!/usr/bin/env python3
"""
Locked Mafia of Business thumbnail template (spec 5.5): a "hisaab"
infographic on a white whiteboard -- title band on top ("पेट्रोल पंप का
हिसाब", accent word in gold, gold underline), the episode's scene in the
centre, 3-4 money annotations left and right with gold arrows pointing in,
gold frame. Black/white/gold only.

Usage:
    python3 make_thumbnail.py "पेट्रोल पंप का हिसाब" --accent-word हिसाब \
        --annotation "₹4.5/लीटर" --annotation "लोन ईएमआई" \
        --scene .../05_scenes/scene_0001.png --out .../08_publish/thumbnail.png

Without --annotation: the scene full-bleed with the title on it. Without a
scene: the boss stickman on the left, title on the right.
"""
import argparse
import math
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import load_state  # noqa: E402

HOST_IMAGE = ROOT / "brand" / "host" / "host-reference-clean.jpeg"
_T = load_state()["thumbnail"]
FONT_BOLD = _T["font_path"]

CANVAS_W, CANVAS_H = 1280, 720
ACCENT = tuple(_T["accent_rgb"])
FRAME = tuple(_T["frame_rgb"])
TEXT = tuple(_T["text_rgb"])
OUTLINE = tuple(_T["outline_rgb"])
WHITE = (255, 255, 255)
_TRAILING = ":,.?!।"
_METRIC = "कHg"  # Devanagari headline + matras are taller than Latin "Hg"

# Annotated layout geometry.
TITLE_BOX = (50, 24, CANVAS_W - 50, 150)          # x0, y0, x1, y1
SCENE_BOX = (340, 175, CANVAS_W - 340, CANVAS_H - 30)
LABEL_MAX_W = 290
# (label anchor, arrow target); left labels anchor on their left edge, right on their right edge.
ANNOTATION_SLOTS = [
    ((40, 230), (SCENE_BOX[0] + 30, 330)),
    ((CANVAS_W - 40, 230), (SCENE_BOX[2] - 30, 330)),
    ((40, 500), (SCENE_BOX[0] + 30, 520)),
    ((CANVAS_W - 40, 500), (SCENE_BOX[2] - 30, 520)),
]


def is_accent(word, accent_word):
    if not accent_word:
        return False
    return word.rstrip(_TRAILING) == accent_word.rstrip(_TRAILING)


def load_host_cutout():
    """Crop the host figure tightly out of its white-background reference."""
    im = Image.open(HOST_IMAGE).convert("RGB")
    bbox = im.convert("L").point(lambda p: 0 if p > 245 else 255).getbbox()
    if bbox:
        pad = 20
        l, t, r, b = bbox
        im = im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))
    return im


def _line_h(font):
    box = font.getbbox(_METRIC)
    return box[3] - box[1]


def wrap_words(words, font, max_width, draw):
    """Greedy wrap into as many lines as needed - caller decides what counts as fitting."""
    lines, current = [], []
    for w in words:
        trial = current + [w]
        if draw.textlength(" ".join(trial), font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def fit_font(draw, words, max_width, max_height, font_path, start_size=140, min_size=32):
    """Largest size where the wrapped title fits the box in at most 2 lines;
    raises rather than silently dropping words."""
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        lines = wrap_words(words, font, max_width, draw)
        if len(lines) <= 2:
            total_h = _line_h(font) * len(lines) * 1.25
            widest = max(draw.textlength(line, font=font) for line in lines)
            if total_h <= max_height and widest <= max_width:
                return font, lines
        size -= 4
    raise SystemExit(f"Title '{' '.join(words)}' doesn't fit the template even at {min_size}px -- shorten it.")


def _draw_title(draw, lines, font, x0, y, step, accent_word, fill=None, stroke=10, center_width=None):
    """Draw the title; return the lowest drawn pixel row (matras below the
    line included), so anything placed under it never cuts through them."""
    bottom = y
    for line in lines:
        x = x0
        if center_width:
            x = x0 + (center_width - draw.textlength(line, font=font)) / 2
        bottom = max(bottom, draw.textbbox((x, y), line, font=font, stroke_width=stroke)[3])
        for w in line.split():
            color = ACCENT if is_accent(w, accent_word) else (fill or TEXT)
            draw.text((x, y), w, font=font, fill=color, stroke_width=stroke, stroke_fill=OUTLINE if fill is None else WHITE)
            x += draw.textlength(w + " ", font=font)
        y += step
    return bottom


def check_no_latin(texts):
    """Noto Sans Devanagari has no Latin letters (they render as boxes);
    digits, ₹ and punctuation are fine."""
    bad = [t for t in texts if re.search(r"[A-Za-z]", t)]
    if bad:
        raise SystemExit(f"Thumbnail text must be Devanagari (digits and ₹ are fine), "
                         f"e.g. EMI -> ईएमआई: {bad}")


def _arrow(draw, start, end, color, width=7, head=24):
    draw.line([start, end], fill=color, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    for d in (2.6, -2.6):
        draw.line([end, (end[0] + head * math.cos(ang + d), end[1] + head * math.sin(ang + d))], fill=color, width=width)


def _label_font(draw, text):
    for size in range(48, 26, -2):
        font = ImageFont.truetype(FONT_BOLD, size)
        if draw.textlength(text, font=font) <= LABEL_MAX_W:
            return font
    return ImageFont.truetype(FONT_BOLD, 26)


def _fit_into(img, box):
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)))
    return img, (x0 + (x1 - x0 - img.width) // 2, y0 + (y1 - y0 - img.height) // 2)


def render_annotated_thumbnail(words, accent_word, annotations, scene_path):
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), WHITE)
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = TITLE_BOX
    font, lines = fit_font(draw, words, x1 - x0, y1 - y0, FONT_BOLD, start_size=110, min_size=40)
    step = int(_line_h(font) * 1.2)
    bottom = _draw_title(draw, lines, font, x0, y0, step, accent_word, fill=OUTLINE, stroke=0, center_width=x1 - x0)
    draw.rectangle([CANVAS_W // 2 - 260, bottom + 8, CANVAS_W // 2 + 260, bottom + 16], fill=ACCENT)

    art = Image.open(scene_path).convert("RGB") if scene_path and Path(scene_path).exists() else load_host_cutout()
    art, pos = _fit_into(art, SCENE_BOX)
    canvas.paste(art, pos)

    for text, ((ax, ay), target) in zip(annotations[:4], ANNOTATION_SLOTS):
        lfont = _label_font(draw, text)
        w = draw.textlength(text, font=lfont)
        left_side = ax < CANVAS_W / 2
        x = ax if left_side else ax - w
        draw.text((x, ay), text, font=lfont, fill=OUTLINE, stroke_width=3, stroke_fill=WHITE)
        start = (x + w + 10, ay + _line_h(lfont) // 2 + 10) if left_side else (x - 10, ay + _line_h(lfont) // 2 + 10)
        _arrow(draw, start, target, ACCENT)

    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=FRAME, width=14)
    return canvas


def render_scene_thumbnail(words, accent_word, scene_path):
    """Fallback without annotations: scene full-bleed, big white outlined title."""
    canvas = Image.open(scene_path).convert("RGB")
    scale = max(CANVAS_W / canvas.width, CANVAS_H / canvas.height)
    canvas = canvas.resize((int(canvas.width * scale) + 1, int(canvas.height * scale) + 1))
    left, top = (canvas.width - CANVAS_W) // 2, (canvas.height - CANVAS_H) // 2
    canvas = canvas.crop((left, top, left + CANVAS_W, top + CANVAS_H))
    draw = ImageDraw.Draw(canvas)
    margin = 50
    font, lines = fit_font(draw, words, int(CANVAS_W * 0.62), CANVAS_H - 2 * margin, FONT_BOLD, start_size=190)
    step = int(_line_h(font) * 1.25)
    _draw_title(draw, lines, font, margin, (CANVAS_H - step * len(lines)) // 2, step, accent_word)
    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=FRAME, width=14)
    return canvas


def render_host_thumbnail(words, accent_word):
    """Fallback without a scene: boss on the left (on its white card), title on the right, on black."""
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (17, 17, 17))
    draw = ImageDraw.Draw(canvas)
    left_w = int(CANVAS_W * 0.42)
    host, pos = _fit_into(load_host_cutout(), (30, 30, left_w - 30, CANVAS_H))
    canvas.paste(host, pos)
    draw.rectangle([left_w, 0, left_w + 6, CANVAS_H], fill=FRAME)
    text_x0 = left_w + 50
    font, lines = fit_font(draw, words, CANVAS_W - text_x0 - 50, CANVAS_H - 120, FONT_BOLD)
    step = int(_line_h(font) * 1.25)
    _draw_title(draw, lines, font, text_x0, (CANVAS_H - step * len(lines)) // 2, step, accent_word)
    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=FRAME, width=14)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="2-4 Devanagari words, e.g. 'पेट्रोल पंप का हिसाब'")
    ap.add_argument("--accent-word", default=None, help="One word from the title to draw in gold")
    ap.add_argument("--annotation", action="append", default=[], help="A money note with an arrow (max 4)")
    ap.add_argument("--scene", default=None, help="Path to a generated scene PNG")
    ap.add_argument("--out", default=str(ROOT / "brand" / "thumbnail-template-preview.png"))
    args = ap.parse_args()

    words = args.title.split()
    if len(words) > 4:
        raise SystemExit(f"Title has {len(words)} words; the locked template allows at most 4.")
    check_no_latin([args.title, *args.annotation])
    scene = args.scene if args.scene and Path(args.scene).exists() else None
    if args.annotation:
        canvas = render_annotated_thumbnail(words, args.accent_word, args.annotation, scene)
    elif scene:
        canvas = render_scene_thumbnail(words, args.accent_word, scene)
    else:
        canvas = render_host_thumbnail(words, args.accent_word)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"Saved {out_path} ({CANVAS_W}x{CANVAS_H})")
    small = canvas.resize((210, 118), Image.LANCZOS)
    small_path = out_path.with_name(out_path.stem + "-210x118-preview.png")
    small.save(small_path)
    print(f"Saved legibility check {small_path}")


if __name__ == "__main__":
    main()

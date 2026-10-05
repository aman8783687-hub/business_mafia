#!/usr/bin/env python3
"""
Locked Business Mafia thumbnail template, modelled on the operator's
hand-made petrol pump thumbnail (the best-clicked packaging so far): the
question title in two brush-stroke bands on the left -- line 1 white on a
black band, line 2 black on a yellow band, tilted slightly -- and the
thumbnail scene (boss on the right, curious, at the business, money in
front) filling the frame. An optional green badge carries one rupee figure.
Brightened after the Growth Mitra analysis (2026-10-04): rupee figures and
digits in the title are highlighted (yellow on the black band, green on the
yellow band) and a green growth arrow sits in the top-right corner.

Usage:
    python3 make_thumbnail.py "डंपर वाला | कितना कमाता है?" \
        --badge "₹3,000/फेरा" \
        --scene .../08_publish/thumbnail_scene.png --out .../08_publish/thumbnail.png

The title is one or two lines separated by "|", at most 4 words per line:
"<X> वाला | कितना कमाता है?" (deep dive) or "₹10,000 से शुरू | ये 7 बिज़नेस" (listicle).
Without a scene the boss reference is placed on the right.
"""
import argparse
import random
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
ACCENT = tuple(_T["accent_rgb"])      # gold
BADGE = tuple(_T["badge_rgb"])        # green: badge
BADGE_TEXT = tuple(_T["badge_text_rgb"])
ARROW = tuple(_T["arrow_rgb"])        # green: growth arrow
NUMBER_ON_INK = tuple(_T["number_on_ink_rgb"])    # rupee figures on the black band
NUMBER_ON_BAND = tuple(_T["number_on_band_rgb"])  # rupee figures on the yellow band
BAND = tuple(_T["band_rgb"])          # yellow: second title band
INK = tuple(_T["outline_rgb"])        # near-black: first band, text on yellow
WHITE = (255, 255, 255)
_METRIC = "कHg"  # Devanagari headline + matras are taller than Latin "Hg"

TEXT_X, TEXT_Y = 34, 46
TEXT_MAX_W = 760          # the left ~60%: the scene keeps the right side
TILT_DEGREES = 3
BAND_PAD_X, BAND_PAD_Y = 26, 14


def split_title(title: str) -> list[str]:
    lines = [" ".join(part.split()) for part in title.split("|")]
    lines = [line for line in lines if line]
    if not 1 <= len(lines) <= 2:
        raise SystemExit(f"Thumbnail title needs 1-2 lines separated by '|': {title!r}")
    for line in lines:
        if len(line.split()) > 4:
            raise SystemExit(f"Thumbnail line '{line}' has {len(line.split())} words; at most 4 per line.")
    return lines


def check_no_latin(texts):
    """Noto Sans Devanagari has no Latin letters (they render as boxes);
    digits, ₹ and punctuation are fine."""
    bad = [t for t in texts if re.search(r"[A-Za-z]", t)]
    if bad:
        raise SystemExit(f"Thumbnail text must be Devanagari (digits and ₹ are fine), "
                         f"e.g. EMI -> ईएमआई: {bad}")


_NUMBER_RE = re.compile(r"[0-9₹]")


def _draw_line(draw, xy, line, font, ink, number_ink):
    """Draw word by word so words with a digit or ₹ get number_ink."""
    x, y = xy
    words = line.split(" ")
    for i, word in enumerate(words):
        offset = draw.textlength(" ".join(words[:i]) + (" " if i else ""), font=font)
        draw.text((x + offset, y), word, font=font, fill=number_ink if _NUMBER_RE.search(word) else ink)


def _line_h(font):
    box = font.getbbox(_METRIC)
    return box[3] - box[1]


def fit_line_font(draw, lines, max_width, start_size=150, min_size=48):
    """One size for both lines: the largest where the widest line fits."""
    for size in range(start_size, min_size - 1, -4):
        font = ImageFont.truetype(FONT_BOLD, size)
        if max(draw.textlength(line, font=font) for line in lines) <= max_width:
            return font
    raise SystemExit(f"Thumbnail title {lines} doesn't fit even at {min_size}px -- shorten it.")


def _brush_band(draw, box, color, rng):
    """A marker-stroke band: ragged top and bottom edges, frayed ends."""
    x0, y0, x1, y1 = box
    step = 22
    top = [(x, y0 + rng.randint(-5, 5)) for x in range(int(x0), int(x1), step)] + [(x1, y0 + rng.randint(-5, 5))]
    bottom = [(x, y1 + rng.randint(-5, 5)) for x in range(int(x1), int(x0), -step)] + [(x0, y1 + rng.randint(-5, 5))]
    draw.polygon(top + bottom, fill=color)
    height = y1 - y0
    for _ in range(7):  # frayed bristle streaks past both ends
        y = rng.uniform(y0 + 4, y1 - 4)
        thick = rng.randint(3, max(4, int(height / 9)))
        draw.line([(x0 - rng.randint(8, 34), y), (x0 + 30, y)], fill=color, width=thick)
        draw.line([(x1 - 30, y), (x1 + rng.randint(8, 34), y)], fill=color, width=thick)


def render_title_layer(lines):
    """The two-band title on a transparent layer, already tilted."""
    layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = fit_line_font(draw, lines, TEXT_MAX_W - 2 * BAND_PAD_X)
    rng = random.Random(" ".join(lines))
    styles = ([(INK, WHITE, NUMBER_ON_INK), (BAND, INK, NUMBER_ON_BAND)] if len(lines) == 2
              else [(BAND, INK, NUMBER_ON_BAND)])
    y = TEXT_Y
    for line, (band, ink, number_ink) in zip(lines, styles):
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        w, h = right - left, max(bottom - top, _line_h(font))
        x = TEXT_X + BAND_PAD_X
        _brush_band(draw, (TEXT_X, y, x + w + BAND_PAD_X, y + h + 2 * BAND_PAD_Y), band, rng)
        _draw_line(draw, (x - left, y + BAND_PAD_Y - top), line, font, ink, number_ink)
        y += h + 2 * BAND_PAD_Y + 10
    return layer.rotate(TILT_DEGREES, resample=Image.BICUBIC, center=(TEXT_X, TEXT_Y))


def _cover(img, w, h):
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def load_host_cutout():
    """Crop the host figure tightly out of its white-background reference."""
    im = Image.open(HOST_IMAGE).convert("RGB")
    bbox = im.convert("L").point(lambda p: 0 if p > 245 else 255).getbbox()
    return im.crop(bbox) if bbox else im


def render_art(scene_path):
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), WHITE)
    if scene_path and Path(scene_path).exists():
        canvas.paste(_cover(Image.open(scene_path).convert("RGB"), CANVAS_W, CANVAS_H), (0, 0))
    else:
        host = load_host_cutout()
        scale = (CANVAS_H - 80) / host.height
        host = host.resize((int(host.width * scale), CANVAS_H - 80), Image.LANCZOS)
        canvas.paste(host, (CANVAS_W - host.width - 80, 60))
    # Fade the left side towards white so the title always reads, even when
    # the art was not composed with an empty left half.
    fade = Image.linear_gradient("L").rotate(90).resize((CANVAS_W // 2, CANVAS_H))
    mask = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    mask.paste(fade.point(lambda p: int(p * 0.75)), (0, 0))
    return Image.composite(Image.new("RGB", canvas.size, WHITE), canvas, mask)


def draw_badge(canvas, text):
    draw = ImageDraw.Draw(canvas)
    for size in range(64, 30, -2):
        font = ImageFont.truetype(FONT_BOLD, size)
        if draw.textlength(text, font=font) <= 420:
            break
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w, h = right - left, bottom - top
    x0, y1 = TEXT_X + 10, CANVAS_H - 50
    box = (x0, y1 - h - 44, x0 + w + 56, y1)
    draw.rounded_rectangle(box, radius=26, fill=BADGE, outline=INK, width=6)
    draw.text((box[0] + 28 - left, box[1] + 22 - top), text, font=font, fill=BADGE_TEXT)


def draw_growth_arrow(canvas):
    """A thick green zig-zag arrow rising into the top-right corner, outlined in ink."""
    draw = ImageDraw.Draw(canvas)
    points = [(1010, 250), (1080, 180), (1120, 215), (1215, 95)]
    head = [(1245, 55), (1180, 78), (1232, 128)]
    for width, colour, grow in ((34, INK, 6), (22, ARROW, 0)):
        draw.line(points, fill=colour, width=width, joint="curve")
        if grow:
            cx = sum(p[0] for p in head) / 3
            cy = sum(p[1] for p in head) / 3
            draw.polygon([(cx + (px - cx) * 1.25, cy + (py - cy) * 1.25) for px, py in head], fill=colour)
        else:
            draw.polygon(head, fill=colour)


def render_thumbnail(lines, badge, scene_path):
    canvas = render_art(scene_path).convert("RGBA")
    canvas.alpha_composite(render_title_layer(lines))
    canvas = canvas.convert("RGB")
    draw_growth_arrow(canvas)
    if badge:
        draw_badge(canvas, badge)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="1-2 Devanagari lines separated by '|', e.g. 'डंपर वाला | कितना कमाता है?'")
    ap.add_argument("--badge", default=None, help="One short rupee figure on a gold badge, e.g. '₹3,000/फेरा'")
    ap.add_argument("--scene", default=None, help="Path to the thumbnail scene PNG")
    ap.add_argument("--out", default=str(ROOT / "brand" / "thumbnail-template-preview.png"))
    args = ap.parse_args()

    lines = split_title(args.title)
    check_no_latin([*lines, args.badge or ""])
    canvas = render_thumbnail(lines, args.badge, args.scene)
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

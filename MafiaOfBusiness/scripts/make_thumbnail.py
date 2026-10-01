#!/usr/bin/env python3
"""
Locked RedHat Engineer thumbnail template.
Host character on the left, <=4 words of title on the right, red/black/white only.

Usage:
    python3 make_thumbnail.py "THE BOX" --out ../episodes/2026-08-22-slug/08_publish/thumbnail.png
    python3 make_thumbnail.py "TINY SWITCH" --accent-word SWITCH
    python3 make_thumbnail.py "TINY SWITCH" --scene ../episodes/<slug>/05_scenes/scene_0001.png

With --scene the episode's own hook image fills the frame and the title sits
on it in huge outlined type -- a bigger, more clickable layout than the
half-empty host-and-title template, which is the fallback.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HOST_IMAGE = ROOT / "brand" / "host" / "host-reference-clean.jpeg"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CANVAS_W, CANVAS_H = 1280, 720
RED = (230, 0, 0)
BLACK = (17, 17, 17)
WHITE = (255, 255, 255)
GRAY = (68, 68, 68)


def load_host_cutout():
    """Crop the host figure tightly out of its white-background reference."""
    im = Image.open(HOST_IMAGE).convert("RGB")
    gray = im.convert("L")
    # Bounding box of "non-white" pixels (the drawn figure).
    bbox = gray.point(lambda p: 0 if p > 245 else 255).getbbox()
    if bbox:
        pad = 20
        l, t, r, b = bbox
        l, t = max(0, l - pad), max(0, t - pad)
        r, b = min(im.width, r + pad), min(im.height, b + pad)
        im = im.crop((l, t, r, b))
    return im


def fit_font(draw, words, max_width, max_height, font_path, start_size=140, min_size=32):
    """Largest bold size where the wrapped title fits the box in at most 2 lines.

    Shrinks all the way to min_size looking for a fit. If even min_size still
    needs a 3rd line, that's a real error (the template hard-caps at 2 lines,
    <=4 words) - raise loudly instead of silently dropping the overflow
    words, which is what an earlier version of this script did.
    """
    size = start_size
    best_at_min = None
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        lines = wrap_words(words, font, max_width, draw)
        if size == min_size:
            best_at_min = (font, lines)
        if len(lines) > 2:
            size -= 4
            continue
        line_h = font.getbbox("Hg")[3] - font.getbbox("Hg")[1]
        total_h = line_h * len(lines) * 1.25
        widest = max(draw.textlength(line, font=font) for line in lines)
        if total_h <= max_height and widest <= max_width:
            return font, lines
        size -= 4
    font, lines = best_at_min
    if len(lines) > 2:
        raise SystemExit(
            f"Title '{' '.join(words)}' doesn't fit the locked template even at "
            f"the smallest font size ({min_size}px) - it needs {len(lines)} lines. "
            f"Shorten it (fewer/shorter words) rather than shipping a thumbnail "
            f"that silently drops words."
        )
    return font, lines


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


def render_scene_thumbnail(words, accent_word, scene_path):
    """Scene image full-bleed, title in big black type with a thick white outline
    so it stays legible over any part of the drawing, framed in red."""
    canvas = Image.open(scene_path).convert("RGB")
    scale = max(CANVAS_W / canvas.width, CANVAS_H / canvas.height)
    canvas = canvas.resize((int(canvas.width * scale) + 1, int(canvas.height * scale) + 1))
    left, top = (canvas.width - CANVAS_W) // 2, (canvas.height - CANVAS_H) // 2
    canvas = canvas.crop((left, top, left + CANVAS_W, top + CANVAS_H))
    draw = ImageDraw.Draw(canvas)

    margin = 50
    font, lines = fit_font(draw, words, int(CANVAS_W * 0.62), CANVAS_H - 2 * margin, FONT_BOLD, start_size=190)
    line_h = font.getbbox("Hg")[3] - font.getbbox("Hg")[1]
    step = int(line_h * 1.2)
    y = (CANVAS_H - step * len(lines)) // 2
    for line in lines:
        x = margin
        for w in line.split():
            color = RED if (accent_word and w.rstrip(":,.") == accent_word.upper()) else BLACK
            draw.text((x, y), w, font=font, fill=color, stroke_width=10, stroke_fill=WHITE)
            x += draw.textlength(w + " ", font=font)
        y += step
    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=RED, width=12)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="Thumbnail title, <=4 words, e.g. 'THE TINY SWITCH'")
    ap.add_argument("--accent-word", default=None, help="One word from the title to render in red")
    ap.add_argument("--scene", default=None, help="Path to a generated scene PNG to use as the background")
    ap.add_argument("--out", default=str(ROOT / "brand" / "thumbnail-template-preview.png"))
    args = ap.parse_args()

    words = args.title.upper().split()
    if len(words) > 4:
        raise SystemExit(f"Title has {len(words)} words; the locked template allows at most 4.")

    if args.scene and Path(args.scene).exists():
        canvas = render_scene_thumbnail(words, args.accent_word, args.scene)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path)
        print(f"Saved {out_path} ({CANVAS_W}x{CANVAS_H}, scene layout)")
        return

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), WHITE)
    draw = ImageDraw.Draw(canvas)

    # --- Host character, left half ---
    host = load_host_cutout()
    left_w, left_h = int(CANVAS_W * 0.46), CANVAS_H
    scale = min((left_w - 60) / host.width, (left_h - 60) / host.height)
    host_resized = host.resize((int(host.width * scale), int(host.height * scale)))
    hx = (left_w - host_resized.width) // 2
    hy = CANVAS_H - host_resized.height  # feet near the bottom edge
    canvas.paste(host_resized, (hx, hy))

    # --- Thin red accent divider ---
    draw.rectangle([left_w, 0, left_w + 6, CANVAS_H], fill=RED)

    # --- Title, right half ---
    text_x0 = left_w + 60
    text_max_w = CANVAS_W - text_x0 - 50
    font, lines = fit_font(draw, words, text_max_w, CANVAS_H - 120, FONT_BOLD)
    line_h = font.getbbox("Hg")[3] - font.getbbox("Hg")[1]
    total_h = int(line_h * 1.25 * len(lines))
    y = (CANVAS_H - total_h) // 2
    for line in lines:
        line_words = line.split()
        x = text_x0
        for i, w in enumerate(line_words):
            color = RED if (args.accent_word and w.rstrip(":,.") == args.accent_word.upper()) else BLACK
            draw.text((x, y), w, font=font, fill=color)
            x += draw.textlength(w + " ", font=font)
        y += int(line_h * 1.25)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"Saved {out_path} ({CANVAS_W}x{CANVAS_H})")

    # Legibility check: how it looks at the YouTube sidebar size.
    small = canvas.resize((210, 118), Image.LANCZOS)
    small_path = out_path.with_name(out_path.stem + "-210x118-preview.png")
    small.save(small_path)
    print(f"Saved legibility check {small_path}")


if __name__ == "__main__":
    main()

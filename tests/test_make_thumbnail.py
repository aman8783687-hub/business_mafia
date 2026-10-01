import json

from PIL import Image

import make_thumbnail as mt
import run_episode


def test_accent_match_ignores_trailing_punctuation_and_handles_rupee():
    assert mt.is_accent("₹40", "₹40")
    assert mt.is_accent("लाख?", "लाख")
    assert not mt.is_accent("चाय", "लाख")
    assert not mt.is_accent("चाय", None)


def _gold_pixels(img):
    gold = tuple(mt.ACCENT)
    return sum(1 for p in img.get_flattened_data() if all(abs(a - b) < 30 for a, b in zip(p, gold)))


def _scene(tmp_path):
    scene = tmp_path / "scene.png"
    Image.new("RGB", (1024, 576), (255, 255, 255)).save(scene)
    return scene


def test_annotated_layout_draws_annotations_with_gold_arrows(tmp_path):
    scene = _scene(tmp_path)
    bare = mt.render_annotated_thumbnail(["पेट्रोल", "पंप", "का", "हिसाब"], "हिसाब", [], scene)
    noted = mt.render_annotated_thumbnail(["पेट्रोल", "पंप", "का", "हिसाब"], "हिसाब",
                                          ["₹4.5/लीटर", "पहले पेमेंट", "लोन ईएमआई", "कैश फ़्लो"], scene)
    assert noted.size == (1280, 720)
    assert _gold_pixels(noted) > _gold_pixels(bare) + 1500  # four gold arrows
    dark = lambda im: sum(1 for p in im.get_flattened_data() if max(p) < 60)
    assert dark(noted) > dark(bare) + 3000  # four black labels


def test_annotated_layout_survives_long_labels_and_missing_scene(tmp_path):
    img = mt.render_annotated_thumbnail(["ढाबे", "का", "हिसाब"], None,
                                        ["दाल = हीरो, बाक़ी सब साइड", "₹1.5 का पापड़ ₹10 में"], None)
    assert img.size == (1280, 720)


def test_scene_and_host_fallbacks_render(tmp_path):
    assert mt.render_scene_thumbnail(["असली", "खेल"], None, _scene(tmp_path)).size == (1280, 720)
    plain = mt.render_host_thumbnail(["चाय", "में", "₹70?"], None)
    accented = mt.render_host_thumbnail(["चाय", "में", "₹70?"], "₹70?")
    assert _gold_pixels(accented) > _gold_pixels(plain) + 1000


def test_latin_letters_are_rejected_but_digits_and_rupee_pass():
    import pytest
    mt.check_no_latin(["₹4.5/लीटर", "पहले पेमेंट"])
    with pytest.raises(SystemExit, match="ईएमआई"):
        mt.check_no_latin(["लोन EMI"])


def test_title_bottom_includes_matras_below_the_line():
    from PIL import ImageDraw, ImageFont
    img = Image.new("RGB", (1280, 300), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(mt.FONT_BOLD, 100)
    bottom = mt._draw_title(draw, ["पेट्रोल"], font, 10, 10, 120, None, fill=(0, 0, 0), stroke=0)
    rows_with_ink = [y for y in range(300) if any(img.getpixel((x, y))[0] < 128 for x in range(0, 700, 2))]
    assert bottom >= max(rows_with_ink)


def test_devanagari_font_is_shaped_not_tofu():
    from PIL import ImageFont, features
    assert features.check("raqm"), "Pillow needs raqm to shape Devanagari"
    font = ImageFont.truetype(mt.FONT_BOLD, 80)
    # 'क्ष' shaped is ONE conjunct, narrower than क + ष side by side
    assert font.getlength("क्ष") < font.getlength("क") + font.getlength("ष")


def test_thumbnail_args_pass_up_to_four_annotations_before_scene(tmp_path):
    ep = tmp_path / "ep"
    (ep / "08_publish").mkdir(parents=True)
    (ep / "05_scenes").mkdir()
    (ep / "05_scenes" / "scene_0001.png").write_bytes(b"png")
    notes = ["₹4.5/लीटर", "पहले पेमेंट", "लोन ईएमआई", "कैश फ़्लो", "पाँचवाँ"]
    (ep / "08_publish" / "metadata.json").write_text(json.dumps(
        {"thumbnail_text": "पेट्रोल पंप का हिसाब", "thumbnail_annotations": notes}, ensure_ascii=False))
    args = run_episode.thumbnail_args(ep)
    passed = [args[k + 1] for k, a in enumerate(args) if a == "--annotation"]
    assert passed == notes[:4]
    assert args[-2] == "--scene"

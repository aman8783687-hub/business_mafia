from PIL import Image

import make_thumbnail as mt


def _scene(tmp_path):
    scene = tmp_path / "scene.png"
    Image.new("RGB", (1024, 576), (255, 255, 255)).save(scene)
    return scene


def _count(img, rgb, tol=30):
    return sum(1 for p in img.get_flattened_data() if all(abs(a - b) < tol for a, b in zip(p, rgb)))


def test_two_line_title_draws_a_black_and_a_yellow_band_on_the_left(tmp_path):
    img = mt.render_thumbnail(["डंपर वाला", "कितना कमाता है?"], None, _scene(tmp_path))
    assert img.size == (1280, 720)
    left = img.crop((0, 0, 640, 360))
    assert _count(left, mt.BAND) > 20000
    assert _count(left, mt.INK) > 20000
    assert _count(img.crop((800, 0, 1280, 720)), mt.BAND) < 500  # the right side is the scene's


def test_badge_adds_green_and_missing_scene_uses_the_host(tmp_path):
    plain = mt.render_thumbnail(["कितना कमाता है?"], None, None)
    badged = mt.render_thumbnail(["कितना कमाता है?"], "₹4.5/लीटर", None)
    assert _count(badged, mt.BADGE) > _count(plain, mt.BADGE) + 5000


def test_rupee_figures_are_highlighted_and_the_growth_arrow_is_drawn(tmp_path):
    img = mt.render_thumbnail(["₹10,000 से शुरू", "ये 7 बिज़नेस"], None, _scene(tmp_path))
    plain = mt.render_thumbnail(["दस हज़ार से शुरू", "ये सात बिज़नेस"], None, _scene(tmp_path))
    left = (0, 0, 760, 400)
    assert _count(img.crop(left), mt.NUMBER_ON_INK) > _count(plain.crop(left), mt.NUMBER_ON_INK) + 1000
    assert _count(img.crop(left), mt.NUMBER_ON_BAND) > _count(plain.crop(left), mt.NUMBER_ON_BAND) + 300
    assert _count(img.crop((980, 30, 1280, 280)), mt.ARROW) > 3000


def test_split_title_enforces_lines_and_words():
    import pytest
    assert mt.split_title("पेट्रोल पंप वाला | कितना कमाता है?") == ["पेट्रोल पंप वाला", "कितना कमाता है?"]
    assert mt.split_title("कितना कमाता है?") == ["कितना कमाता है?"]
    with pytest.raises(SystemExit, match="1-2 lines"):
        mt.split_title("एक | दो | तीन")
    with pytest.raises(SystemExit, match="at most 4"):
        mt.split_title("एक दो तीन चार पाँच")


def test_latin_letters_are_rejected_but_digits_and_rupee_pass():
    import pytest
    mt.check_no_latin(["₹4.5/लीटर", "पहले पेमेंट"])
    with pytest.raises(SystemExit, match="ईएमआई"):
        mt.check_no_latin(["लोन EMI"])


def test_devanagari_font_is_shaped_not_tofu():
    from PIL import ImageFont, features
    assert features.check("raqm"), "Pillow needs raqm to shape Devanagari"
    font = ImageFont.truetype(mt.FONT_BOLD, 80)
    # 'क्ष' shaped is ONE conjunct, narrower than क + ष side by side
    assert font.getlength("क्ष") < font.getlength("क") + font.getlength("ष")

import check_script

SECTIONS = ["hook", "duniya", "khel", "raaz", "sabak"]

GOOD = """# चाय वाला
Target runtime: 4:00

[HOOK]
1. एक कप चाय दस रुपये की, पर उसमें मुनाफ़ा कितना?

[DUNIYA]
2. सुबह पाँच बजे रमेश अपनी टपरी खोलता है।

[KHEL]
3. दूध, चीनी और पत्ती मिलाकर लागत तीन रुपये आती है।

[RAAZ]
12. असली कमाई चाय से नहीं, साथ बिकने वाले बिस्कुट से होती है।

[SABAK]
13. आपके शहर में चाय कितने की है? कमेंट में बताइए।
"""


def test_good_script_passes():
    assert check_script.check(GOOD, SECTIONS) == []


def test_beat_numbers_are_not_digits_in_narration():
    # "12." is a beat index, not narration -- must not be flagged.
    assert not any("digit" in p for p in check_script.check(GOOD, SECTIONS))


def test_digits_in_narration_are_rejected():
    bad = GOOD.replace("लागत तीन रुपये", "लागत 3 रुपये")
    problems = check_script.check(bad, SECTIONS)
    assert any("beat 3" in p and "digit" in p for p in problems)


def test_english_sentence_is_rejected():
    bad = GOOD.replace("सुबह पाँच बजे रमेश अपनी टपरी खोलता है।",
                       "Every morning Ramesh opens his tea stall at five.")
    problems = check_script.check(bad, SECTIONS)
    assert any("beat 2" in p and "Devanagari" in p for p in problems)


def test_a_few_english_business_words_are_fine():
    ok = GOOD.replace("असली कमाई", "असली profit")
    assert check_script.check(ok, SECTIONS) == []


def test_missing_and_out_of_order_sections():
    missing = GOOD.replace("[RAAZ]\n", "")
    assert any("missing" in p and "RAAZ" in p for p in check_script.check(missing, SECTIONS))
    swapped = GOOD.replace("[DUNIYA]", "[TMP]").replace("[KHEL]", "[DUNIYA]").replace("[TMP]", "[KHEL]")
    assert any("order" in p for p in check_script.check(swapped, SECTIONS))


def test_a_wrapped_line_without_a_beat_number_is_flagged_not_ignored():
    bad = GOOD.replace("लागत तीन रुपये आती है।", "लागत तीन रुपये आती है,\nदस हज़ार नहीं 10,000 रुपये।")
    problems = check_script.check(bad, SECTIONS)
    assert any("without a beat number" in p and "10,000" in p for p in problems)


def test_beat_without_a_space_after_the_dot_is_still_a_beat():
    # stitch_audio parses r"^\s*(\d+)\.\s*(.+)$", so "2.पैसा 5 लाख" is beat 2 there
    bad = GOOD.replace("2. सुबह पाँच बजे", "2.सुबह 5 बजे")
    assert any("beat 2" in p and "digit" in p for p in check_script.check(bad, SECTIONS))


def _plan(*chunks):
    return {"chunks": [{"id": i + 1, "beats": b, "text": t} for i, (b, t) in enumerate(chunks)]}


def test_chunk_plan_matching_the_script_passes():
    plan = _plan(([1, 2], "एक कप चाय दस रुपये की।"), ([3], "दूध चीनी पत्ती।"), ([12, 13], "असली कमाई। कमेंट कीजिए।"))
    assert check_script.check_chunk_plan(GOOD, plan) == []


def test_chunk_text_with_digits_or_english_is_flagged_because_that_is_what_gets_spoken():
    plan = _plan(([1, 2], "लागत 10,000 रुपये"), ([3], "Every morning he opens the stall"),
                 ([12, 13], "असली कमाई।"))
    problems = check_script.check_chunk_plan(GOOD, plan)
    assert any("chunk 1" in p and "digit" in p for p in problems)
    assert any("chunk 2" in p and "English" in p for p in problems)


def test_chunk_plan_must_cover_every_beat_exactly_once():
    plan = _plan(([1, 2, 3], "ठीक।"), ([3, 99], "ठीक।"))
    problems = check_script.check_chunk_plan(GOOD, plan)
    assert any("beat 3" in p and "more than one chunk" in p for p in problems)
    assert any("beat 99" in p and "not in script" in p for p in problems)
    assert any("beat 12" in p and "no chunk" in p for p in problems)


def test_metadata_must_make_a_buildable_thumbnail_before_anything_is_spent():
    ok = {"title": "पेट्रोल पंप", "thumbnail_text": "पेट्रोल पंप वाला | कितना कमाता है?",
          "thumbnail_badge": "₹4.5/लीटर", "thumbnail_scene": "a petrol pump"}
    assert check_script.check_metadata(ok) == []
    assert any("thumbnail_text" in p for p in check_script.check_metadata({"title": "x"}))
    assert any("at most 4 words" in p for p in check_script.check_metadata({**ok, "thumbnail_text": "एक दो तीन चार पाँच"}))
    assert any("1-2 lines" in p for p in check_script.check_metadata({**ok, "thumbnail_text": "एक | दो | तीन"}))
    assert any("thumbnail_scene" in p for p in check_script.check_metadata({**ok, "thumbnail_scene": ""}))
    bad = check_script.check_metadata({**ok, "thumbnail_badge": "लोन EMI"})
    assert any("Latin" in p and "EMI" in p for p in bad)

def test_word_budget_follows_the_runtime_window():
    fmt = {"words_per_minute": 140, "runtime_min_seconds": 480, "runtime_max_seconds": 720}
    assert check_script.word_budget(fmt) == (1064, 1764)
    beat = "1. " + " ".join(["शब्द"] * 10)
    assert check_script.check_word_count("\n".join([beat] * 140), (1064, 1764)) == []
    assert "at least 1064" in check_script.check_word_count("\n".join([beat] * 50), (1064, 1764))[0]
    assert "at most 1764" in check_script.check_word_count("\n".join([beat] * 200), (1064, 1764))[0]


def test_state_word_budget_is_the_8_to_12_minute_format():
    from state import load_state
    assert check_script.word_budget(load_state()["format"]) == (1064, 1764)


def test_topic_format_must_be_kamai_or_list():
    assert check_script.check_topic({"format": "list"}, ["kamai", "list"]) == []
    assert check_script.check_topic({}, ["kamai", "list"]) == []  # older episodes are deep dives
    assert "use one of" in check_script.check_topic({"format": "short"}, ["kamai", "list"])[0]

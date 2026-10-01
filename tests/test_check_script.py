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

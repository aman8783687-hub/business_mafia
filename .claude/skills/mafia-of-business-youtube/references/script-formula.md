# Script formula (Hindi)

The script is the video. Assume the viewer's thumb is over the back button the whole time.

## Specs

- **Length:** about 480-600 Hindi words for 240 s (`hi-IN-MadhurNeural` speaks ~140 words/min). `stitch_audio.py` fails over 300 s or under 180 s: trim or add, never speed the voice.
- **Language:** conversational Hindi in Devanagari, the way people talk at a chai stall, not textbook shuddh Hindi. English business words stay English but in Devanagari: प्रॉफ़िट, मार्जिन, कस्टमर, ब्रांड.
- **Numbers as words:** "दस रुपये", "पचास हज़ार", "दो लाख". Never digits (`check_script.py` rejects them).
- **Hisaab, not math:** one rupee number per beat, carried by the character. Named costs (ईएमआई, किराया, डीज़ल, स्टाफ़, बिजली) are good. No formulas, no stacked percentages, no tables.
- **Voice:** second person, present tense. "आप सुबह पाँच बजे दुकान खोलते हैं..." beats "दुकानदार सुबह दुकान खोलता था".
- **Sentences:** short. Vary rhythm. A three-word line after a long one lands hard: "और यहीं है खेल।"
- **No filler:** no "नमस्कार दोस्तों", no "आज के इस वीडियो में", no channel intro. They cost the seconds you can least afford.
- **No calculations on screen or in speech:** if a number needs a calculation to understand, replace it with a comparison ("एक कप पर जितना कमाता है, उतने में आपका बिस्कुट आता है").

## Structure

### [HOOK] (0:00-0:20) -- myth, then one number
Open on the belief everyone has, then break it with one number, then tease the secret:
- "पेट्रोल पंप खोल लो, बैठे-बैठे नोट गिनो... सुनने में कितना आसान लगता है ना?"
- "पर पंचानवे रुपये के पेट्रोल में मालिक को मिलते हैं सिर्फ़ साढ़े चार रुपये।"
- "और आख़िर में वो एक बात, जिस पर पूरा धंधा टिका है।"

### [DUNIYA] (0:20-1:00) -- the character and the setup
Introduce a hypothetical owner with a common name, always as an example: "मान लीजिए रमेश..." (never presented as a real person). What he invests, where, why he started. Put the viewer there: "आपने भी देखा होगा..."

### [KHEL] (1:00-3:00) -- पैसा कहाँ बनता है, कहाँ डूबता है
First the money coming in, then the leaks: EMI, rent, staff, bijli, diesel, wastage, udhaar. Each leak is a small scene with रमेश and one rupee number. Include one comparison (highway vs gaon, small vs big, good month vs bad month).

### [RAAZ] (3:00-3:45) -- the hero product or the hidden twist
The one non-obvious thing the business really runs on: the dal that carries the dhaba, the papad bought at डेढ़ रुपये and sold at दस, the tanker that must be paid before a single litre is sold, the one bad month that sinks a dumper owner. Slow down. Pay off the hook's tease explicitly.

### [SABAK] (last 20-40 s) -- rules and the payoff
Two or three simple rules (मेन्यू छोटा रखो, इमरजेंसी फ़ंड, बार-बार आने वाला ग्राहक मार्जिन से बड़ा). The payoff line: "ये धंधा पेट्रोल का नहीं, कैश-फ़्लो और भरोसे का है।" One specific comment question ("आपके शहर में एक प्लेट मोमो कितने की है?"). Name the next episode ("अगली बार: डंपर वाले का पूरा हिसाब"). Ask for the subscribe once, about the series.

## Retention rules

- Mark the script every 30 seconds (~70 words). At each mark ask: what changed? If nothing, add a turn, a question to the viewer, a new character or a new place.
- Never stack two abstract lines without something the stickman can act out.
- Kill the second-best example. Three great leaks beat five okay ones.
- Every estimate is said as one: "अंदाज़न", "लगभग", with a round range.

## Format of `02_script/script.md`

```markdown
# चाय वाला असल में कितना कमाता है
Target runtime: 4:00

[HOOK]
1. दस रुपये की चाय, इसमें क्या कमाई... सुनने में तो यही लगता है ना?
2. पर बनाने में लगते हैं सिर्फ़ तीन रुपये। और असली कमाई चाय से होती भी नहीं। वो राज़ आख़िर में।

[DUNIYA]
3. ...

[KHEL]
...

[RAAZ]
...

[SABAK]
...
```

Beat numbers are ASCII digits followed by a dot; narration text has no digits. Run `python3 scripts/check_script.py <slug>` after writing.

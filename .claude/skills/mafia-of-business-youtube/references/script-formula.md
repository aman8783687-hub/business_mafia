# Script formula (Hindi)

The script is the video. Assume the viewer's thumb is over the back button the whole time.

## Tone: the good side of business

The viewer should finish feeling "यार, ये तो इज़्ज़त का धंधा है, और समझदारी से किया जाए तो मैं भी कर सकता हूँ।" Respect for the owner, curiosity about the skill, hope at the end. The hisaab stays honest; only the framing changes:

- **Admire, don't expose.** The owner is smart and hardworking, never a victim and never a cheat. "लोग इसे छोटा धंधा समझते हैं" beats "ये धंधा एक जाल है".
- **Every cost comes with its fix.** Name the cost (ईएमआई, डीज़ल, स्टाफ़) and in the same beat show how good owners handle it (bulk ख़रीद, repeat कस्टमर, सही रूट, छोटा मेन्यू). A cost is never left as a dead end.
- **No doom words** in the hook, the [RAAZ] or the ending: डूबना, बर्बाद, जाल, धोखा, फँस गया. Risk is said once, calmly, with what owners do about it.
- **No get-rich promise either.** Real numbers, estimates said as estimates. Feeling good comes from understanding and respect, not from hype.
- **End on a win** for रमेश and a line of respect for the people in the trade.

## Specs

- **Length:** 8-12 minutes, about 1,250-1,500 Hindi words for a 600 s target (`hi-IN-MadhurNeural` speaks ~140 words/min). `check_script.py` fails a script under ~1,060 or over ~1,760 words; `stitch_audio.py` fails under 480 s or over 720 s: edit the script, never the voice speed. Why so long: on the reference channel (Growth Mitra, 2026-10-04) every 2.5-9 minute video got 100-700 views and every hit ran 16-27 minutes. Length is earned with more substance (more cost-and-fix scenes, more ideas, the "आप शुरू करें तो" block), never with padding.
- **Two formats** (`topic.json` `format`, alternate them): **`kamai`**, the deep dive "<X> वाला कितना कमाता है?", and **`list`**, "₹<X> से शुरू करें ये <N> बिज़नेस". Both use the same five tags, so voice presets and checks are unchanged.
- **Language:** conversational Hindi in Devanagari, the way people talk at a chai stall, not textbook shuddh Hindi. English business words stay English but in Devanagari: प्रॉफ़िट, मार्जिन, कस्टमर, ब्रांड.
- **Numbers as words:** "दस रुपये", "पचास हज़ार", "दो लाख". Never digits (`check_script.py` rejects them).
- **Hisaab, not math:** one rupee number per beat, carried by the character. Named costs (ईएमआई, किराया, डीज़ल, स्टाफ़, बिजली) are good. No formulas, no stacked percentages, no tables.
- **Voice:** second person, present tense. "आप सुबह पाँच बजे दुकान खोलते हैं..." beats "दुकानदार सुबह दुकान खोलता था".
- **Sentences:** short. Vary rhythm. A three-word line after a long one lands hard: "और यहीं है खेल।"
- **No filler:** no "नमस्कार दोस्तों", no "आज के इस वीडियो में", no channel intro. They cost the seconds you can least afford.
- **No calculations on screen or in speech:** if a number needs a calculation to understand, replace it with a comparison ("एक कप पर जितना कमाता है, उतने में आपका बिस्कुट आता है").

## Structure: `kamai` (deep dive)

### [HOOK] (0:00-0:30) -- the question, one surprising number, the tease
Open on the question everyone has wondered about, answer it with one number that makes the viewer look at this business with new respect, then tease the owner's smart move:
- "पेट्रोल पंप वाला एक लीटर पर कितना कमाता है? सोचा है कभी?"
- "पंचानवे रुपये के पेट्रोल में मालिक को मिलते हैं लगभग साढ़े चार रुपये। फिर भी अच्छे पंप वाले अच्छी कमाई करते हैं।"
- "कैसे? उनकी एक समझदारी वाली चाल है। वो आख़िर में।"

### [DUNIYA] (0:30-2:00) -- the character and the setup
Introduce a hypothetical owner with a common name, always as an example: "मान लीजिए रमेश..." (never presented as a real person). What he invests, where, why he started, what his first month looked like. Put the viewer there: "आपने भी देखा होगा..."

### [KHEL] (2:00-6:30) -- पैसा कहाँ से आता है, और समझदार मालिक उसे कैसे बचाता है
First the money coming in and the skill behind it: a normal day, a slow day, a festival day. Then four or five costs (EMI, rent, staff, bijli, diesel, wastage, udhaar), each a small scene with रमेश, one rupee number, and his fix in the same beat. Two comparisons that show what good owners do differently (highway vs gaon, new owner vs experienced owner, small setup vs big setup). End [KHEL] with the month's hisaab in words: what comes in, what goes out, what रमेश keeps, as a range.

### [RAAZ] (6:30-8:00) -- the owner's smart move
The one non-obvious thing good owners do that makes the business work: the dal that carries the dhaba, the papad bought at डेढ़ रुपये and sold at दस, the air-and-service corner that brings the pump's regulars back, the fixed contract that keeps a dumper busy all month. Told with admiration. Slow down. Pay off the hook's tease explicitly.

### [SABAK] (last 1:30-2:30) -- "आप शुरू करना चाहें तो", rules and the payoff
First the viewer's version, the part that made the reference channel's videos travel: "अगर आप ये शुरू करना चाहें तो" -- roughly what it takes to start small (a round range), the first step, and the one mistake beginners make. Then two or three simple rules for doing it well (मेन्यू छोटा रखो, इमरजेंसी फ़ंड, बार-बार आने वाला ग्राहक मार्जिन से बड़ा). The payoff line, with respect: "ये धंधा पेट्रोल का नहीं, कैश-फ़्लो और भरोसे का है। अगली बार पंप पर जाएँ, तो इस मेहनत को याद रखिएगा।" One warm comment question ("आपके शहर में सबसे भरोसेमंद पंप कौन सा है?", "आपके शहर में एक प्लेट मोमो कितने की है?"). Name the next episode ("अगली बार: डंपर वाले का पूरा हिसाब"). Ask for the subscribe once, about the series.

## Structure: `list` ("₹<X> से शुरू करें ये <N> बिज़नेस")

Five to seven businesses the viewer could start with that budget, from the channel's verticals (`topic-strategy.md`). Real, legal, local, no apps or schemes. Same tone: respect, honest ranges, no promise.

### [HOOK] (0:00-0:40) -- the budget shock and the tease
- Make the budget concrete: "दस हज़ार रुपये। आज इतने में एक ठीक-ठाक फ़ोन भी नहीं आता।"
- The promise, said honestly: "पर सही जगह लगें, तो ये एक छोटा धंधा खड़ा कर सकते हैं।"
- What each idea comes with: where the money goes, a realistic monthly range, the one mistake to avoid.
- The tease: "चौथा और छठा आइडिया शायद आपको हैरान कर दे, क्योंकि उनकी बात कोई नहीं करता।"
- One calm line of honesty: "ये जल्दी अमीर बनने वाला वीडियो नहीं है। मेहनत हर धंधे में लगती है।"

### [DUNIYA] (0:40-1:30) -- who this is for
"मान लीजिए रमेश" (or a सीमा) with that budget: a student, a job-holder, someone at home. One rule that applies to all the ideas: start small, test in the mohalla first, grow from repeat customers.

### [KHEL] (1:30-8:00) -- the ideas, one by one
Each idea opens with its number in words ("बिज़नेस नंबर एक: घर का टिफ़िन") and gets about a minute in four moves: what the budget buys, how the first customers come, the monthly range as an estimate ("दस ग्राहक हों तो महीने के लगभग बीस से पच्चीस हज़ार"), and the beginner's mistake with its fix. Put the two strongest ideas at positions 1 and the teased number. Make each idea a small scene the stickman can act out (one prop each).

### [RAAZ] (8:00-9:00) -- the surprising idea and the common thread
Pay off the teased idea, then the one move that works across all of them (repeat customers, a small menu, cash-flow before profit). Told with respect for people already doing it.

### [SABAK] (last 1:00-1:30) -- choose, start, comment
How to pick one by skill and location, not by the biggest number. A warm comment question ("आप कौन सा शुरू करेंगे? आपके शहर में किसकी डिमांड है?"), the next episode, and the subscribe ask once.

### Chapters
Every idea is a chapter in the description (`0:00 हुक`, `1:30 बिज़नेस 1: टिफ़िन सर्विस`, ...).

## Retention rules

- Mark the script every 30 seconds (~70 words). At each mark ask: what changed? If nothing, add a turn, a question to the viewer, a new character or a new place.
- Keep an open loop running the whole video: the [HOOK] tease, then about every two minutes a forward pointer ("पर असली कमाल अभी बाकी है", "इसका जवाब [RAAZ] में").
- Never stack two abstract lines without something the stickman can act out.
- Kill the second-best example. Three great cost-and-fix beats beat five okay ones.
- Every estimate is said as one: "अंदाज़न", "लगभग", with a round range.

## Format of `02_script/script.md`

```markdown
# चाय वाला असल में कितना कमाता है
Target runtime: 10:00

[HOOK]
1. दस रुपये की चाय बेचने वाला कितना कमाता है? जवाब सुनकर आप उसे इज़्ज़त से देखेंगे।
2. बनाने में लगते हैं लगभग तीन रुपये। और समझदार चाय वाले की असली कमाई एक और चीज़ से होती है। वो राज़ आख़िर में।

[DUNIYA]
3. ...

[KHEL]
...

[RAAZ]
...

[SABAK]
...
```

Beat numbers are ASCII digits followed by a dot; narration text has no digits. Write beats of two or three sentences (7-10 s of speech each, one scene per beat): a 10-minute script is about 65-85 beats. Run `python3 scripts/check_script.py <slug>` after writing.

# Thumbnail, title, metadata and SEO

Packaging decides whether the video is clicked; retention decides whether YouTube shows it to more people. Never trade one for the other: no promise the video does not keep. Same template every episode, so the series is recognisable.

## Thumbnail: the question template (`scripts/make_thumbnail.py`, run by `run_episode.py`)

Modelled on the operator's hand-made petrol pump thumbnail, which replaced the old white "हिसाब" infographic (that one read like a worksheet at phone size; episode 1 CTR was 2.6%).

- **Title, left side, two brush-stroke bands, tilted slightly:** line 1 white on black, line 2 black on yellow. Words with a digit or ₹ are highlighted automatically (yellow on the black band, green on the yellow band), so put the money and the count in digits. `thumbnail_text` (lines split by `|`, at most 4 words per line):
  - `kamai`: `"<X> वाला | कितना कमाता है?"`
  - `list`: `"₹10,000 से शुरू | ये 7 बिज़नेस"` (the budget on line 1, the count on line 2, exactly as the title says them).
  The thumbnail says the same thing as the video title.
- **Growth arrow:** a green zig-zag arrow is drawn top right on every thumbnail (the reference channel's signature cue for money growing).
- **Art, right side:** `generate_thumbnail_scene.py` makes one FLUX image from `thumbnail_scene`: the boss large on the right, hand on chin, curious and impressed, at the business, gold money (note stacks, a bowl of coins) in front, the left half empty. Write `thumbnail_scene` in English, naming the business and two props: "a big tipper dumper truck tipping a heap of sand behind him, stacks of gold rupee notes and a bowl of gold coins on the ground in front of him". Look at `08_publish/thumbnail_scene.png`; if the boss is off-model or the left half is busy, rerun with `--force --seed <n>`.
- **Optional green badge, bottom left:** `thumbnail_badge`, one rupee figure the video states: "₹3,000/फेरा", "₹4.5/लीटर", for a `list` episode the best idea's range "₹24,000/महीना". Digits and ₹ are fine; **no Latin letters** (the font has none). The figure must be in `sources.md` or said in the video as an estimate.
- **Mood:** bright, curious and admiring, never alarmed. No red, no "सच्चाई जानकर हैरान" bait. Never a real person's face (the reference channel uses Warren Buffett's; we do not).
- For a `list` episode, `thumbnail_scene` shows the boss with three or four small businesses' props spread behind him (a tiffin stack, a phone-cover stand, a sewing machine) and gold money in front.
- Legibility: open `thumbnail-210x118-preview.png`; both lines must read at that size.

## Title: two series templates

`kamai`: `<X> वाला कितना कमाता है? 💰 | <one specific, positive hook in Hindi>`

`list`: `₹<budget> से शुरू करें ये <N> बिज़नेस 🔥 | <one honest hook>`, e.g. `₹10,000 से शुरू करें ये 7 बिज़नेस 🔥 | कम लागत, अच्छी कमाई` (the reference channel's 261K title shape). Budgets that worked there: ₹2,000, ₹10,000, ₹20,000. Never "करोड़ों की कमाई" or any promise the video does not show.

e.g. `पेट्रोल पंप वाला कितना कमाता है? 💰 | 1 लीटर पर असली कमाई` (the operator's title, which outperformed the old English-tailed template), `डंपर वाला कितना कमाता है? 💰 | एक फेरे की असली कमाई`. Adapt the first half to the business ("<X> वाली", "<X> मालिक"). The hook names a unit the viewer can picture (1 लीटर, एक फेरा, एक प्लेट, एक कप). Digits are fine in the title. 40-80 characters. Put two variations in `title_alternates` for YouTube's Test & Compare.

## Description

```
[Myth hook in Hindi + the main Hinglish search phrase, within the first 150 characters.]

[2-3 Hindi sentences on what the video reveals, with respect for the owner, without giving away the RAAZ.]

⏱️ Chapters
0:00 [hook label in Hindi]
0:xx रमेश की कहानी
0:xx पैसा कहाँ से आता है
0:xx मालिक की समझदारी
0:xx सबक

🔍 आपके सवाल (Your Queries):
[15-20 search phrases, one per line: Hinglish, Devanagari and English variants]

📚 Sources
- [source] -- [URL]

🎩 Business Mafia -- हर धंधे का असली हिसाब, हिंदी में।

#BusinessMafia #BusinessModel #[TopicHashtag]
```

Chapters come from `03_audio/timings.json` section start times; at least four, first at 0:00. A `list` episode gets one chapter per idea ("1:30 बिज़नेस 1: टिफ़िन सर्विस"); a `kamai` episode adds a chapter for "आप शुरू करना चाहें तो". Leave out subscribe/playlist links; the operator adds them.

## Tags

15-25, within YouTube's 500-character limit: the main query in Hinglish, Devanagari and English ("petrol pump kitna kamata hai", "पेट्रोल पंप कितना कमाता है", "petrol pump business profit"), cost/investment variants ("petrol pump investment", "petrol pump dealer margin"), common misspellings, and series terms ("business model in hindi", "Business Mafia").

## Playlist

`playlist` = the topic's vertical (`topic-strategy.md`); every `list` episode goes to "कम पैसे में बिज़नेस" instead, so the listicles binge together. `posting.md` tells the operator which playlist to add the video to.

## Engagement package (in `metadata.json`, copied into `posting.md`)

- `pinned_comment`: a bonus fact plus a question, in Hindi.
- `community_post`: a one-line poll ("पेट्रोल पंप मालिक को एक लीटर पर कितना मिलता है? A) ₹20 B) ₹10 C) ₹5 से कम").
- `shorts_hook`: `{"start": 0.0, "end": <end of the last [HOOK] or first [DUNIYA] beat, 30-55 s>}` from `timings.json`, for a hand-cut Short.

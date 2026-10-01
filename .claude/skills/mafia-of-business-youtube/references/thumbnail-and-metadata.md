# Thumbnail, title, metadata and SEO

Packaging decides whether the video is clicked; retention decides whether YouTube shows it to more people. Never trade one for the other: no promise the video does not keep. Same template every episode, so the series is recognisable.

## Thumbnail: the "hisaab" infographic (`scripts/make_thumbnail.py`, run by `run_episode.py`)

- White whiteboard, gold frame. Title band on top: `thumbnail_text` = "<X> का हिसाब" (2-4 Devanagari words), `thumbnail_accent_word` = "हिसाब" or the business name, drawn in gold, gold underline.
- Centre: the thumbnail scene (`thumbnail_beat`, default 1): the boss at the business, subject centred, empty space left and right.
- `thumbnail_annotations`: 3-4 money notes, each 2-3 words, ~12 characters max, placed left and right with gold arrows: "₹4.5/लीटर", "पहले पेमेंट", "लोन ईएमआई", "दाल = हीरो", "बर्बादी ₹2,500/दिन". Digits and ₹ are fine; **no Latin letters** (the font has none; the script refuses them): write ईएमआई, not EMI. Every figure must be in `sources.md` or said in the video as an estimate.
- Legibility: open `thumbnail-210x118-preview.png`; if the title band isn't readable at that size, shorten it.

## Title: one series template

`<X> वाला असल में कितना कमाता है? | <X in English> Business Profit in Hindi`

e.g. `पेट्रोल पंप वाला असल में कितना कमाता है? | Petrol Pump Business Profit in Hindi`. Adapt the Devanagari half to the business ("<X> असल में कितना कमाता है?", "<X> की असली कमाई?"), keep the English half. 45-80 characters. Put two variations in `title_alternates` for YouTube's Test & Compare.

## Description

```
[Myth hook in Hindi + the main Hinglish search phrase, within the first 150 characters.]

[2-3 Hindi sentences on what the video reveals, without giving away the RAAZ.]

⏱️ Chapters
0:00 [hook label in Hindi]
0:xx रमेश की कहानी
0:xx पैसा कहाँ बनता है, कहाँ डूबता है
0:xx असली राज़
0:xx सबक

🔍 आपके सवाल (Your Queries):
[15-20 search phrases, one per line: Hinglish, Devanagari and English variants]

📚 Sources
- [source] -- [URL]

🎩 Mafia of Business -- हर धंधे का असली हिसाब, हिंदी में।

#MafiaOfBusiness #BusinessModel #[TopicHashtag]
```

Chapters come from `03_audio/timings.json` section start times; at least four, first at 0:00. Leave out subscribe/playlist links; the operator adds them.

## Tags

15-25, within YouTube's 500-character limit: the main query in Hinglish, Devanagari and English ("petrol pump kitna kamata hai", "पेट्रोल पंप कितना कमाता है", "petrol pump business profit"), cost/investment variants ("petrol pump investment", "petrol pump dealer margin"), common misspellings, and series terms ("business model in hindi", "Mafia of Business").

## Playlist

`playlist` = the topic's vertical (`topic-strategy.md`). `posting.md` tells the operator which playlist to add the video to.

## Engagement package (in `metadata.json`, copied into `posting.md`)

- `pinned_comment`: a bonus fact plus a question, in Hindi.
- `community_post`: a one-line poll ("पेट्रोल पंप मालिक को एक लीटर पर कितना मिलता है? A) ₹20 B) ₹10 C) ₹5 से कम").
- `shorts_hook`: `{"start": 0.0, "end": <end of the last [HOOK] or first [DUNIYA] beat, 30-55 s>}` from `timings.json`, for a hand-cut Short.

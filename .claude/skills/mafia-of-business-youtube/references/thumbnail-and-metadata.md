# Thumbnail, title and metadata

Packaging decides whether the video gets watched. On a daily channel, it is the highest-leverage 30 minutes of the whole day.

## Thumbnail

**Locked template** (`scripts/make_thumbnail.py`, run by `run_episode.py` from `metadata.json`):
- 1280x720, PNG, `08_publish/thumbnail.png`.
- **Scene layout (default when the thumbnail beat's PNG exists):** the episode's own hook scene fills the frame (`thumbnail_beat`, default 1), 2-4 words of title in huge black type with a thick white outline on the left, one word in `#E60000`, red frame. Write that beat with the subject on the right and empty space on the left (see `visuals-and-animation.md`).
- **Fallback layout:** the host on the left, title on the right, on white.
- **Text:** 2-4 words, never a full sentence, never a title repeat.
- **Never:** shocked-face clickbait, red arrows and circles, a fifth colour, small text, anything touching the frame edge (the timestamp overlays the bottom-right corner).

**Text formulas that work:** the contradiction ("TOO SMALL TO SEE"), the stake ("$3 TRILLION IDEA"), the mystery ("NOBODY NOTICED"), the scale ("5,000 YEARS LATE").

**Legibility test:** scale to 210×118 px and look at it. If the words aren't readable and the object isn't identifiable at that size, redo it. Also check it against a dark and a light UI background.

Once the channel has enough traffic, use YouTube's built-in thumbnail Test & Compare on videos where two concepts genuinely differ — and feed the winner's pattern back into the template.

## Title

- 45–60 characters so it isn't truncated on mobile.
- Front-load the interesting word; the last third of a title often gets cut.
- One clear idea, no ALL CAPS, no more than one piece of punctuation.
- The title must be a promise the video keeps. Overpromising buys one click and loses a subscriber.

**Formulas:**
- *The Invention That [Unexpected Consequence]* — "The Invention That Made Cities Possible"
- *Why [Common Thing] Took [Surprising Time]* — "Why the Wheel Took 5,000 Years to Reach Suitcases"
- *How [Thing] Actually Works* — reserved for genuinely mechanism-led videos
- *[Year]: The Machine That [Change]* — "1947: The Machine That Ate the Vacuum Tube"
- *The [Adjective] History of [Thing]* — use sparingly, it's the most crowded pattern

Write three candidate titles every day and pick one. Log the rejected ones — they're useful for A/B retitling underperformers after 48 hours.

## Description

```
[1–2 sentence hook restating the video's promise, containing the main search term naturally.]

[3–4 sentences on what the video covers.]

⏱️ Chapters
0:00 [Hook line]
0:xx [Section]
...

📚 Sources
- [Source name] — [URL]
- ...

🎩 RedHat Engineer explains the innovations that built the modern world — one story a day.
Subscribe: [channel URL]

▶️ Watch next: [most relevant previous video + link]
📂 Series playlist: [link]

#hashtag1 #hashtag2 #hashtag3
```

The agent cannot look up channel or playlist URLs: leave out the `Subscribe`, `Watch next` and `Series playlist` lines rather than writing `[link]` placeholders; the operator adds them when posting.

Chapters need at least three timestamps and the first must be 0:00. Sources in the description are a real credibility signal on a history-of-technology channel — never skip them.

## Tags and metadata

The agent writes the tags and the fields in `metadata-and-delivery.md`; the playlist, end screen, pinned comment and other YouTube Studio settings below are done by the operator when posting.

- 8–15 tags: the exact topic, 2–3 synonyms, the series name, plus format terms (technology history, explained, documentary, animation).
- Set the video to **Not made for kids**.
- Set language and caption language; upload the `.srt`.
- Add to the series playlist and to the "All Episodes" playlist.
- End screen: subscribe element + one specific next video (the most-related previous episode) + the series playlist.
- Pinned comment: a one-line extra fact or an honest "what I couldn't fit in" plus a question that invites replies. Post it immediately after publishing — early comment activity is worth having.
- Set the altered/synthetic content disclosure honestly (see `compliance-and-safety.md`).

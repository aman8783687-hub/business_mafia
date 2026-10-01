# Research and fact-checking

A money channel lives or dies on its numbers. One confidently wrong figure ("मालिक को ₹50 मिलते हैं") becomes the top comment forever.

## Process

1. **Frame the myth.** Write the one-sentence belief the video breaks ("पंप खोल लो, बैठे-बैठे नोट गिनो") and the one number that breaks it. Research to test it, not to decorate it.
2. **Gather 6-12 sources.** Prefer: company filings and annual reports, government data and ministry pages (e.g. petroleum ministry, NABARD, MyNeta/ADR affidavit summaries), industry associations, reputable business press, documented interviews with real operators, university and agriculture-department extension pages. Treat blogs, AI summaries and other YouTube videos as leads, never sources.
3. **Triangulate every number.** Dealer commissions, margins, costs, EMI ranges, yields and prices need two independent sources. If they disagree, say a range ("तीन से पाँच रुपये") or drop the number.
4. **Street and village businesses rarely have a published number.** Build the estimate from several documented operator interviews or news features, record each, and say it in the script as an estimate ("अंदाज़न", "लगभग") with a round range. Never present an estimate as a fact.
5. **Watch for traps:** one famous owner's numbers presented as typical; pre-GST or pre-2020 prices; peak-season figures presented as the yearly average; gross revenue presented as profit; subsidies presented as income.
6. **Log everything** to `01_research/sources.md` as: claim -> source -> URL -> confidence (high/medium/low) -> "fact" or "estimate".

## The fact gate

Before the script leaves stage 2, walk it line by line and mark every rupee figure, date, name and "first" claim. Each must map to a row in `sources.md`. A line you cannot source is rewritten as a clearly-labelled estimate with a range, or cut. Plausible-sounding invention is the worst outcome available. `run_episode.py` refuses to start without `01_research/sources.md`.

## Hypothetical characters

रमेश, राजू and शर्मा जी are examples ("मान लीजिए"). Their numbers must still come from `sources.md`.

## Corrections policy

If an error ships: the operator pins a correction comment within 24 hours and logs it in `reports/changelog.md`; if the error is central to the video's claim, unlist or replace the video.

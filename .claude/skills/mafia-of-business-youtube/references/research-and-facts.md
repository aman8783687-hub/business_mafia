# Research and fact-checking

A channel about history and technology lives or dies on being right. One confidently stated wrong date in the first month becomes the top comment forever.

## Process

1. **Frame the question.** Before searching, write the one-sentence thesis of the video. Research to test it, not to decorate it.
2. **Gather 6–12 sources.** Prefer: university and museum pages, primary documents, patent records, IEEE/ACM/Nature-tier writeups, established encyclopaedias, well-sourced books. Treat blog posts, AI summaries, and other YouTube videos as leads, never as sources.
3. **Triangulate every number.** Dates of invention, "firsts", casualty figures, costs, speeds, and adoption statistics need two independent sources. If two sources disagree, either say so in the script ("estimates range from…") or drop the number.
4. **Watch for the classic traps** of invention history:
   - Lone-genius myths. Almost nothing was invented by one person in one moment; the honest story is usually better anyway.
   - "First" claims that depend on definition — say what definition you're using.
   - Apocryphal anecdotes (falling apples, bathtubs, garages). Verify or label as legend.
   - Retroactive numbers quoted without inflation adjustment.
   - Quotes attributed to famous people that they never said. If you cannot source a quote to a primary document, do not use it.
5. **Log everything** to `01_research/sources.md` as: claim → source → URL → confidence (high/medium/low).
6. **Collect visual references** in the same pass: reference photos of the people, machines, buildings and documents you'll need in stages 4 and 5. Note the licence of each image (see `compliance-and-safety.md`).

## The fact gate

Before the script leaves stage 2, walk the script line by line and mark every factual assertion. Each one must map to a row in `sources.md`. Any line that cannot be sourced gets rewritten into something you can support, or cut. Never let a gap be filled by a plausible-sounding invention — plausible and wrong is the worst outcome available.

## Handling uncertainty on camera

Uncertainty is content, not weakness. "We don't actually know who did it first, and that argument is still going" is a more interesting line than a false certainty. Give the viewer the honest state of the evidence.

## Corrections policy

If an error ships:
- Pin a correction comment within 24 hours of noticing.
- Add a correction card in the next video's description.
- If the error is central to the video's claim, unlist or replace the video and log it in `reports/changelog.md`.

Handling this openly costs one comment; hiding it costs the channel's credibility.

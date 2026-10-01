# Script formula

The script is the video. Animation quality raises a good script; it cannot rescue a boring one. Assume the viewer's thumb is hovering over the back button for the entire runtime and write accordingly.

## Specs

- **Length:** 700–950 words for a 5–7 minute video at ~140 words/minute. Count words, then check the estimate against the actual voiceover duration after stage 3.
- **Sentences:** short. Average 12–16 words. Vary rhythm — a three-word sentence after a long one lands like a drumbeat.
- **Voice:** second person and present tense wherever possible. "You're standing in a workshop in 1947" beats "In 1947, researchers were working…"
- **No filler:** delete "in this video we will", "without further ado", "let's dive in", "as we all know". They cost you the exact seconds you can least afford.
- **Story over lecture:** this is a story channel, not an educational channel. Favor the people, the rivalry, the accident, the stakes — over explaining how something works. If a sentence reads like a textbook ("this works because…", "the process involves…"), rewrite it as something that happened to someone.

## Structure

### 1. Hook (0:00–0:15) — the most important 15 seconds you will write
No logo, no intro, no greeting, and no intro sting or outro card in the edit: the video starts at 0:00 with the hook. **The very first sentence is a question** (the viewer's own question, or the one the story answers). Patterns that work, each phrased so it opens on or quickly lands on that question:

- **The absurd fact:** "This lump of glass and metal was more valuable than the entire building it sat in."
- **The stakes flip:** "In 1943, this machine was so secret that the men building it weren't told what it did."
- **The reframe question:** "Why did it take humanity 5,000 years to put wheels on a suitcase?"
- **The impossible before/after:** "Before this, a message took three weeks to cross the Atlantic. After it: seven minutes."

Then a one-line promise of the journey — what the viewer will understand by the end — and go. Nothing interrupts the hook: the setup follows straight on.

### 2. Setup (0:15–1:15)
Establish the world before the invention. Make the problem *felt*, not stated: the cost, the danger, the daily annoyance. The viewer should want the solution before it arrives.

### 3. Escalation (1:15–4:00)
Three to five beats, each ending in a small turn. Structure each beat as: attempt → obstacle → consequence. This is where you deploy:
- **Concrete comparisons** — not "very fast", but "faster than a message could physically travel for the previous 3,000 years."
- **Human moments** — the rivalry, the stubbornness, the accident. These carry the video, not the mechanics.
- **The mechanism, kept light** — if the story needs *how* it worked, land it in one sentence with a visual metaphor a stickman can act out, then move straight back to what happened next. It's seasoning, not a required checkbox — never let an explanation run long enough to feel like class.

### 4. The turn (4:00–5:15)
The consequence nobody expected. The second-order effect, the misuse, the industry it accidentally killed, the problem it created. This is the section that earns shares.

### 5. Landing (last 30–45 seconds)
Tie back to the hook's exact image or phrase — closing the loop is what makes a video feel *finished*. End on a forward-looking thought, then a specific next-video pointer ("the machine that replaced it is the story of the next video") rather than a generic "like and subscribe". Ask for the subscribe once, in one sentence, and make it about the series, not about you.

## The mystery structure (default for this channel)

Layer this over the five sections above. It is what keeps a 6-minute story watchable:

- **HOOK:** open on the *question* (rule above), then promise the ending honestly: "you'll know what the record proves, what is legend, and what nobody can answer". That promise is the main reason to stay.
- **Open loops:** plant two or three (the wildest theory is coming; one detail still bothers people) and close each one before the end.
- **Theory, then check:** for every theory, one beat that states it and one or two beats that test it. Never state a theory and leave it standing, and never debunk one without first giving it a fair hearing.
- **Sourced tone:** quote documents word for word only when the wording is in `sources.md`. Say "we could not trace it to any record" instead of repeating an unsourced anecdote as fact.
- **The twist near the end:** the real ending is usually more interesting than the myth (something that did arrive by another route, or the narrow gap that is still unexplained).
- **Close the loop on the hook question,** then invite one specific comment ("which theory did you believe before today?") and point to the next episode.

## Retention discipline

- Mark your script at 30-second intervals. At each mark, ask: *what changed in the last 30 seconds?* If the answer is "nothing, I was explaining", inject a turn, a question, a jolt of scale, or a hard cut to a new visual idea.
- Open loops early, close them late: "we'll come back to that mistake" — and actually come back.
- Never stack more than two abstract sentences without an image the animation can literally show. If you can't picture the stickman doing it, rewrite it.
- Kill the second-best example. Two great examples beat four decent ones.

## Format of `02_script/script.md`

Write the script as numbered narration beats so the shotlist and audio chunks map cleanly:

```markdown
# [Working title]
Target runtime: 6:00

[COLD_OPEN]
1. This lump of glass and metal was worth more than the building around it.
2. And in nineteen forty-seven, almost nobody knew it existed.

[SETUP]
3. ...

[RISING_MYSTERY]
...

[CLIMAX_REVEAL]
...

[AFTERMATH]
...
```

The five tags are fixed: `COLD_OPEN` is the hook (0:00-0:15), `SETUP` the setup, `RISING_MYSTERY` the escalation (the bulk of the video), `CLIMAX_REVEAL` the turn, `AFTERMATH` the landing. `generate_narration_chunks.py` uses them to pick the voice preset and the ambience planner uses them to place the reveal sting.

Each numbered line is 1–3 sentences — this is also the unit you will hand to the TTS in stage 3, so keep every line comfortably under 30 seconds when read aloud (roughly 60–70 words maximum, ideally 25–45).

Alongside the script, write `02_script/shotlist.json`: for each numbered beat, a one-line visual description. Do this while the writing is fresh — it's the bridge to stage 5. This is a **draft** — stage 5 rebuilds it into the authoritative `05_scenes/shotlist.json` once real beat timing exists; don't expect this early version to still be read by later scripts.

## Read-back test

Read the finished script aloud at speaking pace before generating audio. Three things you're listening for: tongue-twisters the TTS will mangle, sentences that need a breath in the middle (split them), and any paragraph where your own attention drifts (cut it).

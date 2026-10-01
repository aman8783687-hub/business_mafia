# Topic strategy

## What belongs on this channel

One innovation per video, told as a story with stakes. The subject can be 5,000 years old or five months old. The test: *can I explain why the world was different after this thing existed?* If the answer is only "it's cool tech", the topic isn't ready — find the tension.

## The mystery lens (channel focus since 2026-09-26)

The channel is about the **story behind the innovation**, and above all the mysteries, legends and conspiracy theories that grew around it. Every topic is scored for that first: *what is the unanswered question, the disputed claim, the thing that went missing?* Tesla's tower, the seized papers and the death ray are the model: a real innovation, a real gap in the record, a set of theories people argue about.

Each mystery episode does three things, in this order:

1. **Tell the theory fairly.** State it the way believers do, in its strongest documented form.
2. **Check it against the record.** What do primary documents, patents and named historians actually show? Say plainly which parts survive and which do not.
3. **Leave the honest open question.** Something narrow and real that nobody can answer yet. This is what makes the mystery a mystery rather than a takedown.

Good mystery topics: vanished or seized papers and prototypes, disputed "firsts", inventors who were ruined or erased, projects that stopped without a clear reason, famous "suppressed technology" claims, unexplained failures and disasters. Rank them alongside the categories below; the category still labels the video.

Guardrails: no invented quotes, and no "the government hid it" claims without a document. A theory without evidence is presented as a theory, in the narration, with the evidence stated. Nothing is ever presented as a real recording of a real event. See `compliance-and-safety.md`.

## Categories

Every bank entry carries a `category` (required by `state_db.py topic-add`). Rotate them so the channel never sticks to one theme, and run an occasional 3-5 video arc when a chain of inventions tells a bigger story (vacuum tube -> transistor -> chip -> GPU -> AI).

1. **Who Really Invented It**: disputed "firsts", simultaneous inventions, patent fights.
2. **Lost & Disputed Inventions**: lost techniques, shelved prototypes, inventors erased from the record.
3. **Disasters That Changed Engineering**: failures and the investigations that followed.
4. **Conspiracy, Checked**: a famous legend told fairly, then tested against documents.
5. **Hidden Infrastructure**: the systems nobody notices (cables, grids, water, code).
6. **Unsolved Technical Mysteries**: devices and methods we still cannot fully explain.

Include history from outside the US and Europe (India, the Islamic world, China): the channel's operator is in India and the audience is global.

## Scoring a candidate topic

Score 1–10 on each, average them, and queue anything ≥ 7.0:

- **Demand** — are people already searching for or watching this? Check YouTube search suggestions, competing videos' view counts, and whether existing coverage is old or bad.
- **Story** — is there a conflict, a wrong turn, a rivalry, a moment of "and then everything changed"?
- **Visual** — can stickmen and simple diagrams carry it? Abstract software concepts are harder than physical machines; find the metaphor before committing.
- **Freshness** — is there an angle nobody else is using? "The invention of X" is crowded; "the mistake that gave us X" is not.
- **Fit** — does it sound like a RedHat Engineer video?

## Gap-finding routine (run weekly)

1. Search YouTube for your next 10 candidate topics. Note the top 3 videos each: views, age, length, thumbnail style, and what they *miss*.
2. Look for topics where the best existing video is over 3 years old or under 100k views on a high-demand term — that's an opening.
3. Read comments on competitors' videos for "I still don't understand…" — those become your hooks.
4. Refill the bank so it never drops below 30 queued topics.

## Seed bank

`seed/topic_bank.seed.json` holds the starting queue (27 topics, one or two lines each: `topic`, `category`, `setting`, `angle`, `visual_hooks`, `score`). The seed only fills an empty database; the live bank is whatever `python3 scripts/state_db.py topics queued` shows.

**Already published, never repeat inside 120 days:** the transistor (three videos), the shipping container, the elevator brake, the camera sensor, the printing press, the barcode (two), the ATM, the QR code, ARPANET, the transformer, the water mill, the mechanical clock, Wardenclyffe/Tesla. Treat these as used even if the bank does not list them. The 2026-09-28 to 09-30 Indian-history mystery episodes are off-brand now and are not part of this channel's record.

## Refilling the bank

When `topics-count` shows fewer than 8 queued, add topics until it is back above 15, with `python3 scripts/state_db.py topic-add` (JSON list on stdin). Each needs `topic`, `category`, `setting`, `angle`, `visual_hooks`, `score`. Balance the categories; score by the rubric above; queue only >= 7.0 (seed entries are 7-9). Every angle must describe something real and documented, with the open question named. On a first run against the old Indian-history bank, reject every queued topic that is not a technology story: `topic-reject "<name>" "off-focus: not a technology story"`.

## Rules

- No topic repeats within 120 days.
- If a video badly underperforms, note *why* in `reports/changelog.md` — was it the topic or the packaging? Don't retire a good topic for a bad title's sake.
- When a topic overperforms, immediately queue a sibling topic in the same category and a follow-up angle within 10 days.

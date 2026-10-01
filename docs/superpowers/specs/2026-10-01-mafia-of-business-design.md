# Mafia of Business -- pipeline design

Date: 2026-10-01
Status: draft, awaiting operator review

## 1. Goal

A GitHub Actions pipeline that makes one **Hindi** YouTube video per run for
the new channel **Mafia of Business** and uploads it to Content Lab, where the
operator downloads it and posts by hand. It is a fork of the RedHat Engineer
pipeline in `../imagine_error_gh_action/`, which stays untouched.

**What the operator asked for**

- Hindi-native channel, India-first audience.
- Topic: how everyday businesses and people Indians know actually make
  money ("restaurant wala kaise kamata hai", gym owner, politician, ...),
  told as a story. No math lecture, no technical detail.
- Long-form 16:9, **3-5 minutes, never over 5:00**.
- Copy the existing pipeline and optimize it for this channel.
- Optimize for YouTube SEO and virality.

**Success criteria**

1. `./make-video` (local) and the workflow (CI) each produce one finished
   Hindi episode: 1920x1080, 180-300 s, Hindi narration, burned-in
   Devanagari captions, a Devanagari thumbnail, and Hindi/Hinglish metadata.
2. The upload lands in Content Lab under the Mafia of Business section.
3. The episode's media is deleted after a confirmed upload, like RedHat.
4. The test suite passes, including new tests for the 5-minute cap, the Hindi
   voice and Devanagari caption chunking.
5. One real end-to-end local run renders correctly. Devanagari conjuncts
   (क्ष, त्र, श्र, matras) are checked by eye in the captions and thumbnail.

## 2. Approach

Fork, don't rebuild. The RedHat pipeline already works end to end: an
opencode agent writes the content, Python scripts produce it, MongoDB holds
the state, and Content Lab receives the upload. The changes are confined to
content rules (skill and references), config (`channel_state.json`), and the
scripts that care about language, length and branding.

Rejected alternatives:
- **Shared library with RedHat** (one codebase, two channel configs): cleaner
  in theory, but it couples two live channels. A fix for one could break the
  other. Not worth it for two channels.
- **New visual style** (option B in brainstorming): the operator chose A.

## 3. Layout and naming

New sibling folder `kaggle-experiment/mafia_of_business_gh_action/`, its own
git repo (to be pushed to a new GitHub repo by the operator).

| RedHat | Mafia of Business |
|---|---|
| `ImagineError/` (working dir) | `MafiaOfBusiness/` |
| `.claude/skills/redhat-engineer-youtube/` | `.claude/skills/mafia-of-business-youtube/` |
| `.github/workflows/redhat-engineer.yml` | `.github/workflows/mafia-of-business.yml` |
| MongoDB db `imagine_error_pipeline` | `mafia_of_business_pipeline` (`MONGODB_DB` still overrides) |
| Content Lab `PROJECT = "redhat-engineer"` | `"mafia-of-business"`, `CHANNEL_TAG = "Mafia of Business"` |
| `IMAGINE_ERROR_SLOT` env var | `MOB_SLOT` |
| output `redhat-engineer-<slug>-episode.mp4` | `mafia-of-business-<slug>-episode.mp4` |

Not copied: `.venv/`, `.pytest_cache/`, `__pycache__/`, `.scratch/`,
`episodes/*`, `.superpowers/`, old `docs/superpowers/` files, `.env` (the
operator copies their own; same keys). The RedHat `reports/changelog.md` and
`experiments.md` start fresh, with one entry noting the fork.

Same secrets as RedHat (`CONTENT_LAB_URL`, `CONTENT_LAB_API_KEY`,
`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `MONGODB_URI`).

## 4. Content design

### 4.1 Topics -- "Kaise kamata hai?"

Everyday people and businesses every Indian has met. Starter bank (at least
30 entries, by category):

- **Street and local:** chai tapri, pani puri wala, dhaba, kirana store,
  sabzi mandi wholesaler, auto/e-rickshaw driver, dabbawala, chhole bhature
  stall.
- **Small business:** restaurant, cloud kitchen, gym, salon, tuition and
  coaching centre, PG/hostel owner, mobile repair shop, sweet shop (mithai).
- **Big-ticket:** wedding planner, tent house and DJ, jeweller, real-estate
  broker, petrol pump, cinema hall/multiplex, private school, hospital.
- **Systems Indians wonder about:** politician (legal income only, see 4.4),
  toll plaza, cricket team (IPL franchise), railway vendor contracts,
  temple trusts (respectful, documented only), YouTuber/influencer.
- **Famous-brand money stories:** Haldiram's, Amul, Zomato/Swiggy
  commission, Dmart, Maggi, Parle-G. Company-level only, no attacks on
  living founders.

Topic score (agent fills it when adding to the bank): relatability (does
every Indian know this person?), the money surprise (is there a "wait,
really?" fact?), search demand (do people type "X kitna kamata hai"?), and
visual potential (can a stickman act it out?).

### 4.2 Story structure (replaces the mystery structure)

Five sections, same mechanism as RedHat's (they drive voice presets, captions
and ambience). New tags:

| Tag | Time | Job |
|---|---|---|
| `[HOOK]` | 0:00-0:20 | First sentence is a question or a shocking rupee fact ("एक कप चाय दस रुपये की... पर उसमें मुनाफ़ा कितना?"). One-line promise: "आज आप जानेंगे असली खेल क्या है." |
| `[DUNIYA]` | 0:20-1:00 | The world: who this person is, the day they live, what everyone *thinks* they earn. |
| `[KHEL]` | 1:00-3:00 | The game: 3-4 money streams, each as a small scene (a customer, a supplier, a deal). The bulk. |
| `[RAAZ]` | 3:00-3:45 | The secret trick: the one non-obvious move that makes the real money (gym memberships people never use, chai's 70% margin, the tent-house's rental reuse). This is what gets shared. |
| `[SABAK]` | last 20-40 s | The takeaway, a loop back to the hook's image, one specific comment question, next-episode pointer. |

Rules:
- Story voice, second person, present tense: "आप सुबह पाँच बजे दुकान खोलते हैं..."
- **No math.** At most one or two simple rupee figures per section, said the
  way people talk ("दस रुपये की चाय, लागत तीन रुपये"). No percentages
  stacked, no formulas, no tables.
- Undocumented figures are labeled as estimates ("अंदाज़न", "लगभग") and
  given as a round range. Never an invented exact figure.
- Conversational Hindi, not shuddh/textbook Hindi. Common English business
  words stay in English and in Devanagari script (प्रॉफ़िट, मार्जिन,
  कस्टमर) because that is how viewers say them.
- Script in Devanagari only. Numbers written as words for the TTS
  ("दस हज़ार", not "10,000"), so the voice reads them naturally.

### 4.3 Length

- Target 240 s (4:00), allowed 180-300 s, **hard cap 300 s**.
- Word budget: about 520-650 Hindi words. edge-tts Hindi speed is
  calibrated in the first real run and the number written into
  `channel_state.json` `format.words_per_minute`.
- `stitch_audio.py` (after stitching) fails the stage with a clear message if
  the narration exceeds 300 s, or falls under 180 s. The fix is a shorter
  script, never a faster voice. `assemble_episode.py` re-checks the final
  video duration before upload.

### 4.4 Compliance additions

On top of RedHat's `compliance-and-safety.md`:
- **Politicians and officials:** only legal, documented income (salary,
  allowances, pension, declared assets in public election affidavits, and
  ADR-type aggregate reports). No named living person accused of anything.
  Corruption is discussed only as reported, sourced, aggregate facts, called
  "आरोप" (allegation) where that is what it is.
- **"Mafia" is a metaphor.** The channel name means "insider who knows the
  game". No glorifying actual crime, no how-to for fraud, tax evasion or
  adulteration. A scam can be *explained* so viewers protect themselves.
- **Brands:** company-level facts from annual reports and press. No claims
  that a named company cheats customers unless a court or regulator found so,
  and it is cited.
- **Religion and caste:** never a business angle on caste. Temple-trust
  episodes are respectful and documented only.

## 5. Production design

### 5.1 Voice

- edge-tts `hi-IN-MadhurNeural` (male, Hindi). Fallback `hi-IN-SwaraNeural`
  if Madhur fails a run. Locked in `channel_state.json`.
- Section presets keyed by the new tags: `hook` slow and weighty, `duniya`
  neutral, `khel` faster and energetic, `raaz` slower with weight, `sabak`
  calm. Same mechanism as RedHat (rate/volume/pitch per section).
- `generate_narration_chunks.py`'s section regex accepts the new tags.
- Word boundaries: edge-tts WordBoundary events come back for Hindi. The
  caption builder must handle Devanagari tokens and punctuation (`।`).

### 5.2 Visuals -- the boss stickman

- Same whiteboard-marker style and FLUX.2 klein reference-image flow.
- New host: the same stickman, **black fedora with a gold band**, a thin
  black suit outline and a gold tie, two dot eyes, no mouth. Colours: black,
  white, gold (`#D4A017`) only. Money props are gold (coins, notes, ₹ bags).
- New reference image `brand/host/host-reference-clean.jpeg` is made from the
  RedHat one with FLUX's reference-edit (swap hat and add suit), and the
  operator approves it before any episode is generated. The style
  reference images from RedHat are dropped.
- Indian settings in prompts (chai stall, dhaba, mandi, auto, wedding
  tent) are described in simple props so the marker style holds.
- Scene holds 5-7 s (shorter than RedHat's 6-10) for pace in a 4-minute
  video: about 35-50 beats.
- No on-image text (unchanged). FLUX cannot draw Devanagari reliably.

### 5.3 Captions

- Font: **Noto Sans Devanagari Bold** (installed locally; CI installs
  `fonts-noto-core`). libass with HarfBuzz shapes conjuncts.
- Highlight colour gold (`&H0017A0D4` in ASS byte order), white text, black
  outline.
- Chunking: 2-4 words per caption (Hindi words are short, but conjunct-heavy
  lines get wide). A caption never splits inside a word.

### 5.4 Ambience

Same engine, no music. Keyword cues retuned to Hindi stems in Devanagari:
- coin/cash sound for पैसा, रुपये, कमाई, मुनाफ़ा, प्रॉफ़िट (new synthesized
  `coin_clink.wav` and `cash_register.wav`);
- sizzle/fire for चाय, तंदूर, आग, खाना; crowd murmur for ग्राहक, भीड़,
  बाज़ार; paper for हिसाब, बिल, नोट.
- `reveal_sting` on `[RAAZ]` beats (replaces `climax_reveal`).

### 5.5 Thumbnail

`make_thumbnail.py` changes:
- Devanagari text with Noto Sans Devanagari Black/Bold, huge, white fill and
  thick black outline. The accent word, usually a rupee figure, in gold.
- Gold frame (replaces red).
- The rupee figure is the thumbnail's hook ("₹40 लाख?", "चाय में 70%?").
  Text 2-4 words, not a title repeat.
- Legibility test at 210x118 px kept.

## 6. YouTube SEO and virality

Ground rule: no tricks that lie. Every number in a thumbnail or title is
from `sources.md` or labeled as an estimate in the video. Clickbait that
the video doesn't pay off kills retention, and retention is what YouTube
rewards.

### 6.1 Title (written by the agent, `metadata.json`)

- **Hybrid script:** Devanagari Hindi plus the English/Hinglish search
  keyword, because Indian viewers search in Roman Hinglish ("gym owner
  kitna kamata hai", "restaurant business profit").
  Example: `Restaurant वाले असल में कैसे कमाते हैं? | Business Model in Hindi`
- 45-70 characters; the keyword in the first half.
- Formulas: "X असल में कैसे कमाता है?", "X का असली खेल", "₹N का X
  business -- सच क्या है?", "X आपको कैसे बेवकूफ़ बनाता है (legally)".
- The agent writes three candidates and keeps the rejected two in
  `metadata.json` `title_alternates` for the operator's A/B Test & Compare.

### 6.2 Description

- First 150 characters: the hook in Hindi plus the Hinglish search phrase
  (shown in search results and suggested-video snippets).
- Chapters with Hindi labels (first at 0:00, at least four, from
  `timings.json`). Chapters show up in Google search as key moments.
- Sources, then a channel line, then 3 hashtags:
  `#MafiaOfBusiness #BusinessModel #<topic>`.

### 6.3 Tags and keywords

- 10-15 tags mixing Hindi, Hinglish and English variants of the main query
  ("chai wala income", "चाय वाला कितना कमाता है", "chai business profit"),
  plus series terms ("business model hindi", "how they make money hindi").
- A new `keywords` field in `topic.json`: the 3-5 query phrases the episode
  is built around. The script's hook and the title both use the main one.

### 6.4 Retention tricks (in the script formula)

- **First 5 seconds:** a rupee shock or a "you've been paying for this"
  line. No greeting, no channel intro.
- **Open loop:** the `[RAAZ]` secret is teased in the hook ("और आख़िर में
  वो एक trick, जिससे असली पैसा बनता है") and paid off at about 75%. This
  holds viewers to the end.
- **Pattern interrupt every 20-30 s:** a new scene, a new character, a
  question to the viewer, a sound cue. Enforced by the 5-7 s scene holds and
  a script check at 30-second marks.
- **Relatability:** "आपने भी देखा होगा..." moments that put the viewer in
  the shop.
- **Comment prompt:** one specific question in `[SABAK]` ("आपके शहर में
  एक कप चाय कितने की है?"). Specific questions get answers; comments boost
  distribution.
- **Series hook:** each episode ends naming the next profession ("अगली बार:
  gym वाले का असली खेल"), and the agent picks that topic next.

### 6.5 Operator package (attached as run artifact)

`metadata.json` also gets:
- `pinned_comment`: a bonus fact plus a question, in Hindi.
- `title_alternates`: the two rejected titles.
- `community_post`: a one-line poll for the YouTube community tab ("चाय
  वाला महीने में कितना कमाता है? A) 15k B) 50k C) 1 लाख+").
- `shorts_hook`: the hook's timestamp range (start/end seconds) so the
  operator can cut a Short by hand.

README "posting checklist" for the operator: post 6-9 PM IST; default audio
language Hindi; upload the Devanagari `.srt`; add to the "Kaise Kamata Hai"
playlist; pin the comment within minutes of posting; publish the community
poll a day before; turn off auto-dubbing.

## 7. Error handling

Inherited from RedHat: idempotent stages, `pending_episodes.py` resume,
`run_cycle.sh` retries (default 4), the Cloudflare quota stop, the upload
retry, cleanup only after a confirmed upload.

New:
- **Length guard** (4.3 above): stage fails with "narration 312 s > 300 s cap:
  trim script" and the agent trims.
- **Hindi guard** (new `scripts/check_script.py`, run by `run_episode.py`
  before audio): the script's narration lines are mostly Devanagari (at
  least 90% of letters), contain no digits (numbers must be words for the
  TTS), and every section tag is present in order. Fails with the offending
  lines.
- **Visual QA gate** adds: boss on-model (black fedora with gold band, no
  mouth), only black/white/gold.

## 8. Testing

- Port the RedHat test suite with renamed paths; all pass.
- New tests:
  - length guard: 299 s passes, 301 s fails, 170 s fails;
  - `check_script.py`: Devanagari ratio, digit rejection, tag order;
  - narration: Hindi voice id and new section presets are picked from
    `channel_state.json`;
  - captions: Devanagari phrases chunk on word boundaries, `।` is handled,
    no caption splits a word;
  - thumbnail: Devanagari text renders with the Noto font (non-empty glyph
    bounding box, no tofu boxes).
- Live checks before calling it done: one Hindi narration chunk generated
  through edge-tts with word boundaries; the reference-image edit for the
  boss stickman (operator approves); one local end-to-end episode with a
  real topic, its captions and thumbnail inspected by eye. The upload step
  is run only after the operator confirms Content Lab accepts the
  `mafia-of-business` project.

## 9. Out of scope (possible later)

- Automatic Shorts generation (9:16 re-crop of the hook). The operator cuts
  Shorts by hand from `shorts_hook` for now.
- Posting to YouTube directly; analytics feedback; a schedule (workflow stays
  `workflow_dispatch` until the operator adds a cron).
- English or other-language versions.

## 10. Open items for the operator

1. Content Lab: does it accept a new `project` value (`mafia-of-business`)
   automatically, or does the section need to be created first?
2. A new GitHub repo for this folder, with the same five secrets.
3. Approve the boss stickman reference image when it is generated.

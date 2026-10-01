# Mafia of Business -- pipeline design

Date: 2026-10-01
Status: approved by operator 2026-10-01

## 1. Goal

A **local** pipeline (`./make-video`) that makes one **Hindi** YouTube video
per run for the new channel **Mafia of Business** and keeps the finished video
on this machine; the operator posts it by hand. State lives in MongoDB. No
Content Lab, no GitHub Actions for now (operator decision, 2026-10-01). It is
a fork of the RedHat Engineer pipeline in `../imagine_error_gh_action/`, which
stays untouched.

**What the operator asked for**

- Hindi-native channel, India-first audience.
- Topic: how everyday businesses and people Indians know actually make
  money ("restaurant wala kaise kamata hai", gym owner, politician, ...),
  told as a story. No math lecture, no technical detail.
- Long-form 16:9, **3-5 minutes, never over 5:00**.
- Copy the existing pipeline and optimize it for this channel.
- Optimize for YouTube SEO and virality.

**Success criteria**

1. `./make-video` produces one finished Hindi episode: 1920x1080,
   180-300 s, Hindi narration, burned-in Devanagari captions, a Devanagari
   thumbnail, and Hindi/Hinglish metadata.
2. The finished package sits in `MafiaOfBusiness/output/<slug>/` (video,
   thumbnail, `.srt`, `metadata.json`, `posting.md`), and MongoDB records the
   episode as `ready`.
3. The episode's intermediate media (audio chunks, scene PNGs, per-beat
   clips) is deleted once the final package is verified; the package is kept.
4. The test suite passes, including new tests for the 5-minute cap, the Hindi
   voice and Devanagari caption chunking.
5. One real end-to-end local run renders correctly. Devanagari conjuncts
   (क्ष, त्र, श्र, matras) are checked by eye in the captions and thumbnail.

## 2. Approach

Fork, don't rebuild. The RedHat pipeline already works end to end: an
opencode agent writes the content, Python scripts produce it, MongoDB holds
the state. The changes are confined to content rules (skill and references),
config (`channel_state.json`), the scripts that care about language, length
and branding, and swapping the Content Lab upload for a local "finalize"
stage.

Rejected alternatives:
- **Shared library with RedHat** (one codebase, two channel configs): cleaner
  in theory, but it couples two live channels. A fix for one could break the
  other. Not worth it for two channels.
- **New visual style** (option B in brainstorming): the operator chose A.

## 3. Layout and naming

New sibling folder `kaggle-experiment/mafia_of_business_gh_action/`, a local
git repo only (no remote for now). The folder name keeps `_gh_action` for
symmetry with the RedHat repo; nothing in it needs GitHub.

| RedHat | Mafia of Business |
|---|---|
| `ImagineError/` (working dir) | `MafiaOfBusiness/` |
| `.claude/skills/redhat-engineer-youtube/` | `.claude/skills/mafia-of-business-youtube/` |
| `.github/workflows/redhat-engineer.yml` | dropped (local only) |
| slot logic (`slot-check`, `IMAGINE_ERROR_SLOT`, `make-video --slot`) | dropped (it only exists for scheduled CI) |
| MongoDB db `imagine_error_pipeline` | `mafia_of_business_pipeline` (`MONGODB_DB` still overrides) |
| `publish_all.py` + `publish_content_lab.py` (upload) | `finalize_episode.py` (local package + Mongo record) |
| output `redhat-engineer-<slug>-episode.mp4` | `mafia-of-business-<slug>.mp4` in `output/<slug>/` |

Not copied: `.venv/`, `.pytest_cache/`, `__pycache__/`, `.scratch/`,
`episodes/*`, `.superpowers/`, old `docs/superpowers/` files, the GitHub
workflow, the Content Lab scripts and their tests, the raphael fallback
backend (its cookie is captcha-blocked). The RedHat `reports/changelog.md`
and `experiments.md` start fresh, with one entry noting the fork.

`.env` needs only `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` and
`MONGODB_URI` (copied from the RedHat `.env`; `.env` stays gitignored).
`output/` and `episodes/*/` are gitignored.

### 3.1 The finalize stage (replaces the upload)

`run_episode.py` runs audio, scenes, assembly and thumbnail as before, then
`finalize_episode.py <slug>`:

1. Verifies the final mp4 (ffprobe: 1920x1080, has audio, duration 180-300 s),
   the thumbnail and `metadata.json`.
2. Copies them, plus `captions.srt`, into `output/<slug>/` and writes
   `posting.md` there: title, alternates, description, tags, pinned comment,
   community poll, Shorts hook range and the posting checklist, ready to paste
   into YouTube Studio.
3. Records the episode in MongoDB (`episodes` collection: slug, title,
   duration, output path, `status: "ready"`, timestamps). Idempotent by slug.
4. Writes `08_publish/finalize_log.json` (`status: ok`).
5. Only then deletes the intermediates (`03_audio/`, `05_scenes/`,
   `07_edit/`), as `cleanup_episode.py` did.

DONE MEANS (cycle prompt): `pending_episodes.py` exits 0 and this episode's
`finalize_log.json` shows `ok`. `run_cycle.sh` counts finalized episodes
instead of uploads. The operator marks an episode `posted` by hand later with
`state_db.py episode-posted <slug> <youtube-url>` (new subcommand), which
lets the agent link the previous episode in descriptions.

### 3.2 Shared Cloudflare quota

This pipeline uses the same Cloudflare account as RedHat, and the free tier
is 10,000 neurons a day, shared. A ~45-beat episode can use most of a day's
quota (on 2026-10-01 the quota was already spent by RedHat before the first
Mafia of Business image). Consequences:
- Resolved: this channel has its own Cloudflare account (see section 10),
  so it no longer competes with RedHat.
- `generate_scenes.py`'s existing quota stop plus skip-finished-beats means a
  stopped run resumes the next day with `./make-video`.

## 4. Content design

### 4.1 Topics -- "Kaise kamata hai?"

Revised 2026-10-01 from the operator's competitor research (Money Games
@MoneyGames_YT, Money Code @moneycode_mc, both started Aug-Sep 2026). What
wins there: **boring, hyper-local, cash businesses from Bharat**, where
everyone has a guess and almost nobody has a good video (Money Code: petrol
pump 720K views = 65x its average, dhaba 62K, kirana 44K; Money Games: dumper
business 241K, poultry 69K, mushroom 60K, transport 42K). What flops:
abstract or distant topics (Money Code: UPI 673, IPL 688, coaching 809,
luxury 903, cashback 918, railways 1.7K, black money 2.1K).

So the bank is built from six verticals (each is also a YouTube playlist):

- **Farming & Pashu:** poultry, mushroom, fish farm, dairy, goat farm,
  bee-keeping.
- **Transport & Heavy Vehicles:** dumper/tipper, truck owner, JCB rental,
  tractor rental, school van, auto/e-rickshaw.
- **Khana & Street Food:** chai tapri, momo cart, pani puri, dhaba, juice
  stall, sweet shop, restaurant.
- **Dukaan & Retail:** kirana, petrol pump, medical store, mobile recharge
  shop, hardware store, jeweller.
- **Services:** barber/salon, laundry, gym, tent house & DJ, mobile repair,
  PG owner, wedding planner.
- **Recycling & Small Industry:** kabadiwala, plastic recycling, cold storage,
  flour mill (chakki), brick kiln.

Plus, sparingly, the **politician** episode the operator asked for (legal
income only, 4.4), scored lower and scheduled after the channel has traction.
Dropped from the starter bank: IPL, railways, coaching, toll plaza, private
school, YouTuber and famous-brand stories (abstract or distant, per the data).

Topic score (agent fills it when adding to the bank): relatability (does
every Indian know this business?), the myth gap (is there a "sunne me aasan
lagta hai" belief the hisaab overturns?), search demand (do people type
"X business profit" / "X kitna kamata hai"?), and visual potential.

### 4.2 Story structure: simple hisaab, told as a story

Operator decision 2026-10-01: the script may include **simple hisaab as
story** -- named costs and one rupee number per beat, carried by a character
("रमेश हर महीने चालीस हज़ार की EMI भरता है"). Still no formulas, no stacked
percentages, no tables. This replaces the earlier "almost no numbers" rule;
both competitor channels show the money breakdown *is* the hook.

Five sections (they drive voice presets, captions and ambience):

| Tag | Time | Job |
|---|---|---|
| `[HOOK]` | 0:00-0:20 | **Myth, then one number shock.** "पेट्रोल पंप खोल लो, बैठे-बैठे नोट गिनो... सुनने में कितना आसान लगता है ना?" then "पर पंचानवे रुपये के पेट्रोल में मालिक को मिलते हैं सिर्फ़ साढ़े चार।" Then tease the [RAAZ]. |
| `[DUNIYA]` | 0:20-1:00 | **The character and the setup.** A hypothetical owner with a common name (रमेश, राजू, शर्मा जी), introduced as an example ("मान लीजिए..."): what he invests, where, why he started. |
| `[KHEL]` | 1:00-3:00 | **पैसा कहाँ बनता है, कहाँ डूबता है.** The money in, then the leaks: EMI, rent, staff, bijli, diesel, wastage, udhaar. One rupee number per beat. One comparison (highway vs gaon, small vs big). |
| `[RAAZ]` | 3:00-3:45 | **The hero product or the hidden twist**: the dal that carries the dhaba, the ₹1.5 papad sold for ₹10, the tanker that must be paid first, the bad month that sinks a dumper owner. What gets shared. |
| `[SABAK]` | last 20-40 s | **Two or three simple rules** (menu chhota rakho, emergency fund, repeat customer > margin), the payoff line ("ये धंधा पेट्रोल का नहीं, कैश-फ़्लो और भरोसे का है"), one specific comment question, next-episode pointer. |

Rules:
- Story voice, second person, present tense: "आप सुबह पाँच बजे दुकान खोलते हैं..."
- **Hisaab, not math:** one rupee figure per beat, said the way people talk
  ("दस रुपये की चाय, लागत तीन रुपये"). No formulas, no tables, no stacked
  percentages. If a number needs a calculation to understand, replace it
  with a comparison.
- Undocumented figures are labeled as estimates ("अंदाज़न", "लगभग") and
  given as a round range. Never an invented exact figure.
- Conversational Hindi, not shuddh/textbook Hindi. Common English business
  words (EMI, profit, margin, customer) are fine, written in Devanagari
  (ईएमआई, प्रॉफ़िट) so the TTS reads them naturally.
- Script in Devanagari only. Numbers written as words for the TTS
  ("दस हज़ार", not "10,000").

### 4.3 Length

- Target 240 s (4:00), allowed 180-300 s, **hard cap 300 s**.
- Word budget: about 520-650 Hindi words. edge-tts Hindi speed is
  calibrated in the first real run and the number written into
  `channel_state.json` `format.words_per_minute`.
- `stitch_audio.py` (after stitching) fails the stage with a clear message if
  the narration exceeds 300 s, or falls under 180 s. The fix is a shorter
  script, never a faster voice. `assemble_episode.py` re-checks the final
  video duration in `finalize_episode.py`.

### 4.4 Compliance additions

On top of RedHat's `compliance-and-safety.md`:
- **Politicians and officials:** only legal, documented income (salary,
  allowances, pension, declared assets in public election affidavits, and
  ADR-type aggregate reports). No named living person accused of anything.
  Corruption is discussed only as reported, sourced, aggregate facts, called
  "आरोप" (allegation) where that is what it is.
- **Hypothetical characters are labeled.** रमेश/राजू are introduced as an
  example ("मान लीजिए"), never presented as a real person or a real
  interview.
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

- Font: **Noto Sans Devanagari Bold** (installed on this machine;
  `make-video` checks `fc-list` for it and stops with an install hint if
  missing). libass with HarfBuzz shapes conjuncts.
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

### 5.5 Thumbnail -- annotated "hisaab" infographic

Revised 2026-10-01 from the research: Money Code's three winners share one
infographic thumbnail (a shop drawing with 4-5 handwritten money notes and
arrows), and infographics stand out in a Hindi finance feed full of faces.
Our version is our own whiteboard look, not a copy:

- White whiteboard background, gold frame.
- Title band at the top: the series phrase "<X> का हिसाब" (2-4 Devanagari
  words) in big black type, accent word in gold, gold underline.
- Centre: the episode's thumbnail scene (the boss at the business, drawn by
  FLUX with the subject centred and empty space on the left and right).
- 3-4 money annotations from `metadata.json` `thumbnail_annotations`, placed
  left and right of the scene in bold black with gold arrows pointing in
  ("₹4.5/लीटर", "पहले पेमेंट", "लोन EMI", "दाल = हीरो"). Digits are fine
  here; only the narration must use words.
- Same template on every episode, so the channel is recognisable in a
  sidebar.
- Fallbacks: no annotations -> the scene full-bleed with the title (5.5 v1);
  no scene -> the boss on the left.
- Legibility test at 210x118 px kept.

## 6. YouTube SEO and virality

Ground rule: no tricks that lie. Every number in a thumbnail or title is
from `sources.md` or labeled as an estimate in the video. Clickbait that
the video doesn't pay off kills retention, and retention is what YouTube
rewards.

### 6.1 Title (fixed series template)

Both competitors use one title template on every video, so viewers learn
the series. Ours:

`<X> वाला असल में कितना कमाता है? | <X in English> Business Profit in Hindi`

e.g. `पेट्रोल पंप वाला असल में कितना कमाता है? | Petrol Pump Business Profit in Hindi`.
The Devanagari question carries the curiosity; the English half is the
Hinglish search phrase people type. 45-80 characters. The agent writes two
alternates in `metadata.json` `title_alternates` (variations on the
question, same English half) for YouTube's Test & Compare.

### 6.2 Description

- First 150 characters: the myth hook in Hindi plus the search phrase.
- Chapters with Hindi labels (first at 0:00, at least four, from
  `timings.json`).
- **"🔍 आपके सवाल (Your Queries)" block:** 15-20 search phrases people type,
  one per line, mixing Hinglish, Devanagari and English ("petrol pump
  kitna kamata hai", "petrol pump dealer margin", "पेट्रोल पंप कैसे खोलें"
  ...). Money Games uses this block on every video.
- Sources, then a channel line, then 3 hashtags:
  `#MafiaOfBusiness #BusinessModel #<topic>`.

### 6.3 Tags, keywords and playlists

- 15-25 tags (YouTube's 500-character limit is the ceiling) mixing Hindi,
  Hinglish and English variants of the main query plus series terms.
- `topic.json` `keywords`: the 3-5 core phrases; title, hook and the first
  description line all use the main one.
- One playlist per vertical (4.1). `metadata.json` `playlist` names the
  episode's vertical; `posting.md` tells the operator which playlist to add
  it to.

### 6.4 Retention tricks (in the script formula)

- **First 5 seconds:** the myth everyone believes ("सुनने में कितना आसान
  लगता है ना?") and one number that breaks it. No greeting, no channel intro.
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

### 6.5 Operator package (in `output/<slug>/posting.md`)

`metadata.json` also gets:
- `pinned_comment`: a bonus fact plus a question, in Hindi.
- `title_alternates`: the two rejected titles.
- `community_post`: a one-line poll for the YouTube community tab ("चाय
  वाला महीने में कितना कमाता है? A) 15k B) 50k C) 1 लाख+").
- `shorts_hook`: the hook's timestamp range (start/end seconds) so the
  operator can cut a Short by hand.

README "posting checklist" for the operator: post daily if possible (both
competitors grew on one video a day), 6-9 PM IST; default audio
language Hindi; upload the Devanagari `.srt`; add to the episode's vertical playlist; pin the comment within minutes of posting; publish the community
poll a day before; turn off auto-dubbing.

## 7. Error handling

Inherited from RedHat: idempotent stages, `pending_episodes.py` resume,
`run_cycle.sh` retries (default 4), the Cloudflare quota stop, cleanup
only after `finalize_episode.py` reports ok. Finalize is idempotent by slug,
so a re-run never duplicates the Mongo record or the output folder.

New:
- **Length guard** (4.3 above): stage fails with "narration 312 s > 300 s cap:
  trim script" and the agent trims.
- **Hindi guard** (new `scripts/check_script.py`, run by `run_episode.py`
  before audio): the script's narration is at least 90% Devanagari letters
  overall, no beat has more than two Latin-script words (one or two English
  business words are fine, a whole English sentence is not), no beat contains
  digits (numbers must be words for the TTS), and every section tag is
  present in order. Fails with the offending lines.
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
  real topic, its captions and thumbnail inspected by eye, finalized into
  `output/<slug>/` with its Mongo record.

## 9. Out of scope (possible later)

- Automatic Shorts generation (9:16 re-crop of the hook). The operator cuts
  Shorts by hand from `shorts_hook` for now.
- Content Lab upload and GitHub Actions (the RedHat code for both can be
  ported back later if wanted).
- Posting to YouTube directly; analytics feedback; a schedule.
- English or other-language versions.

## 10. Decisions and open items

Decided 2026-10-01: no Content Lab (local `output/` + MongoDB only); no
GitHub repo for now (local git only).

Also decided 2026-10-01:
- Boss stickman: variant 1 of 4 (seed 11, cleanest strokes, closest to the
  RedHat line style), saved as `MafiaOfBusiness/brand/host/host-reference-clean.jpeg`.
- Own Cloudflare account for this channel (own 10,000-neuron daily quota),
  in this repo's `.env`.

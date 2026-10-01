# Character bible

The canonical reference is `brand/host/host-reference-clean.jpeg` (the clean whiteboard stickman on a plain white background, sent with every request). Generation goes through FLUX.2 [klein] on Cloudflare Workers AI (`scripts/generate_scenes.py` with `IMAGE_BACKEND=flux`, the default: `scripts/scenes/flux_orchestrator.py`; see `visuals-and-animation.md`), whose image-editing endpoint conditions every generated scene on that reference image. Expect a strong identity lock, though still not pixel-perfect sameness (see `channel_state.json → style_lock`). A bad scene is fixed by rerolling with `generate_scenes.py --beats N --seed <new>`, not by describing the character differently in the prompt. One real ceiling that IS worth designing around: FLUX.2 klein reliably composes at most 2 distinct characters in a single shot — a 3rd (e.g. host + supporting character + a third figure) collapses to just one rendered subject. Write those beats as shot/reverse-shot pairs instead of trying to fit everyone in one frame (see the poses section below and `visuals-and-animation.md`).

## The host

**Who he is:** curious, smart, calm, confident. An observer and thinker who explains complex things simply and is always learning. He is never smug, never a hype man, never the joke.

**How he looks:**
- Minimalist stick figure: thick black lines, round white head, two simple black dot-oval eyes, no nose, no mouth (expression comes from posture, hands and eyebrows-by-implication).
- The red fedora (`#E60000`) with a black band — the single most important brand element. It is on his head in every shot unless the script explicitly calls for removing it as a story beat.
- Often holding a tablet or notebook — the knowledge-seeker prop.
- Clean black and white body, red only on the hat and occasional accent.

**Canonical poses** (from the sheet — reuse these rather than inventing new ones): Explaining (finger raised), Thinking (arms folded, head tilted), Discovering (magnifying glass), Presenting (arm out to the side toward a diagram), Curious (hand to head, question mark), Building (at a laptop).

Pick the pose that matches the narration's intent, then vary camera distance for rhythm — wide for context, mid for explanation, close for emphasis.

## Style lock

Every scene prompt = **the style suffix from `channel_state.json` + subject description + reference image**. The suffix (keep it verbatim):

> hand-drawn black marker stickman on a clean white whiteboard, thick confident marker strokes, solid red marker fedora with black band, the stickman has exactly two black dot eyes and NO mouth, a neutral calm face, thin single-line stick limbs and a plain stick body with no clothing, no text, no letters, no numbers, one or two simple hand-drawn marker props only, no arrows, lots of empty white space, only red, black and white colors, whiteboard explainer animation look

**2026-09-17 fix:** earlier versions of this suffix asked for "tech doodle icons" (network nodes, chips, clouds) scattered around the character. Operator feedback after the first real episode flagged this as clutter they didn't want. It turned out the icons were coming from the reference image itself, not just the text — `image=` conditioning copies visual elements from whatever photo it's given, and the old reference (a crop of `Main_Character.png`) had those icons baked into its background. Fixed by regenerating `hero_reference.png` as a fresh, plain-background, text-only FLUX.2 generation (no icons to copy) and rewriting the suffix to explicitly forbid them. If clutter reappears in future scenes, check the reference image first, not just the prompt text — a photo's background elements can leak into every generation regardless of what the prompt says.

There is no negative prompt: `Flux2KleinPipeline` (FLUX.2-klein-4B) has no `negative_prompt` parameter. Anything to avoid must be phrased as a positive instruction in the suffix or the scene description instead (e.g. describe "simple/plain background" rather than adding "no clutter" to a negative list that no longer exists).

**2026-09-26 style change:** the look moved from dark-navy flat vector to hand-drawn marker on a white whiteboard (operator's pick from the visual-style experiments, `experiments/visual-style/`, variant `whiteboard-v2`). Scene descriptions may include simple hand-drawn environments (buildings, machines, rails) but should not mention arrows, labels or text. The previous suffix is kept as variant `legacy-navy` in the experiment harness. Close-up descriptions must not say "hat and eyes visible at the top of the frame": every tested style drew a second giant head from that wording.

**Colour discipline:** black, white, two greys, one red (the white whiteboard background is the white; no navy, cream or yellow). If a generated scene introduces a genuinely unauthorised colour, regenerate it. This rule alone does more for brand recognition than anything else.

## Supporting cast: turning real people into RedHat stickmen

When the script features a real person — Einstein, Tesla, Lovelace, Turing, Oppenheimer, Curie, a living founder — follow this exactly:

1. **Find real reference photos first.** 2–3 images, clearly showing the face and typical dress. Save to `01_research/refs/`.
2. **Identify 2–3 signature traits** — the smallest set of features that makes them instantly recognisable. Einstein: the explosive white hair and moustache. Tesla: slicked-back dark hair, thin moustache, high collar. Lovelace: ringlets and a wide period dress silhouette. Turing: side-parted hair, tweed jacket. Curie: pinned-up dark hair, dark high-necked dress. Oppenheimer: the porkpie hat, gaunt frame, cigarette.
3. **Draw them in the channel's style, not the photo's style.** Same stick-figure body, same line weight, same simple dot eyes as the host. Only the signature traits carry the likeness. The result should read as "oh, that's Einstein" from across the room while still obviously belonging to this channel.
4. **Never** produce a realistic or photo-like rendering of a real person. Never put words in a real person's mouth as a quote unless it is a sourced quotation, and attribute it on screen.
5. **Save a character sheet** for each: 3 poses on a white background, saved to `04_characters/<name>.png`, and keep the same 2–3 signature traits in the shotlist description whenever that person appears again, so the same Einstein shows up in every Einstein episode. Recurring, consistent historical characters are a genuine channel signature.
   **Limit:** the pipeline passes one fixed host reference image via `image=` on every beat; there is no per-character reference upload. A supporting character's likeness therefore comes from the shotlist description (2–3 signature traits, same line style), not from a saved sheet. Keep the saved sheet as a text/visual note for later episodes, and never let a scene depend on a likeness the description cannot carry.

Living public figures: same rules, plus keep the portrayal neutral and factual. Nothing that mocks, defames or implies statements they didn't make.

## Objects, machines and diagrams

Machines get the same minimalist treatment: outline only, labelled with clean sans-serif text, red used to highlight the one part currently being discussed. Keep any single diagram to **one idea and at most 5 labels** — if it needs more, it's two scenes.

Scale comparisons are a house speciality: put the stickman next to the object at true relative scale. It's cheap to draw and instantly communicates.

## Consistency checks

Before a scene image is accepted:
1. Hat is present, the right shape, and exactly `#E60000`.
2. Head-to-body proportion matches the sheet.
3. Line weight matches neighbouring scenes.
4. Palette contains no unauthorised colour.
5. Hands have a plausible number of fingers (or are simple line stubs, which is safer — prefer stub hands).
6. No text artifacts in the image; all on-screen text is added in the editor, not generated.

Regenerate rather than accept drift. One off-model scene is a small problem; twenty tolerated off-model scenes is a channel with no visual identity.

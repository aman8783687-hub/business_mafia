# Character bible

## The Boss (host)

- Reference: `brand/host/host-reference-clean.jpeg` (approved 2026-10-01), sent with every FLUX request (thumbnail scene, flux rerolls). The default perchance backend cannot take it: the style text is the only lock, so check every scene against it.
- Look: thin black stick body and limbs, round white head, two black dot eyes, **no mouth**, black fedora with a gold band, thin black suit-jacket outline, small solid gold tie.
- Personality (shown through poses, not faces): calm, knowing, slightly amused -- the insider who explains the game. Leans on counters, points at props, counts coins, tips the hat.
- Never: a mouth, a red hat, coloured clothes beyond the gold tie and band, guns or crime props.

## Other characters

- Plain stickmen (no hat) as customers, shopkeepers, workers, suppliers. Give them one identifying prop: an apron for the chai wala, a dumbbell for the gym trainer, a turban or a sari outline where the story needs it, drawn simply and respectfully.
- At most two characters per shot; write conversations as shot/reverse-shot pairs.

## Style lock

The `image_prompt_suffix` in `channel_state.json` is prepended to every prompt. Black, white and gold only. Money (coins, notes, ₹ bags) is drawn in gold. No text, letters or numbers in the image.

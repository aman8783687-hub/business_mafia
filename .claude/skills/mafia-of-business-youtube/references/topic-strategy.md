# Topic strategy

## Two formats, alternating

- **`kamai`** -- "<X> वाला असल में कितना कमाता है": one business, the full hisaab, ending with how the viewer could start. Everything below about verticals and myths applies.
- **`list`** -- "₹<budget> से शुरू करें ये <N> बिज़नेस": five to seven businesses from these verticals that the viewer can start with that budget. The reference channel's biggest video (261K) has this shape. The budget is the hook: ₹2,000, ₹5,000, ₹10,000, ₹20,000, ₹50,000, or a setting ("गाँव में", "घर से", "नौकरी के साथ").

Never two of the same format in a row; `recent 3` shows the last episodes' formats. Every topic in the bank carries `format`.

## What belongs on this channel

"Kaise kamata hai?" for **boring, hyper-local, cash businesses from Bharat**: the businesses every Indian passes daily, where everyone has a guess and nobody has a good video. The test: is there a myth that simple hisaab overturns, and does the real hisaab make the owner look smart and hardworking? The channel shows the good side of business (`script-formula.md`, "Tone").

Evidence (operator's research, 2026-10-01): comparable channels' breakouts were petrol pump (720K, 65x average), dumper (241K), poultry (69K), dhaba (62K), mushroom (60K), kirana (44K), transport (42K). Abstract or distant topics flopped: UPI 673, IPL 688, coaching 809, luxury 903, cashback 918, railways 1.7K, black money 2.1K. Do not queue apps, finance concepts, sports leagues, luxury or government systems.

## Verticals (the `category` field; each is a YouTube playlist)

1. **Farming & Pashu** -- poultry, mushroom, fish, dairy, goat, bee-keeping.
2. **Transport & Heavy Vehicles** -- dumper/tipper, truck, JCB, tractor rental, school van, e-rickshaw.
3. **Khana & Street Food** -- chai, momo, pani puri, dhaba, juice, sweet shop, restaurant.
4. **Dukaan & Retail** -- kirana, petrol pump, medical store, hardware, jeweller.
5. **Services** -- barber, laundry, gym, tent house, mobile repair, wedding planner.
6. **Recycling & Small Industry** -- kabadiwala, plastic recycling, cold storage, atta chakki, brick kiln.
7. **Neta & System** -- the politician episode only (legal income, `compliance-and-safety.md`); not before episode 10.

Never two episodes in a row from the same vertical. Farming and heavy vehicles drew most of one competitor's views: keep at least one of every three episodes in those two.

## Scoring (1-10 each, average, queue at 7.0+)

- **Relatability** -- does every Indian pass this business?
- **Myth gap** -- is there a belief the hisaab overturns ("छोटा धंधा है", "इसमें क्या कमाई") and a [RAAZ] smart move the owner makes?
- **Search demand** -- do people type "X business profit" / "X kitna kamata hai"? Check YouTube search suggestions.
- **Visual** -- can the boss stickman act it out with one or two props?

## Series chaining

Each [SABAK] names the next topic; pick it next unless it breaks the vertical rotation or compliance.

## Keywords and myth

Every topic carries `keywords` (3-5 query phrases mixing Hinglish, Devanagari and English) and `myth` (the belief the hook breaks, phrased so the answer earns respect: "चाय वाला क्या ही कमाता होगा" rather than "पंप खोलो, बैठे-बैठे नोट गिनो"). Copy both into `topic.json`.

## `list` topics

Same scoring, read for the viewer: Relatability (can someone with this budget do it in a normal mohalla or village?), Myth gap ("इतने कम में क्या शुरू होगा"), Search demand ("10000 me business", "kam paise me business", "gaon me business"), Visual (one prop per idea). Fields as below plus `ideas`: the five to seven candidate businesses. No apps, trading, MLM, reselling schemes or anything needing a big licence.

## Refilling the bank

When `topics-count` shows fewer than 8 queued, add topics with `python3 scripts/state_db.py topic-add` (JSON list on stdin) until more than 15 are queued. Keep about one `list` topic for every `kamai` topic queued. Each item: `topic` (Devanagari: "<X> असल में कितना कमाता है" or "₹<budget> से शुरू करें ये <N> बिज़नेस"), `format` (`kamai` or `list`), `category` (a vertical above; `list` topics use the vertical most of their ideas come from, or "Mixed"), `setting`, `myth`, `angle`, `visual_hooks` (3), `score`, `keywords` (3-5). Never a topic already used.

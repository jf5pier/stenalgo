# Abbreviation rules — questions for round 2 (2026-10-01)

Design choices only you can make. Companion documents:
`PLAN_2026-10-01-abbreviations-complexity.md`,
`PLAN_2026-10-01-abbreviations-algorithm.md`. Each question lists the
context and the trade-off; none require code to answer.

## Precedence & semantics

**Q1 — Brief vs attach when both cover the same tokens.**
"n'est pas" (18.3M) can be a whole-expression brief OR written ne + est + pas
through the "ne…pas" attach rule. Prefer the composition (fewer rules,
productive) or the brief (one memorized fact, no stacking)? This is the
tie-break in Phase 2A's greedy queue.

**Q2 — Reserved keys in play?**
Keys 0/1 (unassigned left-pinky pair, held for a possible third mark, display
"&"/"%") and 10/15 (the * and # marks) are excluded from keypress
enumeration today (`FORBIDDEN_KEYS`, src/affixbinding.py:27). May abbreviation
keypresses use 0/1? Allowing them adds mark-free chords and enlarges the
collision-free space considerably; keeping them out preserves the third-mark
option. What about 10/15 (mixed phoneme+mark chords are legal and costed)?

**Q3 — Circumfix semantics for "ne…pas".**
Always ONE suffix keypress (your sketch: the ne…pas frame collapses onto the
verb's last stroke), or a prefix + suffix key PAIR (two presses, cleaner
algebra, more strokes)? And are variant frames — n'…pas (elision),
ne…plus, ne…jamais — separate rules or slot-forms of one rule in the
FORM_COST sense?

## Budget & pricing

**Q4 — Budget interaction with the 30 affix rules.**
One shared learnability budget (abbreviation rules must then out-marginal
affix rules head-to-head) or a separate expression budget? Related: is a
brief priced like a productive rule (FORM_COST = 100 per extra form) or
higher, as an unanalyzable fact to memorize?

**Q5 — Pricing composability.**
Pure marginal credit (compositions are free wins discovered at simulation
time) or an explicit bonus term rewarding rules whose JOINT use is frequent
("il y a" + ne…pas)? A bonus spends budget on rewarding pairs; marginal
credit may under-select the enabling rule when its solo value is small.

**Q6 — Brief-worthiness threshold.**
Minimum longform length (≥2 strokes? ≥3 for single-word briefs — a
one-syllable word is already one stroke) and a minimum frequency below which
a brief cannot enter the queue at all?

## Shapes

**Q7 — Shadowing.**
May a brief take a shorter word's existing stroke when the frequency ratio is
extreme (pushing the weaker word onto a disambiguation mark), or is reuse of
any live stroke a hard no? Today the collision audit treats every
disambiguated outline as occupied.

**Q8 — Multi-stroke briefs.**
Allowed for long expressions (with `hasBoundaryRisk` checks), or is "brief"
strictly one stroke, with 2-stroke forms handled only by the attach fallback
ladder?

**Q9 — Brief-stroke derivation.**
Restrict candidates to mnemonic derivations from the longform (first-stroke
key unions, skeletons — keySimilarity-labeled for your review), or allow
free chord assignment when it buys frequency? (Measured on the re- prefix:
top-similarity keys can be the WORST performers; the label helps review but
must not select.)

**Q10 — Attach-rule host scope.**
Productive (any host word, like affix rules — maximal coverage, more
exceptions) or restricted to hosts attested in the n-gram data (bounded,
data-backed, smaller wins)?

## Corpus & fallback

**Q11 — Frequency arbiter.**
All-time Google Books counts vs a recent decade window (LexiqueGoogleNgram
carries both). Books skew formal/literary; particle frames like "de la" may
weight differently in contemporary text.

**Q12 — Fallback when the merge fails on a host.**
Standalone attach stroke (the `_newBase` RULE fallback — the writer feels the
impossible chord as an extra stroke) or write the particle out in full
(counted as a word exception against the 5% gate)?

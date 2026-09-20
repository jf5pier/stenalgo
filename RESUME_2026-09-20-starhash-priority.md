# `*`/`#` marking rule — frequency-regret design session (2026-09-20)

Written so a fresh (cleared-context) session can pick up without re-deriving context.
**Status as of end of day 2026-09-20: fully designed AND implemented, including the
N-ary/multi-reading case, physical key realization, composition with Phase P, and a
correctly-sourced Rule 3.** See "What's genuinely still open" at the bottom for the
one piece that remains (wiring into `dictionary.py`'s actual persisted output) and
`ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s Phase P section for the condensed, currently-true
summary of what landed where. This file itself still reads as the original design
session's narrative (rationale, data, threshold sensitivity) — that reasoning is still
accurate; only "still open" items below have been struck through as they were closed
out in the same-day follow-up implementation session. Read together with
`RESUME_2026-09-19-phaseP.md` (defines the three collision buckets this session builds
on).

## Bottom line

Designed and implemented a systematic rule for which reading gets the extra `*`/`#`
stroke when two homophone readings clash by grammatical category, covering both
Phase P's bucket 2 (cross-category clash, same lemme different `gramCat`,
`detectCrossCategoryClash`) and bucket 3 (cross-lemma collision, different lemme,
`crossLemmaCollisions`). The design: frequency-ratio exemption + homograph exemption +
a correctly-sourced spelling-doublet exemption (Rule 3, see below) + a 6-entry
`GramCat` priority list for the remaining hard cases, getting within **0.526% of the
theoretical best possible** average keystroke cost, using a single memorable rule set
instead of per-pair memorization. The naive "many collisions ⇒ doublet" version of
Rule 3 was tested and **disproven** via real Google Ngram data (see below) — but the
correctly-sourced replacement (cross-referencing `resources/reform1990.tsv` directly,
found the same session per the discovery noted below) **was built and shipped** in the
follow-up implementation session; see `loadReform1990DoubletPairs` in
`src/ambiguitychecker.py`.

## The reframing: regret, not classification

Original question was "how do we classify types of homophones" (PCA over frequency was
floated). Reframed once it was established the mark must be a **static per-word
choice** — the writer can't decide at write-time which reading is intended, so the
mark can't depend on runtime probability, only on a fixed convention. That makes it a
**regret-minimization problem**, not a clustering problem.

## Cost model

Uses `word.frequency` — confirmed (via code read) to be the single live frequency
signal read by every ranking/tiebreak/cost site in the codebase
(`greedyoptimizer.py:284`, `ambiguitychecker.py:96,152,198,670`). It's hard-set to
`frequencyFilm` (film-subtitle corpus) in `src/word.py:89`; a blended
`0.9*film+0.1*book` version is commented out one line above; `frequencyBook` is
carried on `Word` but read by nothing. `.frequency` is what all formulas below use.

For a clashing pair between side A and side B:
- **cost** of a rule marking side A = `freq(A)` (every occurrence of A costs one
  `*`-press). Summed over all pairs a rule applies to = the real keystroke bill.
- **optimum** = `min(freqA, freqB)` — the unconstrained, per-pair-perfect floor (mark
  whichever side is individually rarer). Unbeatable, but needs memorizing per lemma.
- **gap** = `cost - optimum` (never negative) — the price of using one fixed rule
  across a whole category instead of optimizing every pair individually.
- **volume** = `freqA + freqB` — total occurrences of either reading.
- **gap%** = `gap / volume` — the normalized, comparable "wasted effort" metric used
  throughout to compare rules/thresholds/buckets against each other.

A **categorical rule** picks one fixed direction (mark category X vs Y) per
`(gramCatA, gramCatB)` type and applies it to every pair of that type.

## The three rules

### Rule 1 — extreme-ratio exemption (adopted, threshold = 10x)

User's insight: when one reading is 1-2 orders of magnitude rarer, a human can guess
it from context without a systematic mark — the frequency gap itself is the mnemonic.
Pairs with `max(freqA,freqB)/min(freqA,freqB) >= threshold` are pulled out of the
population a categorical rule is fit against, and instead individually resolved at
their own per-pair optimum (mark the rarer side), at zero "rule to remember" cost.

**This turned out to be the dominant lever**, not a minor tweak — at 10x it already
covers 88.8% of total volume. Threshold sensitivity (full detail in "Threshold
sensitivity" below): **10x is the empirically correct choice** — it's the only
threshold that both (a) minimizes total gap% and (b) yields a single consistent
linear `GramCat` ranking with zero cycles. 30x and 100x are both worse on gap% AND
both produce the exact same 3-cycle (`NOM beats ADJ, ADJ beats VER, VER beats NOM`) —
so higher isn't "more conservative," it's just worse on every axis tested.

### Rule 2 — homograph exemption (adopted, small effect)

If `orthoA == orthoB`, no mark is needed — identical spelling means identical typed
output regardless of which reading was meant, so it was never a real ambiguity. This
exclusion already existed in Phase P's `_isInScopeCollision` for the stroke-collision
buckets, and bucket 3's `crossLemmaCollisions` already excludes identical-ortho pairs
upstream (0 pairs dropped when re-checked). Bucket 2 dropped exactly 1 of 74 pairs
(27.5 volume) — small effect, but free and correct. (Caveat: the bucket-2 check used
a conservative "whole paradigm-set matches" approximation rather than exact per-pair
ortho equality — flagged, not verified further, low-stakes given the effect size.)

### Rule 3 — spelling-doublet exemption via "many collisions ⇒ likely a spelling
variant" heuristic — **tested and REJECTED, but see the important correction below**

Hypothesis: a lemma pair generating many colliding inflected forms at once (e.g. one
lemma pair spawning 10-15 separate word-form collisions) is probably two spellings of
the *same* word (pre/post-1990-reform doublets), not two genuinely different words,
and so needs no disambiguation at all.

Tested against real Google Books Ngram data (JSON endpoint,
`corpus=fr-2019`/`fr`, `year_start=1800`) on the 5 largest examples of this pattern
found in the lemma-pair collapse (see below): `ressurgir`/`resurgir` (15 word-pairs),
`lacer`/`lasser` (12), `compter`/`conter` (11), `trimbaler`/`trimballer` (10),
`tacher`/`tâcher` (9).

**Result: only 2 of 5 are true doublets.** `ressurgir`/`resurgir` and
`trimbaler`/`trimballer` show modest ratios (1.17x, 2.04x) with a clean historical
crossover, consistent with one word spelled two ways. The other three are genuinely
**distinct lexemes** that just happen to be near-total homophones across their
conjugation paradigms: `lacer` (to lace, ratio 9.19x, `lasser` dominant throughout,
no crossover) ≠ `lasser` (to tire); `compter` (to count, ratio 20.15x, dominant and
stable for a century) ≠ `conter` (to narrate); `tacher` (to stain, ratio 6.45x) ≠
`tâcher` (to try). None of the real crossovers line up with the 1990 reform date
either — they're decades apart from each other and from 1990.

**Conclusion: "high collision count" is not a valid doublet signal** — drop this
version of Rule 3. A real spelling-doublet exemption needs an actual lexicographic
source, not an inferred heuristic.

**Important discovery made while writing this file, not yet acted on**: that real
lexicographic source **already exists in this repo**. `resources/reform1990.tsv` (270
sourced rows) plus the full research trail in `scratch/reform1990/` (see
`scratch/reform1990/STATUS.md`) is exactly this — an OQLF- and Journal-officiel-
cross-validated list of genuine 1990 French spelling-reform old/new pairs, built and
verified in a prior session (2026-09-16, committed across several commits ending in
`2127790 Resolve absous/dissous/repartie/repartir, closing out the 1990 reform
thread`). It's wired into `lexique.py` behind five independent opt-in flags, all off
by default (`APPLY_1990_REFORM_LEMMES`, `_ORTHO`, `_ELER_ETER`, `_EMPRUNT_PLURIEL`,
`_INTERPELER`, `_ABSOUS_DISSOUS`). **A correct Rule 3 would cross-reference this
session's 1,085 distinct lemma pairs (see below) against `resources/reform1990.tsv`
directly**, instead of guessing from collision count — not done this session, flagged
as the concrete next step if Rule 3 is worth reviving.

## Threshold sensitivity — 10x vs 30x vs 100x

| Metric | 10x | 30x | 100x |
|---|---|---|---|
| Pairs exempted (of 1325 pooled) | 729 | 611 | 545 |
| % volume exempted | 88.8% | 81.3% | 76.4% |
| Distinct lemma pairs exempted (of 1085) | 585 | 483 | 429 |
| Residual same-cat / diff-cat pair count | 393 / 203 | 461 / 253 | 497 / 283 |
| ADJ/NOM direction | mark-ADJ | mark-ADJ | mark-ADJ |
| NOM/VER direction | mark-**VER** | mark-**NOM** | mark-**NOM** |
| ADJ/VER direction | mark-**ADJ** | mark-**VER** | mark-**VER** |
| Single linear ranking? | **Yes** | **No** — cycle | **No** — same cycle |
| Grand total gap% | **0.526%** | 1.235% | 1.532% |

30x/100x both produce the identical 3-cycle (`NOM > ADJ > VER > NOM`), traced to ~118
borderline (ratio 10-30x) pairs re-entering the "hard" residual — mostly deverbal
`-é(s)`/`-ée(s)` pairs (`équipés`/`équipées`, `battus`/`battues`, `jetés`/`jetées`,
`menés`/`menées` for NOM/VER; `traînées`/`traînés`, `saints`/`ceints`,
`scellée`/`sellée` for ADJ/VER). These two category-pair types have small samples
(n=58-85 depending on threshold) so a handful of borderline pairs is enough to flip
the aggregate vote; ADJ/NOM (n=121-170) is large enough to stay stable at "mark ADJ"
across all three thresholds regardless. **10x is the correct choice, confirmed on
both criteria that matter (lowest gap%, only consistent ranking) — not a compromise.**

## Final recommended design (at 10x)

1. **Homograph check** (Rule 2) — no mark if `orthoA == orthoB`.
2. **Ratio-10x exemption** (Rule 1) — if one reading is ≥10x rarer, mark it; no
   memorization needed, the frequency gap is self-evident. Covers 88.8% of volume.
3. **`GramCat` priority list** for the remaining cross-category residual (203 pairs):
   `ADV > PRO:pos > NOM > VER > ADJ > ADJ:pos` (canonical → marked). Single consistent
   linear order, zero cycles, reproduces every category-pair-type's regret-optimal
   direction exactly. (Note: this **reverses** an earlier-session tentative
   conclusion of "mark NOM" for NOM/VER — that was fit on bucket-3-alone raw data,
   dominated by easy/extreme-ratio pairs; once those are exempted by Rule 1, the
   actual hard population wants the opposite direction, "mark VER". Discard the
   earlier "mark NOM" recommendation.)
4. **Same-category residual** (393 pairs, no `GramCat` signal possible since both
   readings share a category) — per-pair "mark whichever specific word is rarer."
   This is optimal by construction and isn't really an exception to memorize; it's
   ordinary per-word brief memorization, same as any other steno theory entry.
5. **Override list** for the ~51 pairs where step 3's aggregate rule still misfires
   (regret > 0) — top 10 by regret, combining the 10x and 100x top-lists since the
   dominant entries repeat across thresholds: `salles`/`sales`, `chers`/`chairs`,
   `différends`/`différents`, `entrées`/`entrés`, `donnés`/`données`,
   `dures`/`durs`, `alentours`/`alentour`, `virées`/`virés`, `portés`/`portées`,
   `envolées`/`envolés`. Top 3 alone are ~55% of all remaining regret.

Net result: **0.526% of all keystroke volume across this disambiguation surface is
"imperfect"** relative to the unreachable theoretical optimum — effectively solved,
with a rule a human can actually learn (5-6 memorable pieces, not per-lemma lookup).

## Data caveats / discrepancies found along the way (not resolved, flagged for a
future session)

- **Bucket 2 population mismatch**: this session's `detectCrossCategoryClash` run
  found 74 pairs (72 lemmas), not the 29 documented in `RESUME_2026-09-19-phaseP.md`.
  **No NOM/VER pairs exist in the current data at all** — the docs' own `dîner`
  NOM-vs-VER illustrative example isn't present. Likely a stale `Dictionary.pickle`/
  `FirstTheory.pickle` (remember the caching gotcha documented repeatedly in
  `scratch/reform1990/STATUS.md`: these pickle files are silently reused if present
  rather than rebuilt) vs. a dictionary regenerated since the 29-pair count was taken.
  **Reconcile this before trusting any bucket-2 number for a final implementation** —
  delete the pickles and rebuild, then re-run `detectCrossCategoryClash` fresh.
- **The `NOM/PRO:per` outlier is resolved, not a data bug**: it's a single pair,
  `hiles` (NOM, freq ≈ 0.0) vs. `ils` (PRO:per, freq ≈ 3075.1) — an unused word
  colliding with one of the most common words in French. Not a homograph; resolved
  automatically by Rule 1 (effectively infinite ratio), contributing 0 to achievable
  cost. Was flagged as a concern before Rule 1 was applied; no longer one.
- **Lemma-pair collapse**: the pooled 1,325 word/lemma-level pairs (74 bucket-2 +
  1,252 bucket-3, minus 1 Rule-2 drop) collapse to **1,085 distinct lemma pairs**
  (bucket 2's 73 stay as-is, already lemma-level; bucket 3's 1,252 collapse to 1,012,
  since 113 lemma pairs have multiple inflected forms colliding at once). This is
  what surfaced the Rule 3 candidates above.
- **ADJ/NOM direction genuinely differs between the two buckets' own raw data**
  (bucket 2 alone wanted "mark NOM"/ADJ canonical; bucket 3 alone wanted "mark
  ADJ"/NOM canonical) — resolved by pooling: bucket 3's volume for this type (~309)
  dwarfs bucket 2's (~5.6), so the pooled-optimal direction is bucket 3's ("mark
  ADJ"), and adopting it uniformly costs bucket 2 almost nothing. This assumes
  buckets 2 and 3 will share one physical marking mechanism — **not yet confirmed**;
  per `RESUME_2026-09-19-phaseP.md`, bucket 2's resolution mechanism is still
  undecided while bucket 3 is explicitly the `*`/`#` track's job. If they end up
  using separate mechanisms, this pooling assumption should be revisited.

## Wishlist item (already written into `ATOMIC_KEYPRESS_REWIRE_PLAN.md`)

Nouns ending in `-er` with plural `-ers` (French verbal nouns derived from an
infinitive, e.g. `dîner`/`dîners`) could reuse the existing `Infinitif`/`Infinitif:p`
atomic-feature markers instead of a generic `*`/`#` mark — a derivational-pattern
rule resolving a whole NOM/VER sub-class at once. Not sized or verified against real
data. See `ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s Phase P section for the exact note; this
file is the analysis session that raised it.

## What's genuinely still open

Everything originally listed here as a next step has been implemented and validated
in the same-day follow-up session (all in `src/ambiguitychecker.py` unless noted):

- ~~Build a `GRAMCAT_PRIORITY`-shaped table and `decideStarHashMark`.~~ **Done.**
  `GRAMCAT_PRIORITY` in `src/greedyoptimizer.py`; `decideStarHashMark(wordA, wordB,
  doubletPairs=frozenset()) -> Word | None` implements homograph exemption → Rule 3
  doublet exemption (opt-in via `doubletPairs`) → `MARKING_OVERRIDES` → ratio-10x
  exemption → same-`gramCat` per-pair-optimal → `GRAMCAT_PRIORITY` → frequency
  fallback. Spot-checked against live `crossLemmaCollisions` data: 1247 bucket-3
  pairs, 0.208% gap from true optimum, consistent with the design's headline number.
- ~~Reconcile the bucket-2 29-vs-74 discrepancy against a fresh rebuild.~~ **Done.**
  Fresh `Dictionary.pickle`/`FirstTheory.pickle` rebuild still gives 74 pairs/72
  lemmas, 0 NOM/VER pairs — confirms it was stale documentation
  (`RESUME_2026-09-19-phaseP.md`'s "29 pairs" is outdated), not a caching bug. Headline
  gap re-verified at 0.499% on the fresh rebuild (vs. 0.526% documented above).
- ~~The N-ary case (clusters of >2 colliding readings) and physical key
  realization.~~ **Done.** `rankHomophoneCluster` (total order via `decideStarHashMark`
  pairwise, `functools.cmp_to_key`), `assignStarHashCombos` (`(), (*,), (#,), (*#,)`
  for ≤4 readings, escalating to repeated `(*#, *#, ...)` syllables beyond that),
  `assignStarHashMarks` (collapses homograph AND Rule-3-doublet readings via
  union-find so they don't consume a slot), `STAR_KEY=10`/`HASH_KEY=15` physical
  mapping, `starHashCodeToStrokes`/`assignStarHashPhysicalStrokes`. Validated against
  the live lexicon: biggest real cluster is 7 readings (the `au`/`eau`/`oh`/`haut`/
  `ho`/`ô`/`aux` set), max escalation depth 4 anywhere in the whole lexicon.
- ~~Composition with Phase P's own extra-stroke mechanism.~~ **Done.** Investigated
  first: 100% of currently-known bucket-2/3 collisions involve a word that already
  has its own Phase P extra stroke (by construction — those collision fields are
  computed from Phase P's `finalInduced`). The two mechanisms compose by simple
  concatenation (Phase P's stroke, then `*`/`#` after it) and can't create new
  cross-cluster collisions (structurally disjoint key ranges: `STAR_KEY`/`HASH_KEY`
  are excluded from `Keyboard.allowedKeys`). Implementation:
  `groupHomophonesByReservedStroke` (groups by shared post-Phase-P stroke, filters to
  genuine distinct-`lemmeGramCat`/distinct-`ortho` groups) and
  `composeReservedKeyStrokes`. Validated: 1079 genuine groups found in Phase P's own
  elicited population, 0 accidental collisions with existing theory strokes, 0 genuine
  (distinct-spelling) collisions left anywhere after composition.
- ~~Cross-reference the 1,085 distinct lemma pairs against `resources/reform1990.tsv`
  for a properly sourced Rule 3.~~ **Done.** `loadReform1990DoubletPairs()` parses the
  file into `{oldSpelling, newSpelling}` pairs (excluding `isException=True` rows);
  threaded as an opt-in `doubletPairs` parameter through the whole pipeline. Of 259
  loaded pairs, 11 bucket-3 collisions were genuinely exempted this way
  (`dessoûler`/`dessouler`, `tocard`/`toquard`, `béluga`/`beluga`, ...), saving 13 real
  words an unneeded stroke, zero regressions.

**What's actually still open:**
- **Decide whether buckets 2 and 3 share one physical marking mechanism** (this
  session's pooling assumed yes) or stay genuinely separate tracks — not re-examined
  during implementation; the implementation pools them via `decideStarHashMark`'s
  single decision function, consistent with the original assumption, but the
  underlying design question was never explicitly re-confirmed.
- **The override list is still provisional** — built from a top-10-by-regret list at
  the time (later replaced with the full ~51-pair list before implementation, but
  never regenerated from a single canonical run purely at the finally-chosen 10x
  threshold in isolation, independent of the 30x/100x cross-check that originally
  produced it).
- **Not wired into `dictionary.py`'s actual persisted output.** Everything above is a
  validated pure-function pipeline (`decideStarHashMark` → ... →
  `composeReservedKeyStrokes`), exercised only by ad hoc scripts and unit tests — it
  is not yet the thing `dictionary.py`'s pipeline calls to produce a real theory
  output. This is a bigger, previously-deferred question (ROADMAP.md open question 4,
  the `theory.tsv`-replacement work), not a small follow-up.

## Script inventory (all in `scratch/`, throwaway/untracked, read-only analyses —
none of this is built for reuse; would need a proper `util/` script, mirroring
`util/build_phase_p_realization.py`'s role, if this design gets implemented)

- `cross_category_regret.py` — bucket 2 alone, raw (no rules).
- `cross_lemma_regret.py` — bucket 3 alone, raw (no rules), same-category vs
  different-category split.
- `combined_regret.py` — pooled bucket 2+3, Rules 1 (10x) + 2 applied. The primary/
  headline script.
- `combined_regret_30x.py` / `combined_regret_100x.py` — copies of the above at
  different Rule-1 thresholds, for the sensitivity table.
- `lemma_pair_exemption.py` — the distinct-lemma-pair rollup (1,325 → 1,085) and its
  per-threshold exemption counts.

All of these load `Dictionary.pickle`/`FirstTheory.pickle` (same
`sys.modules["__main__"].Dictionary` alias trick as `util/build_phase_p_realization.py`
— see that script's `_loadTheory` for the pattern) and, for bucket 3, the ortho pairs
in `phase_p_keypress_realization.json`.

## Verification commands for a fresh session

```
# Confirm bucket-2 population against a FRESH rebuild (resolve the 29-vs-74 discrepancy first)
rm -f Dictionary.pickle FirstTheory.pickle && python dictionary.py
python -c "from src.ambiguitychecker import detectCrossCategoryClash; ..."  # re-run, compare to 74

# Reproduce the headline 10x result
python scratch/combined_regret.py

# Reproduce the threshold comparison
python scratch/combined_regret_30x.py
python scratch/combined_regret_100x.py

# Reproduce the lemma-pair collapse / exemption counts
python scratch/lemma_pair_exemption.py
```

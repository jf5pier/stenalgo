# Resume: Phase 3/4 budgeted selection + exception-rate requirement (2026-09-27)

**Read this file, then (in order) `PLAN_2026-09-26-affix-abbreviations.md`,
`RESUME_2026-09-26-affix-scan-state.md`, `RESUME_2026-09-26-pluvier-affix-scan.md`,
`RESUME_2026-09-27-affix-growth-search-design.md`, `DESIGN_2026-09-27-affix-rule-selection.md`.**
The DESIGN file's Phase 1/2 (lattice growth, candidate rules) are implemented and were verified
in the session that wrote that file. **This session implemented Phase 3 (budgeted selection) and
Phase 4 (keypress binding), then spent most of its time on real-data investigation that changed
several of DESIGN's assumptions.** This file is the up-to-date picture; where it disagrees with
DESIGN, this file wins.

Everything here is measurement/proposal work on a steno theory generator. Nothing is wired into
production (`dictionary.py`/the real pipeline). `pytest src/test/` (697 tests) and `mypy src/`
must stay clean; use `env/bin/python`, run from the repo root, serialize heavy runs (7 GB RAM).

## 1. What's implemented (all four phases now exist)

- **Phase 1** (`src/affixes.py`): the pattern lattice -- `Slot`, `growAffixesLattice`,
  `_growLatticeLevel`, A7 (`poolTailVariants`) and A8 (`poolKnownAffixGroups`) pooling.
- **Phase 2** (`src/affixrules.py`): `buildCandidateRule` (root + greedy form selection, cheap
  proxy score) and `chooseRuleKeypress` (the expensive per-root keypress search -- **substantially
  rewritten this session**, see §3).
- **Phase 3** (`src/affixrules.py`): `selectRules` -- a 3-stage lazy-greedy heap (raw upper bound
  -> proxy marginal -> exact marginal), each stage recomputed fresh against the current selection
  before being trusted, word-once-crediting via `bestS`. `swapPass` -- up to 3 rounds trying to
  replace a selected rule with a better unselected one.
- **Phase 4** (`src/affixrules.py`): `bindKeypresses` -- assigns each selected rule its key,
  descending by score, allowing two rules of the same position to share a key when a joint
  simulation (`_jointLoss`) loses at most `SPLIT_MAX_LOSS` (2%) of either.
- **CLI** (`util/affix_scan.py`): `--part b` (default, non-`--legacy`) now runs the full
  Phase 2-4 pipeline (`partSelectAndBind`), writing `scratch/affix-rules.tsv` and
  `scratch/affix-rules-report.md`. `--preview-only` runs just the old Phase-2-only top-30 preview
  (`partRules`). `--legacy` still runs the pre-existing `growthMerges`/`unifyFamilies`/
  `assignGreedy` path unchanged, for comparison.

**Test gap, not yet closed**: none of Phase 3/4 (`selectRules`, `swapPass`, `bindKeypresses`,
`_jointLoss`, `_exceptionRate`) has dedicated unit tests yet. DESIGN §7.2 lists the fixtures that
should exist (selection budget respected, swap never lowers the total, two colliding rules can't
share, etc.) -- none written. This session's verification was all real-data spot-checks instead.
Close this gap before trusting the pipeline unattended.

## 2. Decisions made this session (in order; each was a real back-and-forth, not a guess)

1. **`-Cter` verb-ending fragments (`ter`/`der`/`ver`/`ler`/`ser`/`ger`/`rer`/`teur`/`cher`):
   deliberately left UNFILTERED.** `isVerbEndingFragment` (in `src/affixes.py`) still exists but
   is **not called** -- the drop in `buildCandidates`'s `kept` loop was removed, with a comment
   explaining why. The user's call: let them compete in Phase 3 on real score instead of being cut
   upstream. Verified: merging them into ONE candidate (`-Cer`, any onset) nets **very negative**
   (-4961, too many `keyOverlap`/`standaloneTrap` collisions once span=1 words can't merge); no
   pair of them can even **share** a keypress (0/36 compatible pairs, `_jointLoss` always > 2%).
   So if kept, they stay as N separate budget slots -- currently 7-9 of the 30, depending on run.
2. **`-iter` verb participles join `-ité`.** `isIterParticiple` (in `src/affixes.py`) admits any
   inflected (non-lemma) form of a verb whose infinitive ends `iter` into suffix seeding, same as a
   lemma form -- deliberately not restricted to the participle mood, since a present-tense
   homograph (`habitez`) only matches a suffix-shaped tail by accident of silent letters, so the
   broadening is safe. **Known gap, not fixed**: the check is spelling-based
   (`lemme.endswith("iter")`), not phonetic-rest-based, so it misses phonetically-identical verbs
   spelled with a doubled consonant or accent (`quitter`, `acquitter`, `fritter`, `gîter` -- freq
   ~89, small but real). Also identified (not yet extended): `-oter`/`-eter`/`-éter` verbs have the
   same kind of real overlap with existing `·oté`/`·°té`/`·eté` noun families and were never
   generalized the way `-iter` was.
3. **Top-200-by-frequency words AND every monosyllabic word are excluded from ever being an affix
   carrier.** `carrierExclusionSet`/`TOP_WORDS_EXCLUDED=200` (in `src/affixes.py`), wired into
   `buildCandidates` via a new `excludeTopWords: bool = True` parameter (default on; the one
   existing unit test that used a synthetic <200-word fixture needed `excludeTopWords=False`,
   since "top 200" is meaningless against a tiny corpus). Reasoning: these words earn their own
   dedicated stenogram in the real theory regardless of shape, so counting their frequency toward
   an affix rule is double-dipping and can badly distort a rule's apparent value (`jamais` alone
   was propping up 99.7% of a "ja-" prefix rule's score before this fix; that rule disappeared
   entirely once excluded, correctly). 8328 words excluded total on the real lexicon (dominated by
   the monosyllabic count, not the top-200 slice).
4. **`SIM_MIN`/`SIM_TOP_N` fully retired; replaced by a hard `MAX_EXCEPTION_RATE = 0.05`
   requirement, and `chooseRuleKeypress` now tests every legal keypress (~1751), not a
   similarity-filtered subset.** Found empirically on `re`: the highest-similarity key (rank
   27/1751, literally "R" -- re's own onset) had an 18.7% exception rate on common words
   (`reviens`, `revient`, `retrouve`...); a key with **zero** similarity (rank 926/1751) scored
   **41% higher** (5917.9 vs 4199.4) and had a fraction of the exceptions. Similarity was hiding
   the better answer, not just failing to help -- so it's no longer any kind of gate, only a label
   on the final pick (`rule.keySimilarity`) for human review. **Real cost of this fix**: many
   rules now sit on keys with near-zero or negative similarity (`a`->0.00, `ré`->0.00, `ai`->-0.50,
   `en`->-0.39, `se`->-0.33, `de`->-0.26...) -- fewer silent failures, but more keys that have to
   be memorized as arbitrary lookups rather than "sounds like the affix." **Open question, not
   decided**: whether to add similarity back as a tiebreaker among rate-compliant candidates
   (prefer the most mnemonic key when two are close in score) instead of pure score-maximization.
   **Runtime cost**: Phase 3 exact-evaluation went from ~70-90s to ~770-830s (whole pipeline
   ~14 min) since every exact-evaluated root now does ~1751 simulate() calls instead of ~40.

## 3. Real bug found this session, NOT yet fixed

**`growAffixesLattice`'s dedup only compares newly-grown children against each other, never
against the pool it started from.** Concretely (`src/affixes.py`, `growAffixesLattice`):

```python
pool = dict(cands)                              # the ORIGINAL pool (includes A7/A8-pooled nodes)
for cand in _dedupeByCarrierSet(allChildren):    # allChildren = only the newly-GROWN nodes
    pool[(cand.position, cand.k, cand.phono, cand.ortho)] = cand
```

`_dedupeByCarrierSet` is only ever called on `allChildren`. If a node produced by A7 pooling
(`poolTailVariants`, which runs *before* growth and has no `rootKey`/`grownFromKey`) happens to
cover the **exact same carrier set** as a node A9 growth later derives from a *different* root, the
two are never compared, never merged, never alias-linked -- they just sit in the final pool as two
separate, unrelated-looking candidates.

**This is exactly what's wrong with `ment` vs `·°ment`** (the user's concrete question this
session): `·°ment` (A7-pooled, k=2, phono `°.m@`, `rootKey=None`, `grownFromKey=None`) and `ment`'s
own lattice-grown descendant `[C]°.m@` (slots `[('onset', '°', ())]`, found via
`descendantsOf(ment, idx)`) are **the same real-world word pattern** -- verified: `ment` has 2292
carriers, `·°ment` has 2275, **1912 overlap (83%)**. But since `·°ment` was never in `allChildren`
when `ment`'s growth ran, `_dedupeByCarrierSet` never saw the collision, so Phase 2 never
considered them as one rule with two forms. Forcing the merge by hand (`Rule(ment, [ment, sment])`)
works fine mechanically -- key `(16,20)`, 15 exceptions (0.56% rate) -- but scores lower (7379.4)
than keeping them as two separately-optimized rules (8176.3 + whatever `·°ment`'s true marginal
is), so the *pipeline's own selection logic* isn't obviously wrong to keep them apart even once
they're linked -- but right now it doesn't even get the chance to choose, because they're invisible
to each other.

**Fix direction (not implemented)**: `_dedupeByCarrierSet` (or a new pass) needs to compare
`allChildren` against the *whole* pool (`cands` too), not just against itself, so a grown node that
duplicates something already in the seed pool gets properly aliased and root/parent-linked. This
would let `buildCandidateRule`'s greedy form-selection *see* `·°ment` as one of `ment`'s own
candidate forms and decide for itself whether to include it -- instead of the two competing as
unrelated roots in Phase 3, which is what happens today (both got selected independently in this
session's last full run, ranks 1 and 2).

**Do this fix, then re-verify**: rerun `pytest`/`mypy`, then a full `--part b --refresh` and check
whether `ment`/`·°ment` (and any other similarly-orphaned A7/A9 pairs -- almost certainly more
exist, `ment` was just the one a human happened to ask about) collapse into fewer, cleaner rules.

## 4. Current numeric baseline (this session's last run, uncommitted, regenerable)

`scratch/affix-rules.tsv` / `scratch/affix-rules-report.md` hold the top-30 from the run *with*
`MAX_EXCEPTION_RATE=0.05` active and all of §2's decisions applied. Top few, for reference:

| rank | rule | score | keys (rtfcre) | exceptions | note |
|---|---|---|---|---|---|
| 1 | `ment` | 8176.3 | `-tm` | 2 | |
| 2 | `·°ment` | 6880.9 | `-dt` | 33 | see §3 -- shouldn't be a separate rule |
| 3 | `re` | 5902.7 | `-d` | 176 (3.8%) | similarity 0.00, see §2.4 |
| 4 | `tion` | 4465.1 | `-dtn` | 0 | |
| ... | (27 more rows) | | | | |

Regenerate with `PYTHONPATH=. env/bin/python -m util.affix_scan --part b --refresh` (~14 min,
uses the cached `scratch/affix-records.pickle` so it skips the 44s lexicon reload... no, actually
`--refresh` forces the reload; drop `--refresh` to reuse the cache if records haven't changed).

## 5. Budget (20 vs 30): still open, leaning 30

Savings curve (1..40, from a `budget=40` run) has **no elbow** -- smooth diminishing returns
throughout, rule #40 still scores ~11% of rule #1's value. Going 20->30 adds +20.4% total value;
30->40 adds +14% more. No point where marginal value craters. Recommended 30 (the design's own
upper bound) absent a hard "fewer rules to memorize" constraint from the user, but this was never
explicitly locked in -- `RULE_BUDGET = 30` is just the constant's current value, not a decision
recorded anywhere else.

## 6. What the next session should do

1. Fix the dedup bug (§3): make `_dedupeByCarrierSet` (or the call site) compare grown children
   against the *whole* pool, not just each other. Add a unit test for exactly this case (two
   candidates, same carrier set, one with `rootKey=None` pre-existing and one freshly grown from
   an unrelated root -- assert they get merged/aliased, not left as two separate pool entries).
2. Rerun the full pipeline; check whether `ment`/`·°ment` (and similar pairs -- search for other
   high-overlap same-territory pairs across the final 30, not just this one) resolve into single
   rules, and whether that changes the RULE_BUDGET recommendation.
3. Decide the open question from §2.4: similarity as a tiebreaker among rate-compliant candidates,
   yes or no.
4. Fill the §7.2 test gap for Phase 3/4 before trusting unattended reruns.
5. Consider extending `isIterParticiple`'s spelling-based check to a phonetic-rest-based one (see
   §2.2), and/or generalizing the `-oter`/`-eter`/`-éter` overlaps the same way `-iter` was.
6. Once the above settle, do the STOP-2 report DESIGN_2026-09-27-affix-rule-selection.md §7
   describes: final rule list, savings curve, sibling-pair list, every default used.

## 7. Constants reference (current values, all tunable, none sacred)

`src/affixes.py`: `MAX_SLOT_EXCLUSIONS=2`, `GROWTH_MAX_DEPTH=3`, `GROWTH_MAX_EXCEPTION_SHARE=0.02`,
`MAX_POOL=200000`, `TOP_WORDS_EXCLUDED=200` (new this session), `VERB_FRAGMENT_GRAMCAT_SHARE=0.9`
(defined, unused -- see §2.1).
`src/affixrules.py`: `RULE_BUDGET=30`, `MAX_RULE_FORMS=4`, `EXCEPTION_ALPHA=1.0`,
`EXCLUSION_COST=5.0`, `FORM_COST=10.0`, `MAX_EXCEPTION_RATE=0.05` (new this session, replaces
`SIM_MIN`/`SIM_TOP_N`), `SWAP_CANDIDATES=20`, `SWAP_PASSES=3`, `REBIND_MAX_LOSS=0.10`,
`REBIND_ITERATIONS=3` (Phase 4 rebind loop -- not yet actually exercised/tested).

## 8. Do not

Do not commit or push `scratch/` outputs (all regenerable). Do not touch the real pipeline
(`dictionary.py`/`util/build_*`/exports) -- this is measurement/proposal tooling only, per
`PLAN_2026-09-26-affix-abbreviations.md` §10 ("Out of scope"). This session's code changes ARE
being committed (on a new branch, not `main` directly) at the user's explicit request -- that's a
change from every prior session's "don't commit" instruction, specific to this point in the work.

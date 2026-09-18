# Investigate & reduce low-coverage discriminator features

## Context

The "Special keypress mapping" table (`dictionary.py`, driven by `satOptimizeDiscriminator`'s
`keyAssignment`) shows several grammatical discriminating features assigned to disambiguate very
few words — sometimes exactly one. Last session (`NOTES_2026-09-17_polarity_and_homograph_merge.md`,
Thread C) chased one instance, `rudoie` (`subjonctif:nbr_s`, 1 word), to a genuine **data bug**:
`LexiqueSynthetic.tsv`'s paradigm-completion tool appended a missing verb reading as a *separate*
`Word` row instead of merging it into the existing `LexiqueMixte.tsv` row for the same orthography,
so two `Word` instances existed where there should have been one, and the homograph-collapse logic
in `featureextractor.py` picked an accidentally-rare leftover feature to disambiguate the phantom
duplicate. A fix (`Word.mergeInfoVerb` + identity-dedup in `dictionary.py:readCorpus`) was written
but **never re-run against the full pipeline or verified past `rudoie`/`parle`**.

This session's exploration (3 parallel Explore agents) checked whether a second instance,
`exclut`, has the same root cause. **It does not.** `exclure` has no `LexiqueSynthetic.tsv` rows at
all (it's richly attested natively, never flagged as undersampled by
`detectUndersampledLemmas`, `src/verbparadigm.py:675`). Instead, `exclut` sits in a genuinely large
7-way same-lemme homophone group (`exclu`/`exclue`/`excluent`/`exclues`/`exclus`/`exclut`/`exclût`,
all phonology `Ekskly`); once the other six members claim common features (`par:pas`, `ind:pre`,
`sub:pre`), `exclut` is left with only `ind:pas:3s` (passé simple, an inherently rare tag — 2903/137656
rows corpus-wide) as its sole remaining discriminator.

Mapping the live selection algorithm (`src/featureextractor.py:222-280`,
`selectSharedDiscriminators`) confirms **why** this happens structurally, independent of any data
bug: the greedy shared-discriminator selection picks the winning feature per round by
`min(key=lambda f: (_featureComplexity(f), -featureCounts[f]))` — **complexity is the primary sort
key, coverage count is only a tiebreaker**. There is no coverage floor and no genuine cost function
anywhere in the pipeline (`satoptimizer.py`'s frequency term only weights *conflict* penalties
between already-selected features, never discriminator selection itself). `greedyoptimizer.py`'s
`FEATURE_PRIORITY` markedness table is dead code — not imported by `dictionary.py` at all, only
exercised by tests.

The uncommitted `SHARED_DISCRIMINATOR_REWIRE_PLAN.md` already anticipated this exact tension: its §7 (explicitly
deferred, "fast-follow once the live wiring exists to measure real numbers") proposes A/B testing
coverage-first ordering (`(-featureCounts[f], _featureComplexity(f))`) against the current
complexity-first ordering. That live wiring now exists (§0–§6 of that plan are implemented and
tests pass), so §7 is now unblocked and directly relevant.

**Goal of this investigation**: classify every feature currently discriminating fewer than 60 words
into (A) data/merge-bug artifacts that produce *phantom* low-count features which shouldn't exist,
vs (B) structurally legitimate but algorithmically avoidable cases (complexity-first ordering
exhausts common features and falls back to a rare one), vs (C) genuinely irreducible cases (a truly
rare grammatical slot that legitimately needs its own key). Produce concrete, scoped fixes for A and
B, and a documented decision for C.

## Investigation steps

1. **Get an accurate, current low-count feature list.** Much of the prior analysis predates several
   uncommitted fixes stacked in this tree (`Word.mergeInfoVerb`, the shared-discriminator rewire). Delete
   `Dictionary.pickle`, `FirstTheory.pickle`, `FeatureDiscrimator.pickle` (per the documented pickle
   gotcha) and re-run `python dictionary.py`. Temporarily bump `dictionary.py`'s
   `LOW_COUNT_THRESHOLD` (currently `30`, `dictionary.py:519`) to `60` so the printed table lists
   every word for every feature in scope. Capture the full "Special keypress mapping" table output.

2. **Classify each low-count feature (<60 words), starting with `rudoie` and `exclut`.** For each:
   - Check whether the discriminated word(s) have a duplicate `Word` instance sourced from
     `LexiqueMixte.tsv` vs `LexiqueSynthetic.tsv` for the same orthography/lemme (Category A —
     rudoie-style phantom split). Confirm `Word.mergeInfoVerb`'s identity-dedup actually fired for
     it post-re-run.
   - If no data-bug shape, check the homophone group size (`buildFeasibleDiscriminatorOptions`,
     `src/featureextractor.py:186-219`) and which features the other group members already claimed
     — confirm it's a legitimate "common features exhausted, rare one left" case (Category B,
     exclut-style).
   - If neither, flag as Category C / unknown for manual review (e.g. a genuinely rare word or a
     feature-extraction bug in `src/featureextractor.py`/`FeatureExtractor` proper, not the
     selection logic).
   - Use `rudoie` and `exclut`'s already-completed traces as the template (grep both TSVs for
     ortho+lemme, check `util/completeVerbParadigms.py`/`detectUndersampledLemmas` involvement,
     check corpus-wide tag frequency).

3. **Validate the Category A fix at scale**, not just `rudoie`/`parle`. Per
   `NOTES_2026-09-17...md`'s open item 3: count how many `wordByIdentity` merges fire on a full
   corpus load (add a counter/log in `dictionary.py:readCorpus`), and cross-reference that count
   against how many Category-A low-count features disappear from the table after the merge fix vs.
   before. This both validates the existing fix and measures how much of the low-count-feature
   problem it alone resolves.

4. **Quantify the Category B lever**: implement `SHARED_DISCRIMINATOR_REWIRE_PLAN.md`'s §7 A/B — swap
   `selectSharedDiscriminators`'s sort key (`src/featureextractor.py:265-266`) from
   `(_featureComplexity(f), -featureCounts[f])` to `(-featureCounts[f], _featureComplexity(f))` (or
   a blended cost, see Solutions), re-run the pipeline, and diff the resulting feature list: how many
   fewer features cover <60 words, does total special-keypress count change (§0–§6 held it at 9), does any
   previously-simple/common feature get displaced by this reordering, and do all tests still pass.

## Solutions to evaluate against the classified list

- **Category A (data-bug phantom splits)**: finish validating the already-written
  `Word.mergeInfoVerb` fix at scale (step 3). If other phantom-split cases turn up with a different
  shape than rudoie (e.g. two *native* `LexiqueMixte.tsv` rows, not a Mixte/Synthetic split), that's
  a new bug class requiring its own fix — do not assume `mergeInfoVerb` covers every case.
- **Category B (complexity-first ordering exhausts common features)**: adopt §7's coverage-first (or
  blended) ordering in `selectSharedDiscriminators` if the A/B in step 4 shows a clear reduction in
  low-count features without regressing total key count or introducing new conflicts. If a pure
  swap over-corrects (e.g. displaces cheap/common features unnecessarily), consider a blended cost
  such as `_featureComplexity(f) - log(featureCounts[f])` instead of a strict lexicographic swap.
- **Category C (irreducible rare grammatical slots)**: for tags that are legitimately rare
  corpus-wide (e.g. passé simple 3s) and only ever needed for one or two words, evaluate whether
  they belong on `ambiguityIgnoreList.tsv`'s exception-list pattern (see memory: Phase 4 exception
  list, cut n≥5 clusters 58→20) rather than consuming a dedicated physical key — i.e., accept the
  residual ambiguity for these ultra-rare forms instead of paying a stroke-assignment cost for them.
  This is a product/theory-design decision, not purely algorithmic — flag candidates for user
  review rather than auto-excluding.
- **`greedyoptimizer.py`'s `FEATURE_PRIORITY`**: confirm it's fully superseded by the live
  `satOptimizeDiscriminator`/shared-discriminator path (already true per this session's trace) and treat it as
  dead code to be removed or explicitly deprecated in a later cleanup — not a lever for this problem.

## Files in scope

- `src/featureextractor.py` — `selectSharedDiscriminators`, `buildFeasibleDiscriminatorOptions`,
  `_featureComplexity` (the core selection logic to modify for Category B)
- `dictionary.py` — `readCorpus` (Category A merge/dedup), `LOW_COUNT_THRESHOLD`/`featureWords`
  table (diagnostic instrumentation)
- `src/word.py` — `Word.mergeInfoVerb`
- `src/verbparadigm.py` — `detectUndersampledLemmas`; `util/completeVerbParadigms.py` — paradigm
  completion (Category A source)
- `SHARED_DISCRIMINATOR_REWIRE_PLAN.md` §7 — the already-scoped, deferred A/B this plan unblocks
- `resources/ambiguityIgnoreList.tsv` — precedent pattern for Category C exception-listing

## Verification

- After each change, delete the three pickle caches and re-run `python dictionary.py`; diff the
  printed "Special keypress mapping" table's feature list and total special-keypress count against the
  pre-change baseline captured in step 1.
- `pytest src/test/` (currently 415+/415 passing per the shared-discriminator rewire's own verification) must
  stay green, with new tests added for any new merge/classification logic (following the existing
  `TestMergeInfoVerb` pattern in `src/test/word_test.py`).
- Track, per iteration, the count of features discriminating <60 words as the headline metric for
  whether each fix is actually reducing low-value discriminators.

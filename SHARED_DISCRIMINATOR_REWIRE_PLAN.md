# Plan: wire the shared-discriminator selection into the real theory

> **Revision 2026-09-17** (after a code-review pass against the current tree):
> - added §3 (**ortho-collapse**) — a correctness requirement the original spec missed;
> - restructured the wiring (§1): the selection is now computed **once** in
>   `dictionary.py` and passed *into* `satOptimizeDiscriminator`. This reverses
>   v1's "only satOptimizeDiscriminator's internal call needs to switch":
>   `dictionary.py`'s own `greedyOptimizeDiscriminator` call feeds the final
>   printed theory table, so it is *not* diagnostics-only;
> - the call graph now lists the consumers outside `dictionary.py __main__`
>   (`ambiguitychecker`, `completeVerbParadigms`/`verbparadigm`) that v1 missed;
> - recorded the open design decision on the selection-criterion ordering (§7);
> - fixed line references drifted by later edits and corrected the verification
>   checklist (pickle deletion was unnecessary, one check was vacuous).

## Context

Stenalgo picks a grammatical "feature" (e.g. `pers_1`, `m_s`, `conditionnel:nbr_p`)
to discriminate each homophone word from the others sharing its lemme, then colors
those features onto a small number of physical special keypresses (combos of the
reserved keys) via CP-SAT. See `CLAUDE.md` for the overall pipeline; this plan
concerns only the discriminator *selection* step, upstream of key coloring.

There are currently **two independent feature-selection algorithms** in
`src/featureextractor.py`, and only the weaker one actually feeds the generated
theory. This plan wires the stronger one in.

## The two algorithms

### 1. Static greedy (`extractDiscriminatingFeatures` + `greedyOptimizeDiscriminator`) — currently live

- `extractDiscriminatingFeatures` (`src/featureextractor.py:31`) builds
  `orderedFeaturesSelected: list[WordFeature]`, a **global priority list** sorted
  once by `(complexity, -popularity)` (complexity added recently — fewer `:`/`_`
  components ranks first; see `_featureComplexity` at the top of the file) and
  never revisited.
- `greedyOptimizeDiscriminator` (`src/greedyoptimizer.py:77`) then, for every
  homophone group, walks that **same fixed list** and takes the first feature that
  happens to resolve each word. It never asks "is this feature still needed given
  what earlier picks already resolved?" — it has no memory of prior groups.
- Consequence: a feature that's simple AND broadly popular (like the grammatical
  category tag `VER`) wins its local race in *every* group where it's merely
  eligible, even in groups where some other, equally-simple feature already
  covers the same words elsewhere. This makes the final feature vocabulary larger
  than necessary — confirmed: `VER` is used ~1600+ times in the live theory even
  though it is not once *necessary* (see next algorithm).

### 2. Shared-discriminator selection (`buildFeasibleDiscriminatorOptions` + `selectSharedDiscriminators`) — currently a dead end

- `buildFeasibleDiscriminatorOptions` (`src/featureextractor.py:186`) computes, for
  every homophone group, the *full* set of features each word could feasibly use
  (not just one).
- `selectSharedDiscriminators` (`src/featureextractor.py:222`) is a genuine adaptive
  greedy shared-discriminator selection: at every outer iteration it **recomputes**, from the words
  still unresolved, how many each remaining feature would cover, and picks the
  best. A feature that's become redundant (everything it would resolve is already
  resolved) shows count 0 and is correctly never chosen.
- Its pick order is simplest-feature-first, coverage second
  (`min(..., key=lambda f: (_featureComplexity(f), -featureCounts[f]))`,
  `src/featureextractor.py:247-248`) — see §7 for why this is a real design
  decision, not just a tie-break.
- **Verified result:** with this algorithm, `VER` usage drops to 0 (fully
  redundant) and it uses fewer distinct features than the static greedy.
  (Caveat: the "fewer unresolved words than greedy's nofeature count" comparison
  from v1 is **not apples-to-apples** until §3 lands — greedy silently drops
  same-ortho siblings where shared-discriminator selection currently counts them unresolved, or worse,
  assigns them features.)
- **The problem:** its output, `sharedChosen: dict[Word, WordFeature]`, is
  currently a dead end. `dictionary.py:464-468` calls it only to print a
  comparison count. Nothing downstream consumes it.

## Call graph before this plan (the bug)

```
dictionary.py (__main__)
│
├─ theory = dictionary.buildTheory(starboard)                              :394
│    dict[Strokes, list[Word]]
│
├─ discrimFeatureWords, orderedFeatures, _ = extractDiscriminatingFeatures(theory)  :433
│    → discrimFeatureWords : dict[WordFeature, set[Word]]
│    → orderedFeatures     : list[WordFeature]        (static priority order)
│
├─ augmentedTheory = greedyOptimizeDiscriminator(theory, discrimFeatureWords,
│                                                  orderedFeatures, starboard)      :439
│    -- feeds the "Feature counts" diagnostic prints (:444-459)
│    -- AND lemmaFeatureWord (:506-511) → the final printed "Special keypress
│       mapping" table (:530-569). NOT diagnostics-only.
│
├─ groupFeasibleFeatures = buildFeasibleDiscriminatorOptions(theory,
│                                                    discrimFeatureWords)           :464
├─ sharedChosen, sharedUnresolved = selectSharedDiscriminators(groupFeasibleFeatures)  :465
│    -- DEAD END: only used for a diagnostic print line (:466-468)
│
└─ satOptimizeDiscriminator(theory, discrimFeatureWords, orderedFeatures, starboard,
                              numSpecialKeypresses=None)                             :480
     (src/satoptimizer.py:272)
     │
     ├─ featuresetWords = greedyOptimizeDiscriminator(theory, discrimFeatureWords,
     │                                                  orderedFeatures, keyboard)  satoptimizer.py:295-296
     │    -- SAME static-priority call, invoked a SECOND time, independently
     │    -- this featuresetWords is what actually gets colored onto keys
     │
     ├─ builds featureSets/penalties from featuresetWords (groups with <2 real
     │  features are skipped, satoptimizer.py:301-303), plus polarityCoefficients
     │  via _computeFamilyCorrelations/associationScore
     │
     ├─ _minSpecialKeypressesNeeded(...) → repeated _colorFeatures (CP-SAT) calls with
     │    increasing K until a zero-conflict coloring is found
     │
     └─ _colorFeatures(...) final call → keyAssignment: dict[WordFeature, int]
          -- THIS is the real theory / key table dictionary.py prints
```

### Consumers outside `dictionary.py __main__` (missed by v1 — all re-derive the greedy selection independently)

- **`src/ambiguitychecker.py:410-415`** — reruns `extractDiscriminatingFeatures` +
  `greedyOptimizeDiscriminator` to build `augmentedTheory`, then
  `buildAtomicFeatureToWords`/`findFeatureKeypresses`/`checkComposedChords` for the
  per-atomic-feature keypress feasibility report. After the rewiring, if this stays
  on greedy it analyzes a theory that no longer exists.
- **`util/completeVerbParadigms.py:283,385`** — builds baseline and augmented
  `featuresetWords` via `greedyOptimizeDiscriminator` for the
  newly-colliding-lemmas measurement.
- **`src/verbparadigm.py:616-635`** — `crossLemmaFeatureSetCollisions` consumes
  that output; its docstring (:621) hardcodes the greedy assumption
  ("a discriminator feature-set greedyOptimizeDiscriminator chose").
- **Tests** — `src/test/satoptimizer_test.py:228-274` exercises
  `satOptimizeDiscriminator` end-to-end (free shape coverage for the adapter;
  `numKeys` assertions may legitimately shift and need review).
  `src/test/featureextractor_test.py:267-379` covers the two selection functions.
  `src/test/greedyoptimizer_test.py` only tests `assignDiscriminatorKeypresses`
  (not in the live path) — unaffected.

## Call graph as implemented (§1-§6 landed, uncommitted as of 2026-09-17)

`buildDiscriminatorSelection` (`src/featureextractor.py:278`) is now the single
entry point every consumer below calls instead of re-deriving its own selection.
It wraps §2 (shape adapter) + §3 (ortho-collapse) around the shared-discriminator selection pair:

```
buildDiscriminatorSelection(theory, wordIsDiscrminatedByFeature=None)   featureextractor.py:278
│
├─ wordIsDiscrminatedByFeature ← extractDiscriminatingFeatures(theory) if not passed in   :294-296
│
├─ groupFeasibleFeatures = buildFeasibleDiscriminatorOptions(theory,
│                                                  wordIsDiscrminatedByFeature)     :298
│
├─ sharedChosen, sharedUnresolved = selectSharedDiscriminators(groupFeasibleFeatures)  :299
│    -- groups same-ortho words per group into homograph groups before covering
│       (§3): a homograph group's feasible set is the union of its members'; the
│       chosen feature is attributed only to its "owner"; an empty-union
│       homograph group leaves every member unresolved
│
└─ reshape sharedChosen/sharedUnresolved into
     featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]        :301-319
     -- same shape greedyOptimizeDiscriminator produces; sorted by cluster size
```

```
dictionary.py (__main__)
│
├─ theory = dictionary.buildTheory(starboard)  (or FirstTheory.pickle)
│
├─ discrimFeatureWords, orderedFeatures, _ = extractDiscriminatingFeatures(theory)
│    (or FeatureDiscrimator.pickle)
│
├─ augmentedTheory = buildDiscriminatorSelection(theory, discrimFeatureWords)
│    -- computed ONCE, reused for everything below (no more chimera risk)
│    -- feeds: feature-count diagnostics, singleFeatureDiscrimator print,
│       lemmaFeatureWord → the printed "Special keypress mapping" table,
│       AND satOptimizeDiscriminator
│
└─ satOptimizeDiscriminator(augmentedTheory, theory, numSpecialKeypresses=None)
     (src/satoptimizer.py:271 — now TAKES featuresetWords as its first
      argument instead of recomputing it; no internal greedyOptimizeDiscriminator
      call left in this path)
     │
     ├─ builds featureSets/penalties directly from the passed-in featuresetWords
     │  (groups with <2 real features still skipped), plus polarityCoefficients
     │  via _computeFamilyCorrelations/associationScore (still needs `theory`)
     │
     ├─ _minSpecialKeypressesNeeded(...) → repeated _colorFeatures (CP-SAT) calls with
     │    increasing K until a zero-conflict coloring is found
     │
     └─ _colorFeatures(...) final call → keyAssignment: dict[WordFeature, int]
          -- feeds lemmaFeatureWord + the printed table, same as before
```

`greedyOptimizeDiscriminator` is no longer called anywhere in `dictionary.py`'s
live path (§6's duplicate pass and its debug print are gone). It remains a
library function, still exercised by `src/test/greedyoptimizer_test.py`
(`assignDiscriminatorKeypresses`, not in the live path) and by tests that build
their own input with it.

### Secondary consumers — now sharing `buildDiscriminatorSelection` (§4 landed for all three)

- **`src/ambiguitychecker.py:410`** — `augmentedTheory = buildDiscriminatorSelection(theory)`
  (recomputes `discrimFeatureWords` internally since it isn't passed one) feeds
  the same `buildAtomicFeatureToWords`/`findFeatureKeypresses`/`checkComposedChords`
  keypress feasibility report as before, now analyzing the theory that's actually
  generated.
- **`util/completeVerbParadigms.py:280-281`** (augmented side, inside
  `temporarilyAugmented`) and **`:371,383`** (baseline side) — both call
  `extractDiscriminatingFeatures` then `buildDiscriminatorSelection`, immediately
  `del`-ing the intermediate `discrimFeatureWords`/`gc.collect()`-ing before the
  other side builds its own (the module's documented single-extraction-at-a-time
  memory discipline, unchanged by this rewire).
- **`src/verbparadigm.py:616-637`** — `crossLemmaFeatureSetCollisions` takes
  `featuresetWords` generically; its docstring (:622-623) now names
  `buildDiscriminatorSelection` as the primary source, with
  `greedyOptimizeDiscriminator` kept only as an alternate ("or by").
- **Tests** — `src/test/satoptimizer_test.py` updated for
  `satOptimizeDiscriminator`'s new `(featuresetWords, theory, ...)` signature.
  `src/test/featureextractor_test.py` gained two ortho-collapse cases (homograph
  pair collapsing to one owner; empty-union homograph group leaves all members unresolved).
  `src/test/greedyoptimizer_test.py` unaffected (never in the live path).

**The bug in one sentence:** the live path (`extractDiscriminatingFeatures` →
`greedyOptimizeDiscriminator` → `satOptimizeDiscriminator` → `keyAssignment`)
never consumes the adaptive, redundancy-free selection that `selectSharedDiscriminators`
already computes — it's thrown away after one print line — and neither do the
ambiguity checker nor the verb-paradigm tooling, which re-derive the greedy
selection independently.

## Goal

Make the actually-generated theory use the shared-discriminator selection's feature choices
instead of the static greedy's, so the real output stops using redundant features
like `VER` wherever a simpler/already-in-use feature would do. "Actually-generated
theory" means all three of:

- the `keyAssignment` that `satOptimizeDiscriminator` produces, and everything
  downstream of it;
- `lemmaFeatureWord` and the printed **Special keypress mapping** table
  (`dictionary.py:506-569`) — the human-facing output;
- the ambiguity-checker's atomic-feature keypress analysis (`ambiguitychecker.py`).

All three must be built from the **same** selection, computed once.

## Proposed changes

### 0. Commit the current working tree as a baseline

Before touching any code, commit everything not yet committed (working-tree
edits and untracked files listed in the repo's git status as of 2026-09-17:
`.gitignore`, `README.md`, `dictionary.py`, `src/greedyoptimizer.py`,
`src/word.py`, `todo.md`, `ROADMAP.md`, this plan file, `resources/ambiguityIgnoreList.tsv`,
`scratch/reform1990/RESUME_2026-09-16.md`, `src/ambiguitychecker.py`,
`src/test/ambiguitychecker_test.py`). This gives the rewiring a clean diff to
be judged against and a trivial revert point. `theory.tsv` is a generated
pipeline output (`dictionary.py:395`, same category as the already-gitignored
`ambiguity_report.tsv`/`anchor_feasibility.tsv`), not source — add it to
`.gitignore` instead of committing it.

### 1. Compute the selection once, in `dictionary.py`, and pass it down

This replaces v1's "only `satOptimizeDiscriminator`'s internal call
(satoptimizer.py:295-296) needs to switch" — that framing treated
`dictionary.py:439`'s `augmentedTheory` as a diagnostic, but it feeds
`lemmaFeatureWord` (`dictionary.py:507-511`) and thus the final printed table.
Rewiring only the internal call would leave that table a chimera: greedy-chosen
`(feature, word)` pairs filtered through the shared-discriminator selection's `keyAssignment`
(`if feature in keyAssignment`, `dictionary.py:510`), with cells silently missing
or showing a word greedy paired with a feature the shared-discriminator selection chose for a different
word.

Concretely:

- In `dictionary.py __main__`, after the existing `selectSharedDiscriminators`
  call, run the adapter (§2) to produce
  `featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]`.
- Use that object for **everything** downstream: the feature-count diagnostics
  (`:444-459`), `lemmaFeatureWord` (`:506-511`), and `satOptimizeDiscriminator`.
- Change `satOptimizeDiscriminator`'s signature to **accept** `featuresetWords`
  instead of recomputing it (drop the internal `greedyOptimizeDiscriminator`
  call at satoptimizer.py:295-296; it still needs `theory` for
  `_computeFamilyCorrelations`, satoptimizer.py:312-313). Callers to update:
  `dictionary.py:480` and `satoptimizer_test.py:228-274` (tests may keep building
  their input with `greedyOptimizeDiscriminator` — it remains a library function).
- Side benefit: kills the duplicate greedy pass and its noisy 20-featureset debug
  print (`greedyoptimizer.py:133-154`) from the live path.

### 2. Shape adapter: `sharedChosen` → `featuresetWords`

`selectSharedDiscriminators` returns `dict[Word, WordFeature]` — flat, one feature
per word, no cluster grouping. To feed `satOptimizeDiscriminator`, regroup into
per-`(strokes, lemme)` clusters exactly as `buildFeasibleDiscriminatorOptions`
grouped them (iterate `groupFeasibleFeatures`), producing the same
`dict[tuple[WordFeature,...], list[tuple[Word,...]]]` shape:

- Per group, build the `(featureTuple, wordTuple)` pair with strict pairwise
  alignment (`feature_i ↔ word_i`). Alignment is the only ordering contract —
  `satOptimizeDiscriminator` treats feature sets as sets, and `dictionary.py:509`
  only `zip()`s.
- Accumulate into the dict keyed by feature tuple with list-append, the same
  merge `greedyOptimizeDiscriminator` uses (`src/greedyoptimizer.py:124-126`) —
  distinct clusters with identical feature tuples must keep merging, not
  overwrite each other.
- Preserve existing downstream behavior automatically via the same shape:
  groups whose real features number <2 are already skipped
  (`satoptimizer.py:301-303`), `NO_FEATURE` entries already filtered.

### 3. Ortho-collapse: replicate greedy's same-ortho semantics — correctness-critical, missed by v1

`greedyOptimizeDiscriminator` drops same-ortho siblings when one of them gets a
feature (`src/greedyoptimizer.py:119-122`): words sharing an orthography write
identical text, so they need no discriminating stroke of their own.
`buildFeasibleDiscriminatorOptions` puts **every** word of the group into the
shared-discriminator selection universe, homographs included. If the adapter doesn't replicate the
collapse:

- A sibling that natively carries its own exclusive feature is a legitimate
  owner in `wordIsDiscrminatedByFeature` (the owner-picking logic at
  `src/featureextractor.py:117-118` exists precisely because true homographs
  exist) → the shared-discriminator selection may assign **both** homographs a feature → a spurious extra
  feature in that group's featureset → extra coloring pressure and a redundant
  dictionary entry writing the same ortho via a different stroke. Directly
  counter to this plan's goal.
- A sibling with no feasible features lands in `sharedUnresolved` → gets
  `NO_FEATURE` → is counted "unresolved" where greedy correctly resolves it
  implicitly via its ortho-mate.

**Spec — cover homograph groups, not words:**

- Within each `(strokes, lemme)` group, group words by `ortho` into homograph
  groups. The homograph group is the unit to cover; its feasible set is the
  **union** of its members' feasible sets.
- When feature `f` is chosen for a homograph group, attribute it to `f`'s
  owner: the member present in `wordIsDiscrminatedByFeature[f]` (exactly one
  per group by construction). Emit `(f, owner)`; emit nothing for the other
  siblings.
- A homograph group whose union-feasible set is empty gets `NO_FEATURE` for
  **all** its members (mirrors greedy: a whole featureless homograph group
  reaches the nofeature fallback at `src/greedyoptimizer.py:105-112`; a
  partially-coverable one never does).
- Implement either inside `selectSharedDiscriminators` or in a wrapper just before
  it — its docstring already claims to mirror greedy's nofeature fallback, so
  this grouping belongs there semantically. Existing tests are unaffected unless
  they include same-ortho homographs within one group (they currently don't) —
  **add one that does** (homograph pair where both members natively carry
  different exclusive features).
- Invariant this buys: after §3, `sharedUnresolved` should equal greedy's
  nofeature word set **exactly** (both reduce to "words whose homograph group
  has an empty feasible union"). Currently the 7 words `dégueu`, `déjanté`, `fayotte`,
  `cachère`, `kasher`, `nues`, `zakouski` — genuine cross-lemma collisions /
  valid-spelling-triplet ambiguity, not bugs. If the two sets ever diverge, the
  adapter has a bug.

### 4. Secondary consumers

- **`ambiguitychecker.py:410-415`**: switch to the same shared selection.
  Extract a helper (e.g. `buildDiscriminatorSelection(theory) ->
  featuresetWords`, wrapping §2+§3) used by both `dictionary.py` and
  `ambiguitychecker.py`, or pickle its output alongside
  `FeatureDiscrimator.pickle` — do not leave a second, divergent re-derivation.
- **`completeVerbParadigms.py:283,385` + `verbparadigm.py:616`**: either switch
  both baseline and augmented sides to the shared selection, or leave them on
  greedy and **document** them as measuring the legacy baseline (update the
  docstring at `verbparadigm.py:621`, which currently hardcodes the greedy
  assumption). Open decision — see §8.
- **Tests**: run `pytest src/test/` before and after; review
  `satoptimizer_test.py` `numKeys`/`keys` expectations against the new input and
  update them deliberately, not just to green the run.

### 5. Re-run and compare

After wiring:
```bash
pytest src/test/
python dictionary.py
```
- **Do not** delete `FirstTheory.pickle` / `FeatureDiscrimator.pickle` (v1 said
  to). Nothing downstream of the change is pickled (the `AugTheory.pickle` block
  at `dictionary.py:417-423` is commented out) and the theory /
  `discrimFeatureWords` inputs are unchanged — deleting `FirstTheory.pickle`
  forces a pointless full `buildTheory` pass over 136k words. Rebuild pickles
  only if the lexicon itself changed.
- Check `satOptimizeDiscriminator: N special keypresses needed ...` — the key count
  should be **≤ today's** (shared-discriminator selection uses fewer distinct features and, with §3,
  never larger per-group feature sets). Note "0 conflicts, penalty 0.0" is
  *structurally guaranteed* with `numSpecialKeypresses=None` (`conflictBudget=0`),
  so it is not an informative check — don't treat it as one.
- Confirm `VER` no longer appears in `keyAssignment` (or appears far less), and
  that the printed Special keypress mapping table is fully populated (no silently
  dropped cells — the §1 chimera symptom).
- Confirm the unresolved-word invariant from §3 (same 7 words, matching
  greedy's nofeature set exactly).

### 6. Fate of the static greedy path

Recommendation (recorded; final call is the user's): **keep**
`greedyOptimizeDiscriminator` as a library function — it is consumed by
`ambiguitychecker.py` (until §4 switches it), `completeVerbParadigms.py`, and
potentially tests — but **remove it from `dictionary.py`'s live path** once §1
lands, printing equivalent stats from the shared-discriminator selection instead of the
comparison line at `dictionary.py:466-468`.

Once rewired, `orderedFeaturesSelected` (the ordering loop at
`src/featureextractor.py:146-181`) becomes vestigial for theory generation —
only the popularity-sorted `wordIsDiscrminatedByFeature` dict is needed (by
`buildFeasibleDiscriminatorOptions`). Retire it in a separate cleanup; note the
loop already contains dead logic (the no-op inner re-filter at `:156-160` and
the last-feature-only `leftOverDiscriminatedFrom` update at `:168-175` affect
diagnostic prints only).

## Open design decisions

> **Deferred fast-follow (recorded during implementation):** the rewiring landed keeping
> the current complexity-first order as-is. The coverage-first A/B below needs the live
> wiring to exist first to measure real numbers on the full lexicon, so it wasn't worth
> blocking the rewire on it — do it as a separate follow-up pass.

### 7. Selection-criterion ordering: complexity-first or coverage-first?

**Decided 2026-09-18 (see `PLAN_2026-09-18_low_value_discriminators.md`): switched to
coverage-first**, `(-featureCounts[f], _featureComplexity(f))`
(`src/featureextractor.py:265-266`). Measured on the full lexicon after re-verifying
`Word.mergeInfoVerb`'s identity-dedup fix (11,461 merges fire on a full corpus load):

| | complexity-first (old) | coverage-first (new) | blended (`complexity - log(count)`, rejected) |
|---|---|---|---|
| distinct features <60-word coverage | 20 | **14** | 18 |
| special keypresses needed | 9 | 11 | 10 |
| tests | 422/422 | 422/422 | 422/422 |

Coverage-first was chosen: it directly targets the headline metric (fewest
low-value/rare discriminators) and fixes both `rudoie` (now covered by
`subjonctif:présent:pers_3:nbr_s`, merged with 27 other words) and `exclut` (now
covered by `indicatif:pers_3:nbr_s`, merged with 33 other words) without
reintroducing new single-word discriminators. The blended cost was tried as the
plan anticipated but rejected: it lands at an intermediate key count (10) while
doing *worse* than a pure swap on the headline metric (18 vs 14) and introduces
two new single-word discriminators (`subjonctif:pers_3`: `rassoie`; `passé`:
`enfonçai`) that neither pure ordering produces — a strict lexicographic swap,
not a blend, turned out to dominate on both axes that mattered here.

The 2-key cost (9→11) is accepted: `_minSpecialKeypressesNeeded`'s coloring budget is the
size of the non-empty stroke-combination space over the 4 reserved keys (up to 15),
not a hard 9-key ceiling, so 11 is comfortably inside budget. This may need
revisiting if a future change pushes special-keypress count close to that ceiling.

Original analysis, for reference:

`selectSharedDiscriminators` previously picked by
`(_featureComplexity(f), -featureCounts[f])` — **complexity primary, coverage
secondary**. That is not a greedy set-cover (the ln·n approximation guarantee
requires max-coverage-first): a simple feature covering 2 words beats a complex
one covering 2000. It trades feature-vocabulary size (and key pressure) for
per-feature cognitive simplicity — the trade this session's numbers now argue
against, at least for the <60-word tail.

### 8. Verb-paradigm tooling baseline

Whether `completeVerbParadigms.py` / `crossLemmaFeatureSetCollisions` should
move to the shared selection (§4) or stay a documented greedy-baseline
measurement. Switching keeps every tool analyzing the real theory; staying
keeps the baseline comparable with historical numbers.

## Non-goals / out of scope for this plan

- No changes to the CP-SAT coloring itself (`_colorFeatures`, `_minSpecialKeypressesNeeded`
  in `src/satoptimizer.py`) — only the *input* feature sets it receives change.
- No changes to `FEATURE_PRIORITY` / `assignDiscriminatorKeypresses` (the
  no-stroke/empty-stroke assignment logic in `src/greedyoptimizer.py`) unless
  testing reveals it depends on assumptions the static greedy's output shape
  happened to guarantee (e.g. ordering) that the adaptive one doesn't.

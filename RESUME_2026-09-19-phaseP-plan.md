# Phase P (physical realization) — Milestone 1 plan

Written so a fresh (cleared-context) session can pick up and execute without re-deriving
context. Read together with `ATOMIC_KEYPRESS_REWIRE_PLAN.md` (its "Phase P" section,
lines 186-218), `RESUME_2026-09-18.md` (design decision #1: reserved keys `[0,1,10,15]`
belong exclusively to the lemma-homophone `*`/`#` track; same-lemma conjugation atoms —
what Phase G/Phase P are about — get keypresses realized from the **coda** bank
`[16..25]`), and `RESUME_2026-09-19-cpsat.md` (Phase G's adopted output this milestone
consumes).

**EXECUTED as of this session — see `RESUME_2026-09-19-phaseP.md` for the final,
verified state.** What actually got built diverged from this plan in two load-bearing
ways the plan didn't anticipate (both driven by user review, not pre-planned): the
discriminator is realized as a brand-new trailing coda stroke, not merged into the
word's last existing stroke (§below); and per-word markers needing several Phase G
groups at once are composed into ONE shared extra stroke, checked jointly, not each
group tested in isolation. Read the new file first; this one is kept for historical
context on the original (superseded) design sketch below.

## Context

Phase G (`src/phasegsat.py`, adopted output in `phase_g_keypress_assignment.json`)
settled the **abstract** layer: 6 keypress groups bundling 13 grammatical markers
(`{f}`, `{impératif,pers_1}`, `{imparfait,pers_2}`, `{conditionnel,infinitif,subjonctif}`,
`{future,passé,pers_3}`, `{nbr_p,p}`), proven minimal (K=6) and exhaustively validated
against all 47,799 homophone groups. It never touched real keyboard keys.

Phase P is the next phase per `ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s own "Phase P" section:
decide which **physical coda keys** (`starboard3h.json`'s `[16..25]`, all right-hand —
the 4 dedicated `[0,1,10,15]` reserved keys belong to the *different* lemma-homophone
`*`/`#` track, confirmed by `RESUME_2026-09-18.md`'s design decision #1) realize each of
Phase G's 6 keypress groups, without colliding with any word's existing stroke in the
live `theory`.

`src/ambiguitychecker.py`'s "Part 2" (`buildAtomicFeatureToWords`, `_isFeasibleAddition`,
`findFeatureKeypresses`, `checkComposedChords`) is already exactly this — but
diagnostic-only, fed by the now-superseded `buildDiscriminatorSelection`/`augmentedTheory`
path (confirmed: its only two callers, `dictionary.py:463` diagnostic prints and its own
`__main__`, never persist anything), and has three known correctness gaps documented in
the plan. This milestone turns it into the real thing: bug-fixed, fed by Phase G's actual
output, cost-aware, and persisted.

**Explicitly out of scope for this milestone** (left for a follow-up): rewriting
`dictionary.py`'s full word list with resolved strokes (replacing `theory.tsv`), the
two-stroke fallback, and restricting `satOptimizeDiscriminator` to the `*`/`#` track —
all bigger, separable efforts the plan already calls out on their own.

## Facts established during planning (don't re-derive)

- `dictionary.py`'s `__main__`: `theory`/`FirstTheory.pickle` built at `:416`;
  `augmentedTheory = buildDiscriminatorSelection(theory, discrimFeatureWords)` at `:463`
  (its only two callers repo-wide are this diagnostic print path and
  `ambiguitychecker.py:412`'s own `__main__`); `satOptimizeDiscriminator` called `:496`.
  **Nothing past `FeatureDiscrimator.pickle` is persisted** — everything from
  `augmentedTheory` onward is recomputed and only printed each run. New Phase P code
  should be wired in independently, right after `theory`/`FirstTheory.pickle` is
  available (~`:416`), NOT by extending `augmentedTheory`/`satOptimizeDiscriminator` —
  those two are the *old*, now-superseded same-lemma path Phase G/elicitation replaced,
  and per the plan should eventually be narrowed to the `*`/`#` track only (separate,
  deferred work).
- `buildDiscriminatorSelection` (`src/featureextractor.py:284-325`) returns
  `dict[tuple[WordFeature,...], list[tuple[Word,...]]]` — same-lemma-homophone
  discriminator selection via combinatorial `Word.getFeatures()` scanning. **Confirmed
  obsolete as Phase P's input** — Phase G/elicitation (`resolved_press_sets.json`,
  `phase_g_keypress_assignment.json`) already supersedes it as the source of truth for
  atomic-feature-to-keypress grouping.
- `getStrokeCost` (`src/keyboard.py:527-546`) DOES have real production callers (correct
  this if previously stated otherwise): `src/cpsatsolver.py:327` (per-part stroke-cost
  dict for the main phoneme-key optimizer) and `src/greedyoptimizer.py:171`
  (`_buildStrokePool`'s sort key for the 4 reserved-key stroke pool). The KeyError bug is
  real and live-reachable in principle, not just a Phase P concern, though the reserved-
  key pool likely avoids it in practice (its combos mostly span different fingers).
  `src/test/keyboard_test.py:331-353` already has some `getStrokeCost` coverage — extend
  it, don't create a parallel file.
- `_possibleKeypress` dicts (`Starboard`, `src/keyboard.py:308-348`) are the authoritative
  per-finger legality table — e.g. `rightPinky` only has `()`,`(22,)`,`(23,)`,`(24,)`,
  `(25,)`,`(22,23)`,`(24,25)`,`(22,24)`,`(23,25)`,`(22,23,24,25)`; `(22,25)`/`(23,24)` are
  absent and currently crash `getStrokeCost` with `KeyError`.
- `ATOMIC_FEATURE_CONFLICTS` (`src/word.py:273`, `{"p":"s","s":"p","m":"f","f":"m"}`) IS
  already used, in `src/greedyoptimizer.py:70` — correct a prior claim that it was
  unused. Still not used anywhere in `ambiguitychecker.py`; may be worth consulting for
  Phase P's own conflict logic but not required by this milestone.
- `Phoneme.consonantPhonemes` (`src/grammar.py:33`) = `"RtsplkmdvjnfbZwzSgNG"`, 20
  phonemes, shared by both onset and coda in `Phoneme.phonemesByPart` — confirmed the
  full consonant inventory, not narrowed.
- `Word` (`src/word.py:26-260`) hashes/equals on `(ortho, phonology, lemme, gramCat.name,
  gender, number)` (`:90`, `:150-157`), not object identity — relevant for building any
  new `Word`-keyed lookup from `resolved_press_sets.json` + `theory`.
- ROADMAP.md open question 4 (`:358-359`): should a new resolved-theory output replace
  `theory.tsv` or live alongside it? Left genuinely open by this milestone (only the
  smaller `phase_p_keypress_realization.json` artifact below is produced now); the
  full "theory 2" replacement is the deferred, larger wiring work.

## Changes

### 1. Fix `getStrokeCost` KeyError (`src/keyboard.py:527-546`)

Illegal per-finger key unions (e.g. coda `{22,25}` on `rightPinky`) currently raise
`KeyError`. Per-finger legality is authoritative in `_possibleKeypress`'s dicts — no
union without an entry is meaningful. Wrap the lookup; on a missing combo, the finger's
key-union is **infeasible**, so the whole stroke is infeasible. Return `None` (not
`math.inf`, so callers can't accidentally treat it as "just a big cost" and rank it
anyway) and update every existing caller:
- `src/cpsatsolver.py:327` — skip strokes where `getStrokeCost` returns `None` when
  building the `{stroke: cost}` dict (dropping them can only prune candidates that were
  never legitimately reachable).
- `src/greedyoptimizer.py:171` (`_buildStrokePool`'s sort key) — filter out `None`-cost
  strokes before sorting, defensively (the 4-reserved-key pool likely never hits this,
  but don't leave a latent crash).
- New Phase P code (below) must treat `None` as "this key-combo candidate is out."

### 2. Fix `checkComposedChords`'s half-combo bug (`src/ambiguitychecker.py:334-337`)

```python
chosenPhoneme = (
    feasibility.feasibleSingleKeyPhonemes[0] if feasibility.feasibleSingleKeyPhonemes
    else feasibility.feasibleComboPhonemes[0][0]   # BUG: drops the combo's 2nd phoneme
)
keys = keyboard.getStrokesOfPhoneme(chosenPhoneme, "coda")
```
When the chosen feasibility is a *combo* (`feasibleComboPhonemes: list[tuple[str,str]]`),
both phonemes' keys must union into `keypressKeys`, not just the first's. Fix: branch on
single-vs-combo explicitly, and for the combo case call `getStrokesOfPhoneme` for both
`p1` and `p2` and union their keys before adding to `keypressKeys`.

### 3. Real cross-cluster new-vs-new collision check

`_isFeasibleAddition` only checks a single word's new candidate stroke against the
**existing** `theory` — it misses two *different* newly-composed candidate strokes
colliding with each other (plan's example: `(12,16)+{18}` and `(12,18)+{16}` both land on
`(12,16,18)`). Add a new function, e.g.:

```python
def findCollidingNewAdditions(
    candidateWords: list[Word], additionKeys: tuple[int, ...],
    wordToStrokes: dict[Word, Strokes],
) -> list[tuple[Word, Word]]
```

that computes every candidate word's induced new stroke under a given `additionKeys` and
returns any pair that collides with each other (in addition to the existing check against
`theory`). Fold this into `findFeatureKeypresses`'s per-candidate feasibility test — a
candidate key-combo is feasible for a Phase G group only if (a) every affected word's new
stroke is absent from `theory`, AND (b) no two affected words' new strokes coincide with
each other. Reuse `_appendCodaAddition` for the induced-stroke computation (already
correct), just extend the acceptance criterion.

### 4. Rewire the input from `augmentedTheory` to Phase G's real output

Replace `buildAtomicFeatureToWords`'s consumption of `buildDiscriminatorSelection`'s
`augmentedTheory` with the actual adopted artifacts:
- `phase_g_keypress_assignment.json` — `markersByKeypress: dict[int, list[str]]`, the 6
  groups to physically realize.
- `resolved_press_sets.json` — per homophone group: `strokes` (the shared base `Strokes`
  for every spelling in the group), `pressSets: dict[ortho, list[marker]]` (which markers
  each spelling needs), `frequencies`.

New function, replacing `buildAtomicFeatureToWords`'s role:
```python
def buildKeypressGroupToWords(
    resolvedGroups: list[dict],  # parsed resolved_press_sets.json
    markersByKeypress: dict[int, frozenset[str]],  # parsed phase_g_keypress_assignment.json
    wordsByOrthoLemme: ...,  # map (ortho, lemmeGramCat) -> Word, to resolve real Word objects
) -> dict[int, list[Word]]
```
mapping each Phase G keypress group id → every `Word` whose press-set touches a marker in
that group (i.e. the real-word population `findFeatureKeypresses` needs to check
feasibility against, replacing the atomic-feature-string keys with Phase G's 6 integer
group ids). `atomicFeatures`/`_selectCanonicalIndex`/`FEATURE_PRIORITY` machinery is no
longer needed for this path (Phase G already decided the canonical/no-stroke member via
the elicitation data), so `buildAtomicFeatureToWords` and `_selectCanonicalIndex` can be
left in place (still used by the diagnostic `__main__`/legacy path) but are not called
from the new Phase P entry point.

Need to resolve `Word` objects: `resolved_press_sets.json` only has orthography + lemma
key + markers, not full `Word` objects. Build a lookup from the loaded `theory`
(`FirstTheory.pickle`) keyed by `(ortho, lemmeGramCat)` or similar — check
`Word.lemmeGramCat`'s exact shape (`src/word.py`) to match `resolved_press_sets.json`'s
`lemmeGramCat` string key exactly.

### 5. Cost-aware candidate ranking

`findFeatureKeypresses` (renamed/adapted for the new group-keyed input, e.g.
`findKeypressGroupRealizations`) currently takes the *first* feasible single-key phoneme
or combo, in whatever order `Phoneme.consonantPhonemes` iterates. Change to: collect
**all** feasible candidates (single-key first, combo only if none), score each with
`keyboard.getStrokeCost(keys, "coda")` (skip `None`-cost candidates per fix #1), and keep
the full ranked list (cheapest first) rather than just one, e.g.
`feasibleSingleKeyPhonemes: list[tuple[str, int]]` (phoneme, cost) sorted ascending. This
gives Phase P (and any future joint solver) a real preference order instead of an
arbitrary one, and directly answers the plan's "not cost-aware" gap.

### 6. Persist a real Phase P output artifact

Currently nothing downstream of `FeatureDiscrimator.pickle` is persisted — everything is
recomputed and printed each run (`dictionary.py`'s whole `__main__` tail). Add a new
canonical build script mirroring `util/build_phase_g_assignment.py`'s role:
`util/build_phase_p_realization.py` — loads `Dictionary.pickle`/`FirstTheory.pickle`,
`phase_g_keypress_assignment.json`, `resolved_press_sets.json`; runs the fixed
feasibility/cost search; writes `phase_p_keypress_realization.json`: per keypress group,
the chosen coda key-combo (or `null` if infeasible even at combo size 2), its cost,
alternate candidates considered, and any residual collisions found. This is milestone 1's
concrete deliverable — it does **not** yet rewrite `theory`/persist a final
stroke-per-word table (that's the deferred `theory.tsv`-replacement work).

### 7. Tests

- `src/test/keyboard_test.py`: add a case for `getStrokeCost`'s illegal-combo path
  returning `None` instead of raising (e.g. `(22, 25)` on `rightPinky`).
- `src/test/ambiguitychecker_test.py`:
  - fix-verification test for `checkComposedChords`'s combo-union bug (a word needing a
    2-phoneme combo keypress gets both phonemes' keys unioned, not just the first's).
  - new tests for `findCollidingNewAdditions` (two synthetic words' induced strokes
    colliding with each other, not with `theory`).
  - new tests for `buildKeypressGroupToWords` against a small literal
    `resolved_press_sets`-shaped fixture + `phase_g_keypress_assignment`-shaped fixture.
  - new tests for cost-aware ranking (candidates returned cheapest-first, `None`-cost
    ones excluded).

## Verification

- `pytest src/test/` — all existing + new tests green (490 existing must stay green).
- `python -m util.build_phase_p_realization` — run against the real, checked-in
  `phase_g_keypress_assignment.json`/`resolved_press_sets.json`/pickles; inspect the
  printed summary (feasible vs infeasible groups, chosen keys, costs) and confirm
  `phase_p_keypress_realization.json` is written.
- Manually sanity-check at least one group's chosen coda key against `starboard3h.json`
  (key really is in `[16..25]`, really unused by that group's affected words' existing
  strokes).

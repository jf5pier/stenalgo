# Plan: wire Part 2's atomic-feature keypress search into a real joint solver

Written 2026-09-18, following a design discussion about why the live same-lemma
discriminator mechanism (`satOptimizeDiscriminator`) can't produce a learnable, consistent
mapping no matter how it's tuned, and a code audit confirming `src/ambiguitychecker.py`'s
"Part 2" already prototypes the alternative but stops at a feasibility report. Written in
the style of `SHARED_DISCRIMINATOR_REWIRE_PLAN.md` (same convention: grounded in a code
audit, not aspiration; numbered proposed changes; open decisions recorded rather than
silently picked).

## Context

See `CLAUDE.md` for the overall pipeline; this plan concerns the same-lemma
("conjugation") half of homophone discrimination, not the lemma-homophone (`*`/`#`) half.

`ROADMAP.md`'s 2026-09-15 design decisions (§3 there) already settled the direction:
same-lemma homophones are a conjugation problem, solved with **meaningful phoneme-key
chords**, not the 4 reserved keys — those are reserved exclusively for lemma-homophones
(`*`/`#`, up to 4 lemmas per cluster). That decision was never implemented: the live
pipeline (`satOptimizeDiscriminator`, `src/satoptimizer.py`) still colors same-lemma
`WordFeature`s onto the reserved-key space today — **11** abstract special keypresses as
of the coverage-first switch (`PLAN_2026-09-18_low_value_discriminators.md`), the inverse
of the decision.

The design discussion that motivated this plan (same session, immediately prior) named
the concrete symptom: `_colorFeatures`'s graph coloring lets any two features share a key
whenever nothing flags them as opposed (`associationScore` returns `0.0` for any pair with
no shared `FEATURE_FAMILIES` entry — mode/tense atoms like `indicatif`/`conditionnel`
aren't in that table at all). A key's meaning is therefore whatever the solver found
cheapest that run, not a fixed, learnable slot — coloring-for-conflict-avoidance cannot
produce "strong polarity" by construction, no matter how the objective is tuned.

`src/ambiguitychecker.py`'s "Part 2" (`buildAtomicFeatureToWords`, `findFeatureKeypresses`,
`checkComposedChords`, added for `ROADMAP.md`'s open question 6) already prototypes the
fix: give each **atomic** grammatical feature — not each compound `WordFeature` — its own
dedicated coda-phoneme keypress, checked for collision-freedom against the whole `theory`.
A compound feature (`pers_3:nbr_p`) is then the **union** of its atoms' keypresses, pressed
as one chord. This is an assignment, not a coloring: once built, a key's meaning is fixed
forever, so "polarity" becomes a structural guarantee instead of a soft objective — the
`FEATURE_FAMILIES`/`associationScore`/`POLARITY_REWARD_SCALE` machinery in
`satoptimizer.py` becomes unnecessary for this track entirely.

Today Part 2 is diagnostic-only. Run via `python -m src.ambiguitychecker`, it prints a
feasibility report and writes `feature_keypress_feasibility.tsv`; nothing downstream reads
either. `dictionary.py`'s live theory build never calls it.

## What Part 2 does today, and its 3 gaps

- `buildAtomicFeatureToWords` (`src/ambiguitychecker.py:202-224`) walks the live
  discriminator selection (`buildDiscriminatorSelection`'s output), splits every
  non-canonical `(word, feature)` pair into atomic features via `atomicFeatures()`
  (`src/word.py:271-275`), and records which words carry each atom.
- `findFeatureKeypresses` (`:257-294`) scans candidate coda phonemes per atomic feature:
  single-key first, 2-key combos only if no single key works, feasible if appending the
  candidate key(s) to every carrying word's stroke never collides with an existing entry
  in `theory` (`_isFeasibleAddition`, `:235-243`).
- `checkComposedChords` (`:303-346`) handles words needing >1 atom at once: unions each
  atom's *first* candidate keypress and re-checks collision-freedom for the composed
  stroke.

Three gaps, found while grounding the design discussion in the actual code:

1. **Independent per-atom scan, not joint.** `findFeatureKeypresses` evaluates every
   atomic feature in isolation; nothing guarantees the choices made for *different* atoms
   stay jointly collision-free once composed. `checkComposedChords` only audits this after
   the fact, per word, with no repair — an infeasible composition is reported, not
   resolved by trying a different candidate for one of the atoms involved.
2. **`comboSize` hardcoded to 2** (`findFeatureKeypresses(..., comboSize: int = 2)`,
   `:261`), and `checkComposedChords` never escalates beyond whatever single phoneme each
   atom's feasibility check happened to pick. A real compound feature can need **up to 4**
   simultaneous atoms — confirmed live: `PLAN_2026-09-18_low_value_discriminators.md`
   documents `rudoie` resolved by `subjonctif:présent:pers_3:nbr_s`, a genuine 4-atom
   compound chosen by the real selection algorithm on the full lexicon, not a synthetic
   edge case.
3. **Not cost-aware.** `findFeatureKeypresses` iterates `Phoneme.consonantPhonemes`
   (`src/grammar.py:33`, fixed enumeration order `"RtsplkmdvjnfbZwzSgNG"`) and
   `checkComposedChords` always takes candidate `[0]` — first feasible, not cheapest.
   Neither consults `keyboard.getStrokeCost` (`src/keyboard.py:142`), the same
   biomechanical cost model `_buildStrokePool` (`src/greedyoptimizer.py:162-172`) and
   `_colorFeatures`'s warm start already use. A physically awkward combo can beat a cheap
   one purely by phoneme-alphabet-order luck.

## A prerequisite correctness bug: two incompatible "atomic feature" tokenizers

Found while checking gap 2 above. Two different functions both claim to split a compound
`WordFeature` into "atomic features," and they disagree:

- `src/word.py:271-275`'s `atomicFeatures()` — used by Part 2 — splits on **both** `_` and
  `:` (`re.split(r'[_:]', base)`). `"subjonctif:présent:pers_3:nbr_s"` becomes 6 fragments:
  `{"subjonctif", "présent", "pers", "3", "nbr", "s"}`.
- `src/satoptimizer.py:52-65`'s `_familyAtomicFeatures()` splits **only** on `:`, treating
  `pers_3`, `nbr_s`, `m_s`, etc. as single tokens — the linguistically correct grain, and
  the one `FEATURE_FAMILIES` (`:16-22`) is keyed by.

Building the joint solver on top of `atomicFeatures()` as-is would silently bind a
dedicated keypress to the bare string `"3"` (shared by every `pers_3`-bearing word, no
linguistic meaning on its own) and to `"pers"` (shared by `pers_1`/`pers_2`/`pers_3` at
once — three *mutually exclusive* values that should never end up needing the same key
pressed together). This is a correctness bug, not a style nit — it would quietly corrupt
whatever the joint solver assigns.

**Must fix before §3 below.** Two options, need to pick one:
- (a) Change `atomicFeatures()` itself to split only on `:`. Check other callers first —
  it's also used by `ATOMIC_FEATURE_CONFLICTS`-adjacent logic; confirm nothing depends on
  the finer split.
- (b) Give Part 2 its own correctly-scoped tokenizer, separate from `word.py`'s, and leave
  `atomicFeatures()` alone in case something else genuinely needs the finer grain.

Either way, add a regression test: `pers_3` must split to `{"pers_3"}`, not
`{"pers", "3"}`.

## Goal

Route same-lemma conjugation discrimination through a real joint solver over atomic
grammatical features and coda-phoneme keypresses, wired into `dictionary.py`'s live theory
output — fulfilling the 2026-09-15 decision that the reserved keys belong to
lemma-homophones only. `satOptimizeDiscriminator`/`_colorFeatures` demotes to a
feasibility monitor for the `*`/`#` track, matching `ROADMAP.md` Phase 2's own framing
("`_colorFeatures` demotes to a feasibility monitor rather than the driving mechanism").

## Call graph today (the gap)

```
dictionary.py (__main__)
│
├─ augmentedTheory = buildDiscriminatorSelection(theory, discrimFeatureWords)   :463
│
└─ satOptimizeDiscriminator(augmentedTheory, theory, numSpecialKeypresses=None) :497
     │
     └─ _colorFeatures(...) → keyAssignment: dict[WordFeature, int]
          -- colors ALL same-lemma WordFeatures onto the 4 reserved keys.
          -- feeds the printed "Special keypress mapping" table. Nothing persisted.

src.ambiguitychecker (__main__, run separately, never called from dictionary.py)
│
├─ augmentedTheory = buildDiscriminatorSelection(theory)                       :412
│
├─ atomicFeatureToWords = buildAtomicFeatureToWords(augmentedTheory)           :414
├─ featureKeypresses = findFeatureKeypresses(atomicFeatureToWords, ...)        :415
│    -- independent per-atom scan, comboSize capped at 2, not cost-aware
├─ composedReport = checkComposedChords(featureKeypresses, ...)                :416
│    -- audits composed chords after the fact, no repair
│
└─ prints a feasibility report + feature_keypress_feasibility.tsv
     -- DEAD END: nothing consumes this. dictionary.py never calls it.
```

## Proposed changes

### 0. Baseline commit

The working tree already carries several uncommitted, stacked threads (the
shared-discriminator rewire, lexicon data fixes, the special-keypress/set-cover
terminology rename). Get to a clean, committed baseline before starting this plan's
implementation, so its own diff is legible and revertable on its own — same reasoning as
`SHARED_DISCRIMINATOR_REWIRE_PLAN.md` §0.

### 1. Fix atomic-feature tokenization

Resolve the prerequisite bug above (pick option (a) or (b)), add the regression test, run
`pytest src/test/` to confirm nothing downstream of `atomicFeatures()` silently depended on
the over-split behavior.

### 2. Decide assignment granularity — open design decision, see below

Before building the solver: does every **distinct** atomic feature string get its own
permanently-dedicated keypress (what Part 2 does today — simple, but spends scarce coda-key
budget on values that are mutually exclusive and could share encoding room), or does each
**family** (person, number, gender, mode, tense — the groupings `FEATURE_FAMILIES` already
names) get a small internal code, since a word only ever carries one value per family at
once? This changes the shape of §3's model, so it needs deciding first — see "Open design
decisions" §A.

### 3. Build the joint feasibility + cost model

Replace `findFeatureKeypresses` + `checkComposedChords`'s two-pass independent-then-audit
approach with one CP-SAT model, shaped like `_colorFeatures`
(`src/satoptimizer.py:160-264`) but with a structurally different constraint:

- **Decision variables**: one boolean per (atomic feature or family-value, per §2's
  decision) × candidate key-set, `exactly-one` per atom.
- **Hard disjointness constraint** — the key structural difference from `_colorFeatures`:
  no two atoms' assigned key-sets may share a physical key, ever. (`_colorFeatures` allows
  sharing unless flagged, because reserved-key coloring is trying to *reuse* a scarce
  4-key space across non-conflicting features. Here, disjointness is what makes a
  composed chord decodable — press keys {16} and {17} together and the reader must be
  able to tell both atoms are "on," which only works if no other atom is *also* {16} or
  {17}.)
- **Per-word joint feasibility** — for every word needing an atom or a union of atoms,
  the composed addition to its stroke must not collide with any existing `theory` entry or
  same-cluster sibling. Precompute this as a lookup (same `_isFeasibleAddition` logic,
  `:235-243`) rather than trying to express "not a member of a large arbitrary forbidden
  set" as a linear constraint directly — feed it into the model as a per-atom-combination
  feasibility table the solver's candidate-set restriction respects, mirroring how
  `buildFeasibleDiscriminatorOptions` precomputes feasibility before
  `selectSharedDiscriminators` optimizes over it.
- **Objective**: minimize total frequency-weighted `keyboard.getStrokeCost`
  (`src/keyboard.py:142`) across all composed chords actually used — same `FREQUENCY_SCALE`
  pattern `satOptimizeDiscriminator` already uses (`src/satoptimizer.py:306,317-318`).
- **Candidate pool per atom**: single coda phonemes first, then N-way combos — see §4 for
  how large N needs to be.

### 4. Generalize N-way composition

Measure real demand before picking a cap: walk the live `buildDiscriminatorSelection`
output and count the max number of `:`-separated atoms (post-§1-fix) in any selected
compound feature across the full lexicon. Expect ≤4 (the `rudoie` precedent), confirm
rather than assume. `checkComposedChords`'s union logic (`:317-346`) is already
N-way-agnostic — it unions `wordAtoms` of any size — the actual gap is candidate
generation (§3's model needs combo candidates up to the measured N, not hardcoded at 2)
and joint search across atoms (§3 also fixes this).

### 5. Two-stroke fallback for infeasible or expensive compositions

Not everything will fit in one stroke's coda room. The coda role has exactly **10**
physical keys in the live layout (`starboard3h.json`: `keyIDinSyllabicPart.coda = [16..25]`),
already densely packed with real phonology — `findFeatureKeypresses`'s own
"INFEASIBLE even at combo size 2" output today is evidence this scarcity is real, not
hypothetical. When a word's needed atom-union has no single-stroke feasible solution (or
only a biomechanically severe one), fall back to a second stroke — same precedent
`ROADMAP.md` design decision #3 already names (English theories fuse common suffixes into
the final chord, e.g. `-S`/`-G`, but fall back to a separate stroke for rarer
modifications). Cutoff rule is an open decision — see "Open design decisions" §B.

### 6. Wire into `dictionary.py`'s live theory + persisted output

- Call the new solver from `dictionary.py`'s `__main__`, feeding it
  `buildDiscriminatorSelection`'s output (already computed once there, `:463`) the same
  way `satOptimizeDiscriminator` is fed today.
- Persist the result — today nothing captures a resolved same-lemma theory to a file
  (`ROADMAP.md` open question 4, re: `theory.tsv`'s fate); this plan's output (atomic
  feature → keys, composed per word) should be the thing that finally gets persisted,
  since it's the first mechanism actually meant to be the real, permanent theory rather
  than a diagnostic table.
- Decide `satOptimizeDiscriminator`'s remaining scope: restrict it to the `*`/`#`
  lemma-homophone track only (2 keys, 4 modifier values by frequency rank within a
  cluster — `ROADMAP.md` design decision #2). Note that track may not need CP-SAT coloring
  at all — it's a frequency-rank assignment within each cluster independently, not a
  shared-key graph-coloring problem across the whole lexicon. Flag as a possible
  follow-on simplification; out of scope for this plan to implement, just don't design
  §3's model in a way that blocks it later.

### 7. Consumers to update

- `src/ambiguitychecker.py` — Part 2 stops being diagnostic-only; its functions become (or
  are wrapped by) the real solver `dictionary.py` calls.
- `dictionary.py` `__main__` — new call + persisted output, per §6.
- Tests — a new `src/test/` module for the joint solver (mirror `satoptimizer_test.py`'s
  pattern: small synthetic cases for the CP-SAT model directly, plus a shape/contract test
  for the `dictionary.py` wiring). Existing `src/test/ambiguitychecker_test.py` coverage
  of Part 1 (classification) is untouched; Part 2's current tests, if any, need review
  once its functions' contracts change.

### 8. Re-run and compare

```bash
pytest src/test/
python dictionary.py
python -m src.ambiguitychecker
```
- Confirm the reserved-key special-keypress count drops to (at most) what the `*`/`#`
  track alone needs — should shrink dramatically from today's 11, since same-lemma
  features no longer compete for that space at all.
- Confirm every atomic feature's assigned keypress is unique and fixed across the whole
  printed/persisted output (the actual "polarity" property this plan exists to deliver) —
  spot-check a few families (person, number, gender) by hand.
- Confirm no regression in total unresolved-word count relative to today's
  `satOptimizeDiscriminator` path (some words may move from "resolved via reserved key" to
  "resolved via phoneme chord" or "resolved via two-stroke fallback," but none should
  become newly unresolved without an explicit decision to accept that, e.g. via the
  Category-C exception-list precedent from `PLAN_2026-09-18_low_value_discriminators.md`).

## Open design decisions

### A. Per-distinct-feature vs per-family-with-internal-code granularity (§2)

Part 2 today gives every distinct atomic feature string its own permanent keypress
(`pers_1`, `pers_2`, `pers_3` each get their own). Since a word only ever carries one
value per family, a family-level code (e.g. no stroke = the most common/unmarked value,
one dedicated key = a second value, a second key or that key's combo = a third) would
spend far less of the scarce 10-key coda budget — but changes what "one key = one fixed
meaning" means: a key's meaning becomes "this family's non-default value," not a single
global constant, and reintroduces a small amount of the "which meaning does this key have
right now" burden this whole plan exists to eliminate, unless the family boundary itself
is made obvious some other way (e.g. gramCat is usually unambiguous from the word's own
orthography, so the same physical key *could* safely mean "feminine" for an adjective and
"2nd person" for a verb — a word is never both). Recommend the family-with-code approach
for budget reasons, but this is a real mnemonic-clarity/resource-efficiency trade-off that
needs the user's steer, not a unilateral call — decide before §3 since it changes the
model's variable shape.

### B. Two-stroke fallback cutoff (§5)

Cost-based (a `getStrokeCost` threshold, mirroring how `_buildStrokePool` sorts by cost),
frequency-based (only fall back for low-frequency words, mirroring
`LOW_COUNT_THRESHOLD`/the Category-C exception-list convention), or a fixed rule (any
composition needing more than N atoms automatically two-strokes, independent of cost)?
Needs a decision before §5 is implementable, though §3's model can be built without
committing to this — the fallback is a post-solve decision about what to do with words the
model reports infeasible or expensive.

### C. Onset phonemes as candidates?

`findFeatureKeypresses`'s docstring says "candidate **right-hand coda** phonemes" — Part 2
only ever searched coda. Should onset (left-hand) phonemes also be eligible candidates for
some families, e.g. once coda room runs out for a given word? Or is onset reserved for the
word's own base phonology by convention, keeping grammatical marking conventionally
right-hand/coda-side (arguably more learnable on its own — mirrors English theories'
suffix-key convention)? Needs a decision; mechanically easy to add to §3's candidate pool
once decided.

### D. Fate of `assignDiscriminatorKeypresses`/`FEATURE_PRIORITY` (`src/greedyoptimizer.py`)

Currently orphaned (tested, not called from `dictionary.py`), operating on the
reserved-key space via graph-coloring + a hand-authored markedness table — the same genre
of mechanism `satOptimizeDiscriminator` implements more rigorously, not something this
plan's phoneme-keypress mechanism directly supersedes (different physical key space).
Likely candidate for retirement once §6 restricts `satOptimizeDiscriminator` to the
`*`/`#` track only (no more use case for "the greedy alternative to reserved-key
coloring"), but confirm rather than assume — flag for a follow-on cleanup, not in scope
here.

## Non-goals / out of scope

- No changes to the lemma-homophone (`*`/`#`) track's own logic, beyond confirming it
  keeps sole claim to the 4 reserved keys once §6 lands.
- No re-optimization of the phoneme→key layout itself (`starboard3h.json`,
  `cpsatsolver.py::optimizeKeyboard`, still commented out per `ROADMAP.md`) — this plan
  only adds a second consumer of the existing coda-key space, layered after the base
  phonology assignment it already encodes.
- No changes to `FEATURE_FAMILIES`/`associationScore`/polarity-coefficient machinery in
  `satoptimizer.py` for the same-lemma track — once every atom has a guaranteed-unique
  keypress, polarity is structural and that machinery has no remaining job for this track.
  Don't extend it with mode/tense entries; it becomes dead code for this purpose once §6
  lands (separate cleanup, not blocking this plan).
- No prefix-formation work (`ROADMAP.md` Phase 6) — same machinery family, explicitly
  out of scope here.

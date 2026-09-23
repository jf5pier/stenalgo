# Resume point — 2026-09-19, branch `phase-g-grouping` (CP-SAT exact optimization of Grouping Phase)

Written so a fresh (cleared-context) session can pick up without re-deriving context.
Read together with `ATOMIC_KEYPRESS_REWIRE_PLAN.md` (authoritative plan) and
`RESUME_2026-09-19-phaseG.md` (the earlier same-day session this one continues directly
from — E5/E6/Grouping Phase implementation, the two-elicitation-model comparison, and the
decision to adopt model 2). This file picks up exactly where that one's "Still open"
list left off.

## Where things stand, in one paragraph

Starting from `RESUME_2026-09-19-phaseG.md`'s open items, this session: (1) adopted
model 2 (pers_3 default) as the primary elicitation calibration, (2) implemented Phase
G's missing frequency-weighted chord-size reporting, (3) built an exact CP-SAT solver
(`src/featuregroupingsat.py`) that **proved Grouping Phase's greedy coloring was leaving a keypress on
the table** — greedy found K=6/7, CP-SAT proved K=5 achievable, later K=6 again after a
real data-correctness fix (see below) — and (4) spent most of the session iteratively
refining that CP-SAT solver's constraint vocabulary in direct response to a sequence of
user preferences about the keypress bundling, ending in a general-purpose hard/soft
constraint system (`mustShareKey`, `aloneKeys`, `mustDifferGroups`, `SameKeyPreference`,
`ExclusiveGroupPreference`, lexicographic multi-tier priority). Along the way, a real
elicitation-data bug was found and fixed: 7 of 26 `impératif`-marking answers had used
`pers_2` instead of `impératif` itself, which (once corrected) raised the true minimum K
from 5 to 6 — a genuine, now-understood tradeoff, not a regression. The final adopted
Grouping Phase output is persisted in `keypress_groups.json` and was **exhaustively
validated** (all 52,373 homophone groups, all 4,363 `impératif` readings, all 15,999
oppositions they participate in) to confirm every imperative reading is discriminable by
pressing its keypress alone, with 0 exceptions. Branch `phase-g-grouping` is pushed to
`origin` (not yet merged to `main`, no PR opened yet). All work is committed; nothing is
in progress or half-done.

## File inventory (everything needed to continue)

**Planning docs (read first, in this order):**
- `ATOMIC_KEYPRESS_REWIRE_PLAN.md` — the authoritative plan (Elicitation/Grouping/Realization Phases sections).
- `RESUME_2026-09-19-phaseG.md` — the immediately-preceding same-day session.
- `RESUME_2026-09-19-cpsat.md` — this file.
- `GLOSSARY.md` — vocabulary reference (Cluster, Reading, Signature/Press-set).

**Code (all committed on `phase-g-grouping`):**
- `src/elicitation.py` — unchanged in structure from the prior session, but:
  - `buildFrequencyByGroupOrtho()` (new): per-group, per-spelling corpus frequency
    (max over that spelling's Word rows), feeding Grouping Phase's frequency-weighted report.
  - `serializeResolvedPressSets()`: now takes an optional `frequencyByGroupOrtho` and
    writes a `"frequencies"` field into the persisted artifact.
- `src/featuregrouping.py` — Grouping Phase (greedy), extended this session:
  - `FrequencyByGroup` type alias, `loadGroupOrthoFrequencies()`,
    `frequencyWeightedChordSizes()` — per-keypress real-corpus usage weight, a Realization Phase
    input the plan calls for but that was never implemented until now. Threaded through
    `runFeatureGrouping`/`FeatureGroupingResult` and the `__main__` report.
  - Everything else (greedy coloring, verify-and-repair loop) is unchanged from the
    prior session — **still greedy, not proven-minimal**; superseded in practice by
    `featuregroupingsat.py` for the actual adopted result, but kept as the fast/cheap path.
- `src/featuregroupingsat.py` — **new module this session**, the CP-SAT exact solver. This is
  where almost all the session's design work landed. Key pieces, roughly in the order
  they were built (see the module's own docstrings for full detail on each):
  - `groupSignatures()` — dedups the 47,799 real homophone groups down to 218 distinct
    coloring problems (only the *set of distinct true press-sets* in a group matters,
    not orthography/stroke identity) — this is what makes exact CP-SAT tractable at all.
  - `_buildDistinctnessModel()` — the shared core: one keypress per marker, and within
    every signature, every pair of press-sets must induce a distinct touched-keypress
    set (the *exact* ground truth `featuregrouping.verifyKeypressAssignment` checks — not
    `featuregrouping.py`'s pairwise `coOccurrencePairs`/`wouldCollideIfMergedPairs`
    pre-checks, which are a greedy-only approximation).
  - `minKeypressesSat(pressSetsByGroup, mustShareKey=..., aloneKeys=..., mustDifferGroups=...)`
    — scans K=1,2,... and returns the first CP-SAT *proves* feasible (so a "no" at each
    step is a proof, not a guess). `mustShareKey` (pin a pair together),
    `aloneKeys` (a marker shares with nothing), `mustDifferGroups` (every pair within a
    group forced apart) are all **HARD** — they can inflate K or fail outright.
  - `minKeypressesSatPreferring(pressSetsByGroup, preferSameKey=..., aloneKeys=..., mustDifferGroups=...)`
    — finds the TRUE minimum K unconstrained by `preferSameKey` first, then re-solves
    AT that fixed K maximizing how many `preferSameKey` pairs share a keypress — a
    **SOFT** tiebreaker that can never inflate K, unlike passing the same pair to
    `mustShareKey`.
  - `SameKeyPreference` / `ExclusiveGroupPreference` (frozen dataclasses) +
    `minKeypressesSatWithPriorities(pressSetsByGroup, preferences: list[...], aloneKeys=..., mustDifferGroups=...)`
    — **lexicographic multi-tier** soft preferences: tier 0 optimized first and then
    LOCKED (via an equality constraint) before tier 1 is optimized only among colorings
    that still achieve tier 0's best, etc. This exists because a single combined
    objective (summing scores) would let a big win on a low-priority tier outweigh a
    small loss on a high-priority one — not what "lower priority" means. Built in
    direct response to the user's final request in this session (see "Key
    decisions" below).
  - `serializeAssignment()` / `groupSignatures()` / CLI (`python -m src.featuregroupingsat
    marker1:marker2` for hard, `marker1~marker2` for soft) — see the module for exact
    argument shapes; the CLI is exploratory, `util/build_keypress_groups.py` is the
    canonical persistence path.
- `util/build_keypress_groups.py` — **new this session**, the canonical build script
  (mirrors `util/build_pers3_default_answers.py`'s role for the elicitation side).
  Currently configured with the FULL adopted constraint set (see "Current adopted
  configuration" below); re-verifies 0 conflicts against the real lexicon before
  writing, refuses to persist otherwise. Run: `python -m util.build_keypress_groups`.
- Tests: `src/test/featuregroupingsat_test.py` (25 tests, all synthetic fixtures — fast, no
  pickle-loading needed), plus `src/test/elicitation_test.py`/`featuregrouping_test.py` extended
  with a handful of frequency-weighting tests. 489 tests total, all passing.

**Data files (git-tracked, real data not build artifacts):**
- `elicitation_answers.json` — **primary**, model 2 (pers_3 default). Also now has the
  `impératif`-marking fix applied (see "Key decisions" #4 below): all 26 `impératif`-side
  answers use `impératif` alone, none use `pers_2` as a substitute.
- `elicitation_answers_pers1default.json` — archived model 1, same `impératif` fix
  applied for consistency, but not otherwise used by the active pipeline.
- `keypress_groups.json` — **the canonical Grouping Phase output**, git-tracked
  (unlike `resolved_press_sets.json`, which is gitignored/regenerable — this one encodes
  real decisions, not a mechanical rebuild). Current content: K=6, 0 conflicts, full
  constraint provenance (`mustShareKey`, `aloneKeys`, `mustDifferGroups`,
  `preferenceTiers`+achieved scores), frequency-weighted chord sizes. See "Current
  adopted configuration" below for the actual keypress table.
- `pers_1PreferedOver_pers_3KeyAssignation` — unchanged from prior session, the
  model-1-vs-2 comparison finding.

**Generated/regenerable, gitignored (regenerate via the commands in "How to regenerate"):**
- `Dictionary.pickle`, `FirstTheory.pickle`, `FeatureDiscrimator.pickle`.
- `questionnaire.json`, `elicitation_questionnaire.html`,
  `elicitation_questionnaire_pers3default.html`.
- `resolved_press_sets.json`, `resolved_press_sets_pers3default.json` — the latter is
  now a stale leftover from the pre-adoption exploration (model 2 IS
  `elicitation_answers.json` now); harmless since gitignored, but not meaningful to
  regenerate anymore under that name.

**Published artifacts (external, load-bearing, unchanged this session):**
- Model 1: https://claude.ai/artifact/AbYKVAYSQ9petdsHAuKY2X
- Model 2: https://claude.ai/artifact/MRLF9MBbbQm5KjoXFYpKKG
- Neither artifact reflects the `impératif` answer fix (7 answers corrected locally in
  `elicitation_answers.json` this session, not pushed back to either published
  questionnaire page) — cosmetic only, since the local JSON is the source of truth for
  the pipeline, but worth knowing if the artifacts are ever reopened for further editing.

## Current adopted configuration (as persisted in `keypress_groups.json`)

**Hard constraints:**
- `f` shares its keypress with nothing else.
- `infinitif`, `pers_1`, `pers_2`, `pers_3` are pairwise forced onto different keypresses.

**Soft preferences, in descending priority (lexicographic — each locked in before the
next is optimized):**
1. `nbr_p` shares a keypress with `p`.
2. `future` shares a keypress with `passé`.
3. `nbr_p`/`p`'s keypress holds no other marker (stays exclusive to just the two of them).

**Result: K=6, 0 conflicts (verified against all 47,799 groups), all 3 soft tiers fully
achieved.** Keypress table (labels are arbitrary/solver-chosen — re-running
`build_keypress_groups` can permute which integer maps to which group, but the
*groupings* themselves are what's been decided):
- `{f}`
- `{impératif, pers_1}`
- `{imparfait, pers_2}`
- `{conditionnel, infinitif, subjonctif}`
- `{future, passé, pers_3}`
- `{nbr_p, p}`

Unpressable (never live) markers, unchanged from before: `VER`, `indicatif`, `m`,
`nbr_s`, `participe`, `présent`, `s`.

This is one of exactly **3 distinct solutions** at K=6 satisfying the two hard
constraints plus `nbr_p`+`p` together (enumerated exhaustively via CP-SAT with
symmetry-breaking) — the other two differ only in where `future` lands (with
`conditionnel`/`infinitif`/`subjonctif` instead of with `passé`/`pers_3`, or with
`nbr_p`/`p`). The user explicitly picked this one (called "solution 3" mid-session)
after the two additional soft preferences (`future`~`passé`, `nbr_p`/`p` exclusivity)
disambiguated it.

## Key decisions this session (why things are the way they are)

1. **Adopted model 2 (pers_3 default) as primary elicitation calibration** — beats model
   1 on K (was 7 vs 6 under greedy; the comparison predates this session's CP-SAT work).
   `elicitation_answers.json` now holds model 2; model 1 preserved as
   `elicitation_answers_pers1default.json`.
2. **CP-SAT beats greedy by a full keypress** — greedy's `coOccurrencePairs`/
   `wouldCollideIfMergedPairs` pre-checks are conservative approximations (used to make
   greedy coloring tractable), not the real constraint. The real constraint (every
   group's induced press-sets pairwise distinct) is directly encodable in CP-SAT and,
   with only 218 distinct signatures, tractable to solve exactly (~3s). First proof
   found K=5 (before the `impératif` fix below); this is the origin of `featuregroupingsat.py`.
3. **`nbr_p`/`p` colocation was investigated as hard-vs-soft** — the user asked "can
   this be favorized rather than forced"; led to building
   `minKeypressesSatPreferring` (find true min K unconstrained, then prefer as
   tiebreaker) as the more principled mechanism over `mustShareKey` (which can inflate
   K). Both happened to find K=5/6 for this specific pair, but the soft mechanism is
   the one to prefer in general since it can't accidentally cost a keypress.
4. **The `impératif`-auto-defining investigation found and fixed a real data bug.** The
   user wanted "no other keys needed to discriminate an impératif case." Checking
   `elicitation_answers.json` found 7 of 26 `impératif`-side answers had checked
   `pers_2` instead of `impératif` (worked because imperative is inherently 2nd-person,
   but was inconsistent — 19/26 used `impératif` properly). **User confirmed these were
   answering mistakes**; fixed in both `elicitation_answers.json` and the archived
   `elicitation_answers_pers1default.json`. Consequence, reproduced and understood: the
   true minimum K rose from 5 to 6, because `impératif` can no longer share a keypress
   with anything (with the fix, sharing would mean pressing it also silently asserts
   whatever it's bundled with — breaking auto-definition). This is a real, structural
   cost of the fix, not a bug in Grouping Phase. **Final exhaustive check** (see below)
   confirms the fixed property holds universally, not just for the 194 sampled
   oppositions.
5. **"Auto-defining" clarified as a Elicitation Phase (data) property, not a Grouping Phase (keypress
   assignment) property.** The user's later precision — "the key CAN be shared for
   other features, just not comboed with another key when discriminating impératif" —
   led to realizing `impératif` does NOT need to be isolated on its own keypress; it
   only needs its own TRUE press requirement to be the singleton `{impératif}`
   (already guaranteed by fix #4). Confirmed 4 markers (`conditionnel`, `nbr_p`,
   `pers_1`, `pers_3`) can safely share with `impératif` at K=6; 8 cannot (would need
   K≥7). The eventual adopted solution bundles `impératif` with `pers_1`.
6. **`aloneKeys`/`mustDifferGroups` added as new hard-constraint types** for the user's
   next two asks: "`f` alone" and "`infinitif`/`pers_1`/`pers_2`/`pers_3` pairwise
   distinct." Implemented generically (`_addMustDifferPairs`,
   `_aloneAndMustDifferPairs`) rather than as one-off code, since the shape (force a
   set of marker pairs apart) is reusable. Confirmed at K=6 unchanged (no extra cost).
7. **Lexicographic multi-tier preferences added for the final ask**: "`future`~`passé`
   share, lower priority than `nbr_p`~`p`" plus "`nbr_p`/`p` exclusive, lowest
   priority." A single summed objective would not respect strict priority ordering (a
   big win on tier 2 could outweigh a small loss on tier 1), so implemented real
   sequential lock-and-reoptimize (`minKeypressesSatWithPriorities`). This produced
   exactly the specific solution (out of 3 possible at K=6) the user asked for by name.
8. **Final validation: exhaustive, not sampled.** The user asked to validate that every
   impératif homophone is discriminable by its key alone. Rather than trust the 194
   sampled questionnaire answers, re-walked the FULL real lexicon (52,373 groups, 4,363
   distinct `impératif` readings, 15,999 pairwise oppositions) and confirmed 0
   violations — every single opposition an `impératif` reading is ever compared against
   requires pressing `impératif` alone. This is a real, complete proof over the actual
   data, not an inference from the sample.

## Addendum (2026-09-19, later same day): frequency-weighted chord report — top-200-word exclusion

Reviewing `frequencyWeightedChordSizes` (see "Still open" #6 below) surfaced two data
issues, one real fix applied, one investigated and found to be a non-issue:

- **Investigated and NOT a bug**: whether same-lemme forms share one frequency in
  `LexiqueMixte`. They mostly don't — Lexique383's *attested* per-form rows (`ai`, `va`,
  `mangea`, `mangerai`, ...) each carry their own real, independently-varying
  `freqlivres`; only the ~52k/58k `LexiqueSynthetic` paradigm-gap-filler rows (mostly
  verb forms with a true corpus count of zero, e.g. `nous mangeassions`) are flat `0.0`.
  Checked whether `freqlemlivres` (the lemma-total column) holds hidden mass to
  redistribute onto those zero rows: it doesn't — summed across all 6,391 verb lemmas,
  `sum(freqlivres over attested forms) - freqlemlivres` nets to -69.29 out of 150,281
  total (rounding noise), so `freqlemlivres` is already just the sum of what Lexique383
  observed. There's no recoverable frequency budget; the missing forms are genuinely
  below the books-corpus's detection floor (a real Good-Turing/zero-frequency problem,
  not a merge bug) — no French-specific quantitative paradigm-cell-frequency table
  exists in the literature to fill it precisely, and the report doesn't need one (see
  next point, which dominates far more than this ever would).
- **Real fix applied**: `frequencyWeightedChordSizes` was letting a handful of
  extremely-high-frequency *irregular* verb forms (`ai`, `va`, `sais`, `veux`, `suis`,
  `peux`, `allez`, `fais`, `dis` — all inside `top500_film.txt`'s first 200 lines)
  dominate keypress usage share (keypress `{impératif, pers_1}` read 31.3% vs. `{f}`'s
  3.9%, almost entirely from these ~10 words). **This is exactly the same top-200
  "brief candidate" population `dictionary.py:166`'s `analyseSyllabification` already
  excludes from syllable-frequency stats** ("Remove the frequent words from syllable
  frequency statistics" — a top-200 word gets a whole-word brief stroke, bypassing
  normal phonemic keypresses entirely, so it must not inflate a keypress's apparent
  real-writing load either). Applied the identical exclusion to
  `buildFrequencyByGroupOrtho` (`src/elicitation.py`): now takes an optional
  `frequentWords: frozenset[str]` (pass `Dictionary.frequentWords`) and zeroes any
  matching ortho's frequency. Wired into `elicitation.py`'s `__main__` via
  `_dictionary.frequentWords`. One test added
  (`test_buildFrequencyByGroupOrtho_zeroes_out_frequent_words`), 21/21
  `elicitation_test.py` passing. **Not yet regenerated**: `resolved_press_sets.json` and
  `keypress_groups.json` still hold the old (pre-exclusion) frequency
  numbers — rerun `python -m src.elicitation` then `python -m util.build_keypress_groups`
  to refresh them before trusting the report for Realization Phase.

## Still open / not yet done

1. **PR not opened.** Branch `phase-g-grouping` is pushed to `origin` (this session) but
   not merged to `main`, and no PR has been created — GitHub offered
   `https://github.com/jf5pier/stenalgo/pull/new/phase-g-grouping`. User has not yet
   said whether/when to open it.
2. **Realization Phase (physical realization) — still not started.** This is now the natural next
   phase per the plan, with the abstract Grouping Phase output finally settled. The plan
   already documents known real bugs waiting there (not yet investigated this session):
   - `_isFeasibleAddition` (`src/ambiguitychecker.py:243`) misses cross-cluster
     new-vs-new collisions between two newly composed chords.
   - `getStrokeCost` (`src/keyboard.py:529-546`) KeyErrors on illegal per-finger unions
     (e.g. coda m+n → right pinky {22,25}, not a valid keypress); the stale
     `anchor_feasibility.tsv` incorrectly listed this as feasible.
   - `checkComposedChords:336` takes only half a 2-phoneme combo
     (`feasibleComboPhonemes[0][0]`).
   - Wiring/persistence: call from `dictionary.py`'s `__main__`, fed by the E6 artifact;
     persist stroke→word output.
3. **`greedyColorMarkers`/`runFeatureGrouping` in `featuregrouping.py` is now superseded in practice** by
   `featuregroupingsat.py` for the actual adopted result, but was NOT removed or deprecated —
   still useful as a fast/cheap sanity check or fallback. No decision made about
   whether to keep both long-term or fold the CP-SAT path into `featuregrouping.py` itself.
4. **`resolved_press_sets_pers3default.json` is now a stale, meaningless filename**
   (harmless since gitignored) — could be cleaned up but wasn't.
5. Two harmless untracked files, unchanged from the prior session, still unaddressed:
   `scratch/callgraph` (old pasted transcript) and `sameLemmeHomophoneResolution.txt`
   (a one-line stray note, never explained).
6. **CORRECTION (later same addendum): the stroke-pairing analysis below is invalid as
   written — built on the wrong physical keys.** It paired Grouping Phase's keypress groups
   against the 4 *reserved* keys `[0,1,10,15]`. Per `RESUME_2026-09-18.md`'s authoritative
   design decision #1 (ROADMAP 2026-09-15, unchanged since): those 4 reserved keys are
   exclusive to the lemma-homophone (`*`/`#`) track — a *different* disambiguation track
   (different lemmas, same sound) from Grouping Phase's same-lemma conjugation markers
   (`impératif`, `pers_1`, `f`, `nbr_p`, ...). Grouping Phase's markers are meant to be realized
   from the **coda bank** instead (`starboard3h.json`'s `coda: [16..25]`, all 10 keys on
   the right hand: right index minus reserved 15, right middle, right ring, right
   pinky) — never the reserved keys. That same 2026-09-18 session also explicitly
   scoped this physical assignment **out for now**, because unlike the (always-idle)
   reserved keys, coda keys already carry real consonant-phoneme chords: a marker
   keypress realized there needs a finger/key-combo that's collision-free against every
   coda-phoneme chord actually used by words needing that marker — a real
   collision-feasibility problem against the live theory, not a plain cost-sort. The
   frequency-weighted usage numbers below (post top-200-word-fix) are still valid and
   useful as Realization Phase input; the reserved-key stroke table paired against them is not and
   should not be used. Left in place below for the record, marked invalid.
7. **[INVALID, see item 6 above — used the wrong physical keys, kept for the record only]**
   Frequency-weighted chord-size analysis on the FINAL adopted K=6 assignment was
   reviewed this addendum session** and cross-referenced against `Starboard`'s reserved-
   key stroke costs (cheapest strokes: `(10,)`/`(15,)` single index keys at 106, then
   `(0,)`/`(1,)` single pinky keys at 127, then `(0,1)` pinky pair at 170, then
   `(10,15)` cross-hand index pair at 252 — exactly 6 strokes cheap enough to precede
   any cross-hand pinky+index combo, matching K=6). Proposed pairing (busiest group →
   cheapest stroke) using the **pre-fix** numbers gave `{impératif, pers_1}` the top
   spot (31.3%, almost entirely from ~9 top-200 words like `ai`/`va`/`sais`). **Recomputed
   after regenerating `resolved_press_sets.json` and `keypress_groups.json`
   with the top-200-word exclusion applied** (`python -m src.elicitation && python -m
   util.build_keypress_groups`, both rerun this addendum session) — the ranking
   changed materially, confirming the exclusion was not cosmetic:

   | rank | group | share (post-fix) | share (pre-fix) |
   |---|---|---|---|
   | 1 | `{conditionnel, infinitif, subjonctif}` | 26.8% | 20.8% |
   | 2 | `{impératif, pers_1}` | 24.4% | 31.3% (was #1) |
   | 3 | `{nbr_p, p}` | 24.2% | 19.3% |
   | 4 | `{imparfait, pers_2}` | 14.7% | 19.9% |
   | 5 | `{f}` | 5.4% | 3.9% |
   | 6 | `{future, passé, pers_3}` | 4.6% | 4.9% |

   Total weight dropped 208,591 → 150,866 (the removed ~58k ≈ the top-200 words'
   contribution). Updated stroke pairing (busiest → cheapest, unchanged cost table:
   `(10,)`/`(15,)`=106, `(0,)`/`(1,)`=127, `(0,1)`=170, `(10,15)`=252):
   `{conditionnel, infinitif, subjonctif}`→`(10,)`, `{impératif, pers_1}`→`(15,)`,
   `{nbr_p, p}`→`(0,)`, `{imparfait, pers_2}`→`(1,)`, `{f}`→`(0,1)`,
   `{future, passé, pers_3}`→`(10,15)`. Top 3 groups are now close (24–27%) rather than
   one dominating — the two cheapest single-key strokes and the two pinky-single strokes
   all go to genuinely comparable-load groups; only the bottom two (`{f}`,
   `{future, passé, pers_3}`) are clearly lighter. This pairing has NOT been discussed
   with or confirmed by the user yet — it's a mechanical re-derivation, not an adopted
   decision.

## How to regenerate everything from scratch

```bash
python -m src.elicitation                    # resolved_press_sets.json, questionnaire.json
python -m src.featuregrouping                          # greedy baseline (K=6, NOT proven-minimal)
python -m src.featuregroupingsat                       # CP-SAT proof of true minimum (no preferences)
python -m util.build_keypress_groups       # THE canonical adopted assignment (all constraints)
pytest src/test/                              # 489 tests, all synthetic fixtures except
                                               # elicitation_test.py/featuregrouping_test.py's real-data
                                               # __main__ paths (not exercised by pytest)
```

To explore a different bundling decision without committing to it, use `featuregroupingsat.py`'s
functions directly (see module docstrings) or the CLI:
```bash
python -m src.featuregroupingsat marker1:marker2      # HARD: force together (can fail/inflate K)
python -m src.featuregroupingsat marker1~marker2      # SOFT: prefer together (never inflates K)
```
For hard `aloneKeys`/`mustDifferGroups` or the multi-tier priority system, there's no
CLI surface yet — call `minKeypressesSat`/`minKeypressesSatWithPriorities` directly (see
`util/build_keypress_groups.py` for a worked example).

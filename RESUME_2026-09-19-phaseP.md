# Phase P (physical realization) — Milestone 1, DONE

Written so a fresh (cleared-context) session can pick up without re-deriving context.
Read together with `RESUME_2026-09-19-phaseP-plan.md` (the original plan this session
started from -- superseded in two load-bearing ways described below, kept only for
historical context), `ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s "Phase P" section, and
`RESUME_2026-09-19-cpsat.md`/`RESUME_2026-09-19-phaseG.md` (Phase G's adopted output
this milestone consumes: `phase_g_keypress_assignment.json`).

## Bottom line

Phase P milestone 1 is complete and verified against the real 47,799-group,
~136k-word lexicon: **all 6 of Phase G's abstract keypress groups now have a real
physical coda key assignment, with zero collisions left in Phase P's own
jurisdiction.** Output artifact: `phase_p_keypress_realization.json`, built by
`python -m util.build_phase_p_realization`.

Final verified result:

| Group | Markers | Physical key(s) | Cost |
|---|---|---|---|
| 0 | `nbr_p`, `p` | `[17]` | 85 |
| 1 | `imparfait`, `pers_2` | `[20]` | 117 |
| 2 | `conditionnel`, `infinitif`, `subjonctif` | `[21]` | 109 |
| 3 | `future`, `passé`, `pers_3` | `[19]` | 131 |
| 4 | `impératif`, `pers_1` | `[18]` | 190 |
| 5 | `f` | `[16]` | 94 |

Residual collisions, split by whose problem each is (see "Three collision buckets"
below): **0 theory collisions, 0 same-lemmeGramCat collisions** (Phase P's own job --
fully resolved), **29 cross-category clashes** (a separate, already-documented bug
class, not Phase P's), **1,252 cross-lemma collisions** (the `*`/`#` reserved-key
track's job, not yet implemented). These numbers can drift slightly between runs of
`util/build_phase_p_realization.py` if the underlying lexicon/pickles change, but the
same-lemmeGramCat count staying at exactly 0 is the thing to re-verify after any
future change to this code -- see "The regression to watch for" below.

## Two ways the executed design diverged from the original plan

Both changes came from the user reviewing example collisions mid-session, not from
anything pre-planned -- a fresh session extending this work should treat these as the
actual design, not the plan file's sketch:

1. **The discriminator is a brand-new trailing stroke, not merged into the last
   existing stroke.** The plan's `_appendCodaAddition` (still used, unmodified, by the
   OLDER atomic-feature diagnostic path in this same file) unions the addition into
   the word's LAST existing stroke's chord. The real Phase P code
   (`_appendCodaExtraStroke`) instead appends an entirely separate trailing stroke --
   an extra "syllable" pressed after the word, not chorded together with its last
   syllable's own keys.
2. **A word needing several Phase G groups at once gets ONE shared extra stroke,
   composed jointly** -- not each group's key added independently to a per-group
   candidate search. This mattered a lot: the very first (naive) implementation
   found the search 0/6 infeasible, entirely because it checked each of the 6 groups'
   candidates against the ENTIRE population needing that marker, ignoring that many
   of those words also needed OTHER groups' markers, whose contribution should be
   composed together into one physical chord.

## Three collision buckets, and why only one blocks a candidate (`_isInScopeCollision`)

Two Word objects landing on the same final stroke isn't always the same kind of
problem. `_isInScopeCollision(word1, word2)` (`src/ambiguitychecker.py`) splits it
into three buckets by comparing `word.ortho`, `word.lemme`, `word.gramCat`,
`word.lemmeGramCat` (`f"{lemme}_{gramCat.name}"`, `src/word.py:96`):

1. **Same `lemmeGramCat`, different `ortho`** -- two inflected forms of the exact same
   lemma+gramCat paradigm (e.g. `dors`/`dort`). This is the ONE thing Phase G/P's
   coda-bank groups exist to prevent. `_isInScopeCollision` returns True only for
   this case; it's the only bucket that blocks a candidate key during the search.
2. **Same bare `lemme`, different `gramCat`** (e.g. `dîner` the NOM vs `dîner` the
   VER -- `dîners`/`dînés`) -- the already-documented "aller"-style cross-category
   clash (`detectCrossCategoryClash`, same file, much earlier in the pipeline). A
   separate, pre-existing issue class. NOT Phase P's job; reported via
   `KeypressGroupPhysicalAssignment.crossCategoryClashCollisions` for visibility only.
3. **Different `lemme` entirely** (true different-word homophones, e.g.
   `abymes`/`abîmes`) -- cross-lemma homophone disambiguation, the reserved `*`/`#`
   keys' job per `RESUME_2026-09-18`'s design decision #1, not yet implemented on this
   `theory`. NOT Phase P's job; reported via `crossLemmaCollisions`.

Identical `ortho` (regardless of lemma/gramCat) is EXCLUDED from all three buckets
everywhere -- two Word objects spelled the same produce identical typed output
regardless of which grammatical reading was meant, so they were never a real
ambiguity needing a distinguishing stroke.

**Do not conflate buckets 2 and 3 with bucket 1.** An earlier iteration this session
used bare `lemme` equality (not `lemmeGramCat`) for "in scope," which wrongly treated
bucket-2 pairs as if they were Phase P's problem and inflated the apparent failure
rate from 0 real collisions to 1,213 -- almost the entire visible "failure" was
measurement error, not a real search limitation. Tightening to `lemmeGramCat`
equality is what got the true same-lemma count down to (eventually) 0.

## The regression to watch for -- don't re-simplify the finalized-word-pool check

Mid-session, in response to a totally reasonable-sounding argument ("Phase G already
proved the 6 groups can't share a keypress, so hardcode that two groups can never get
the same physical key"), I replaced the finalized-word-pool cross-check with a simple
"reject a candidate key-set that any other already-decided group already has." **This
reintroduced the bug and silently regressed the same-lemmeGramCat count from 0 back
to 1,213** -- caught only because the real-lexicon verification run was re-run
immediately after and the number visibly changed back.

Why the simple version is insufficient: Phase G's own `verifyKeypressAssignment`
(`src/phaseg.py:142`) only proves the 6 groups are pairwise distinguishable in the
ABSTRACT (no two spellings within one homophone entry induce the same SET of
abstract keypress ids). It says nothing about the physical result once real keys are
assigned. Requiring every PAIR of groups to get a distinct key-SET is necessary but
NOT sufficient: a word needing groups A and B at once gets their UNION as its one
physical chord, and that union can coincidentally equal some THIRD group C's own
key-set even though A, B, and C are all pairwise distinct from each other. Concrete
real-lexicon example hit during this session: groups 0 and 5 got key-sets `(17,)` and
`(16,)` -- pairwise distinct -- but a word needing BOTH (`équipées`) got their union
`(16,17)`, which happened to equal group 3's own key-set exactly, silently reuniting
`équipées` with a same-`lemmeGramCat` sibling (`équipai`) that only needed group 3.

The correct, current fix (`realizeKeypressGroupsAsExtraStroke`, in
`src/ambiguitychecker.py`) is a "finalized word pool": a word becomes "finalized" the
moment every Phase G group it needs has been processed (assigned a key, or given up
on) -- its own composed stroke can never change again after that. Every new candidate
being considered for the group currently being decided is checked against the REAL
composed stroke of every already-finalized word, not just against a pairwise
group-key-set-distinctness rule. `src/test/ambiguitychecker_test.py`'s
`TestRealizeKeypressGroupsAsExtraStroke::test_multi_group_composition_does_not_coincide_with_another_group`
is a regression test for exactly this failure mode (a synthetic version of the
`équipées`/`équipai` pattern) -- if a future change makes that test fail, the
finalized-pool check has been broken again the same way.

## Code inventory (all in `src/ambiguitychecker.py` unless noted)

New/changed for this milestone (the OLDER atomic-feature diagnostic functions --
`buildAtomicFeatureToWords`, `findFeatureKeypresses`, `checkComposedChords`,
`_appendCodaAddition`, `_isFeasibleAddition` -- are unchanged, still fed by the
now-superseded `buildDiscriminatorSelection` path, and NOT used by any of this):

- `Keyboard.getStrokeCost`/`Starboard.getStrokeCost` (`src/keyboard.py`) now returns
  `int | None` -- `None` means the key combo is illegal (no finger can press it),
  instead of raising `KeyError`. Both real callers (`src/cpsatsolver.py:326-328`,
  `src/greedyoptimizer.py:_buildStrokePool`) updated to drop `None`-cost strokes.
- `buildWordsByOrthoLemme(theory)` -- index every Word by `(ortho, lemmeGramCat)`.
- `buildKeypressGroupToWords(resolvedGroups, markersByKeypress, wordToStrokes,
  wordsByOrthoLemme)` -- maps each Phase G group id to every real `Word` whose
  elicited press-set touches a marker in that group; disambiguates same-(ortho,
  lemmeGramCat) Word collisions via the entry's own `strokes` field.
- `buildWordToGroups(groupToWords)` -- inverted index, Word -> frozenset of group ids
  it needs.
- `_appendCodaExtraStroke(strokes, additionKeys)` -- the new-stroke-append mechanism
  (see "diverged from the plan" #1 above).
- `_isInScopeCollision(word1, word2)` -- the three-bucket classifier (see above).
- `findCollidingInducedStrokes(inducedStrokeOf)` -- generic "any two words share a
  final stroke" check over an arbitrary `dict[Word, Strokes]` (not tied to one shared
  `additionKeys` the way the older `findCollidingNewAdditions` is -- the latter now
  just delegates to this).
- `KeypressGroupPhysicalAssignment` (dataclass) -- the milestone's result type:
  `chosenKeysByGroup`, `costByGroup`, `alternatesByGroup`, `unassignedGroups`,
  `residualCollisions` (bucket 1), `crossCategoryClashCollisions` (bucket 2),
  `crossLemmaCollisions` (bucket 3), `residualTheoryCollisions`.
- `realizeKeypressGroupsAsExtraStroke(groupToWords, theory, keyboard, comboSize=2)` --
  the milestone's main entry point. Greedily processes groups largest-population-first
  (single coda key, then 2-key combo fallback), ranking candidates by
  `_candidateCost`'s frequency-weighted REAL composed-chord cost (see "same-column
  bonus" below), guarded by: `_isRedundantForAnyWord` (a candidate that's a no-op once
  unioned with a word's other already-decided groups), a physically-illegal-chord
  check (`getStrokeCost(...) is None`), a theory-collision check, an in-scope
  same-signature collision check, and the finalized-word-pool check described above.
  Ends with one full-assignment verification pass across every affected word, split
  into the three buckets.
- `_candidateCost` -- prices a candidate by the REAL composed extra-stroke cost across
  its affected words (frequency-weighted average), not the candidate's own isolated
  cost. This is what implements the "same-column bonus" the user asked for: Starboard
  already prices a same-column 2-key combo (e.g. coda `(22,23)`) below a cross-column
  combo of the same two keys (e.g. `(22,24)`) -- pricing the real per-word composition
  (rather than the bare candidate key-set) is what lets a candidate that happens to
  land in the same physical column as a frequently co-occurring group's key actually
  earn that discount in the ranking.

`util/build_phase_p_realization.py` -- the canonical build script (mirrors
`util/build_phase_g_assignment.py`'s role). Loads `Dictionary.pickle`/
`FirstTheory.pickle`, `phase_g_keypress_assignment.json`, `resolved_press_sets.json`;
runs `realizeKeypressGroupsAsExtraStroke`; writes `phase_p_keypress_realization.json`
(per group: markers, affected word count, chosen keys, cost, alternates; plus the
three residual-collision buckets as ortho pairs/lists). Note: `Dictionary.pickle` was
written while `dictionary.py` ran as `__main__`, so this script has to alias
`sys.modules["__main__"].Dictionary` before unpickling (see the script's own
`_loadTheory`) -- a plain `python -m util.foo` script doesn't get that for free the
way running `src/ambiguitychecker.py` directly as `__main__` does.

Tests: `src/test/keyboard_test.py` (illegal-combo-returns-None coverage),
`src/test/ambiguitychecker_test.py` (all Phase P functions above, including the two
regression tests named in this file). 515 tests total, all green. `mypy src/` is clean
on every file this milestone touched (pre-existing unrelated errors remain in
`cpsatsolver.py`/`satoptimizer.py`/`dictionary.py`/`featureextractor.py`/`keyboard.py`
-- OR-Tools stub mismatches and a few unrelated type issues, none introduced here).

## Explicitly still out of scope / deferred (unchanged from the original plan)

- Rewriting `dictionary.py`'s full word list with resolved strokes (replacing
  `theory.tsv`) -- this milestone only produces the smaller
  `phase_p_keypress_realization.json` artifact, per ROADMAP.md open question 4.
- The `*`/`#` reserved-key lemma-homophone track itself is still unimplemented; the
  1,252 cross-lemma collisions this run found are exactly the population that track
  would need to resolve.
- The cross-category clash fix (29 pairs) -- whatever mechanism eventually handles
  `detectCrossCategoryClash`'s findings generally (ignore-list style, or something
  else) should also cover these 29.
- Restricting `satOptimizeDiscriminator`/`buildDiscriminatorSelection` to the `*`/`#`
  track only -- still the old, superseded same-lemma path, untouched.
- The "two-stroke fallback" is NOT needed for this milestone's own scope after all --
  every genuine same-lemmeGramCat case got resolved with a single shared extra stroke.
  It may still matter for the `*`/`#` track's own eventual cross-lemma work, which
  this milestone deliberately didn't touch.

## Verification commands for a fresh session

```
pytest src/test/ambiguitychecker_test.py src/test/keyboard_test.py -q   # or pytest src/test/ -q for all 515
mypy src/ambiguitychecker.py src/keyboard.py src/cpsatsolver.py src/greedyoptimizer.py util/build_phase_p_realization.py
python -m util.build_phase_p_realization
```
The last command should print `6/6 keypress groups realized (0 residual theory
collisions, 0 residual same-lemmeGramCat collisions [Phase P's own job], ...)`. If the
same-lemmeGramCat count is not 0, something regressed -- see "The regression to watch
for" above before assuming it's a new, different problem.
